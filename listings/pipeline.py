"""
Automated Data Cleaning, Normalization, and Snapshot Ingestion Pipeline.
Handles Persian/Arabic digit conversion, price normalization, invalid data detection,
and historical snapshot change tracking.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from django.utils import timezone as django_tz
from core.constants import (
    EVENT_AREA_CHANGE,
    EVENT_INITIAL,
    EVENT_PRICE_DECREASE,
    EVENT_PRICE_INCREASE,
    EVENT_REAPPEARED,
    EVENT_TITLE_MODIFICATION,
    EVENT_UNCHANGED,
    SALE_CATEGORIES,
    RENT_CATEGORIES,
)
from core.normalizers import (
    clean_persian_text,
    parse_iranian_price,
    to_english_digits,
)
from core.tehran_data import suggest_district_for_neighborhood
from ingestion.models import SearchPartition
from listings.models import DivarListing, ListingSnapshot, SearchPartitionExecution

logger = logging.getLogger(__name__)


class ListingDataCleaner:
    """
    Validates and cleans raw listing dictionaries from the Divar API.
    """

    @classmethod
    def clean_and_normalize(cls, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Takes raw dictionary from Divar API response and returns normalized dictionary.
        Returns None if listing violates basic validity (missing token, zero/invalid price, impossible area).
        """
        token = raw.get("token") or raw.get("divar_token")
        if not token:
            logger.warning("Dropped listing with missing token")
            return None

        title = clean_persian_text(raw.get("title", ""))
        desc = clean_persian_text(raw.get("description", ""))
        category = raw.get("category", "apartment-sale")
        city = (raw.get("city") or "tehran").lower()

        # Parse & normalize area
        raw_area = raw.get("area_m2") or raw.get("size") or raw.get("area")
        area_m2 = None
        if raw_area is not None:
            try:
                area_str = to_english_digits(str(raw_area)).replace(",", "").strip()
                area_m2 = float(area_str)
            except (ValueError, TypeError):
                area_m2 = None

        # Impossible area filter: residential under 15m² or over 5,000m²
        if area_m2 is not None and (area_m2 < 12 or area_m2 > 5000):
            logger.warning(f"Listing {token} has suspicious area {area_m2}m²; discarding invalid area")
            area_m2 = None

        # Parse price fields
        raw_price = raw.get("price")
        raw_rent = raw.get("rent")
        raw_deposit = raw.get("deposit") or raw.get("credit")

        price = parse_iranian_price(raw_price)
        rent = parse_iranian_price(raw_rent)
        deposit = parse_iranian_price(raw_deposit)

        # Basic validity filter for sale listings:
        # In Tehran, an entire property for sale under 50 Million Tomans is a dummy/deposit placeholder
        if category in SALE_CATEGORIES and price is not None and price < 50_000_000:
            price = None

        # Calculate price per meter
        price_per_m2 = None
        rent_per_m2 = None
        deposit_per_m2 = None

        if area_m2 and area_m2 > 0:
            if price and price > 0:
                price_per_m2 = int(round(price / area_m2))
            if rent and rent > 0:
                rent_per_m2 = int(round(rent / area_m2))
            if deposit and deposit > 0:
                deposit_per_m2 = int(round(deposit / area_m2))

        # Location normalization
        neighborhood = clean_persian_text(raw.get("neighborhood", ""))
        district = raw.get("district")
        if district is not None:
            try:
                district = int(to_english_digits(district))
                if district < 1 or district > 22:
                    district = None
            except (ValueError, TypeError):
                district = None

        if district is None and neighborhood:
            district = suggest_district_for_neighborhood(neighborhood)

        # Coordinate normalization
        lat = raw.get("latitude") or raw.get("lat")
        lon = raw.get("longitude") or raw.get("long") or raw.get("lon")
        try:
            lat = float(lat) if lat is not None else None
            lon = float(lon) if lon is not None else None
            # Validate Tehran coordinate bounds (~35.5 - 35.9 lat, ~51.1 - 51.6 lon)
            if lat and lon:
                if not (35.4 <= lat <= 36.0 and 51.0 <= lon <= 51.8):
                    lat, lon = None, None
        except (ValueError, TypeError):
            lat, lon = None, None

        # Property attributes
        def safe_int(val):
            if val is None:
                return None
            try:
                v = int(to_english_digits(str(val)))
                return v if v >= 0 else None
            except (ValueError, TypeError):
                return None

        rooms = safe_int(raw.get("rooms"))
        floor = safe_int(raw.get("floor"))
        total_floors = safe_int(raw.get("total_floors"))
        building_age = safe_int(raw.get("building_age") or raw.get("age"))

        # Amenities
        def bool_val(v):
            if isinstance(v, bool):
                return v
            if isinstance(v, str):
                v_clean = v.strip().lower()
                return v_clean in ("true", "1", "دارد", "yes")
            return False

        parking = bool_val(raw.get("parking"))
        elevator = bool_val(raw.get("elevator"))
        storage = bool_val(raw.get("storage"))
        balcony = bool_val(raw.get("balcony"))

        return {
            "divar_token": str(token).strip(),
            "title": title or f"ملک در {neighborhood or 'تهران'}",
            "description": desc,
            "category": category,
            "city": city,
            "district": district,
            "neighborhood": neighborhood,
            "latitude": lat,
            "longitude": lon,
            "address_text": raw.get("address_text", ""),
            "price": price,
            "price_mode": raw.get("price_mode", "total"),
            "rent": rent,
            "deposit": deposit,
            "area_m2": area_m2,
            "price_per_m2": price_per_m2,
            "rent_per_m2": rent_per_m2,
            "deposit_per_m2": deposit_per_m2,
            "rooms": rooms,
            "floor": floor,
            "total_floors": total_floors,
            "building_age": building_age,
            "parking": parking,
            "elevator": elevator,
            "storage": storage,
            "balcony": balcony,
            "construction_type": raw.get("construction_type", ""),
            "property_type": raw.get("property_type", ""),
            "seller_type": raw.get("seller_type", ""),
            "source_url": raw.get("source_url") or f"https://divar.ir/v/{token}",
            "raw_json": raw,
        }


class ListingIngestionService:
    """
    Saves cleaned listings and tracks historical price snapshots.
    """

    @classmethod
    def ingest_listing(
        cls,
        raw_data: Dict[str, Any],
        partition: Optional[SearchPartition] = None,
    ) -> Tuple[Optional[DivarListing], bool]:
        """
        Ingests a listing. Compares against prior snapshot if existing.
        Returns (listing, is_new).
        """
        clean = ListingDataCleaner.clean_and_normalize(raw_data)
        if not clean:
            return None, False

        token = clean["divar_token"]
        existing = DivarListing.objects.filter(divar_token=token).first()

        now = django_tz.now()

        if not existing:
            # New listing
            listing = DivarListing.objects.create(
                divar_token=token,
                title=clean["title"],
                description=clean["description"],
                category=clean["category"],
                city=clean["city"],
                district=clean["district"],
                neighborhood=clean["neighborhood"],
                latitude=clean["latitude"],
                longitude=clean["longitude"],
                address_text=clean["address_text"],
                price=clean["price"],
                price_mode=clean["price_mode"],
                rent=clean["rent"],
                deposit=clean["deposit"],
                area_m2=clean["area_m2"],
                price_per_m2=clean["price_per_m2"],
                rent_per_m2=clean["rent_per_m2"],
                deposit_per_m2=clean["deposit_per_m2"],
                rooms=clean["rooms"],
                floor=clean["floor"],
                total_floors=clean["total_floors"],
                building_age=clean["building_age"],
                parking=clean["parking"],
                elevator=clean["elevator"],
                storage=clean["storage"],
                balcony=clean["balcony"],
                construction_type=clean["construction_type"],
                property_type=clean["property_type"],
                seller_type=clean["seller_type"],
                status="active",
                source_url=clean["source_url"],
                raw_json=clean["raw_json"],
            )

            # Initial snapshot
            ListingSnapshot.objects.create(
                listing=listing,
                price=listing.price,
                rent=listing.rent,
                deposit=listing.deposit,
                area_m2=listing.area_m2,
                price_per_m2=listing.price_per_m2,
                status="active",
                title=listing.title,
                raw_json=listing.raw_json,
                price_change_absolute=0,
                price_change_percent=0.0,
                price_per_m2_change=0,
                event_type=EVENT_INITIAL,
            )

            if partition:
                SearchPartitionExecution.objects.get_or_create(
                    partition=partition,
                    listing=listing,
                    defaults={"is_new_listing": True}
                )

            return listing, True

        else:
            # Existing listing: compare to last snapshot
            latest_snap = existing.snapshots.first()
            event_type = EVENT_UNCHANGED
            abs_change = 0
            pct_change = 0.0
            sqm_change = 0

            new_price = clean["price"]
            new_area = clean["area_m2"]
            new_sqm = clean["price_per_m2"]
            was_disappeared = existing.status == "disappeared"

            if latest_snap and latest_snap.price and new_price:
                diff = new_price - latest_snap.price
                if diff != 0:
                    abs_change = diff
                    pct_change = round((diff / latest_snap.price) * 100.0, 2)
                    if latest_snap.price_per_m2 and new_sqm:
                        sqm_change = new_sqm - latest_snap.price_per_m2

                    if diff < 0:
                        event_type = EVENT_PRICE_DECREASE
                    else:
                        event_type = EVENT_PRICE_INCREASE

            elif latest_snap and latest_snap.area_m2 != new_area and new_area is not None:
                event_type = EVENT_AREA_CHANGE
            elif latest_snap and latest_snap.title != clean["title"]:
                event_type = EVENT_TITLE_MODIFICATION
            elif was_disappeared:
                event_type = EVENT_REAPPEARED

            # Update listing fields
            existing.title = clean["title"]
            existing.description = clean["description"]
            existing.price = clean["price"]
            existing.rent = clean["rent"]
            existing.deposit = clean["deposit"]
            existing.area_m2 = clean["area_m2"]
            existing.price_per_m2 = clean["price_per_m2"]
            existing.rent_per_m2 = clean["rent_per_m2"]
            existing.deposit_per_m2 = clean["deposit_per_m2"]
            existing.status = "active"
            existing.last_seen_at = now
            existing.raw_json = clean["raw_json"]
            if clean["latitude"] and clean["longitude"]:
                existing.latitude = clean["latitude"]
                existing.longitude = clean["longitude"]
            existing.save()

            # Record snapshot if any change occurred or if over 24h since last snapshot
            time_since_snap = (now - latest_snap.captured_at).total_seconds() if latest_snap else 999999
            if event_type != EVENT_UNCHANGED or time_since_snap > 86400:
                ListingSnapshot.objects.create(
                    listing=existing,
                    price=existing.price,
                    rent=existing.rent,
                    deposit=existing.deposit,
                    area_m2=existing.area_m2,
                    price_per_m2=existing.price_per_m2,
                    status="active",
                    title=existing.title,
                    raw_json=existing.raw_json,
                    price_change_absolute=abs_change,
                    price_change_percent=pct_change,
                    price_per_m2_change=sqm_change,
                    event_type=event_type,
                )

            if partition:
                SearchPartitionExecution.objects.get_or_create(
                    partition=partition,
                    listing=existing,
                    defaults={"is_new_listing": False}
                )

            return existing, False
