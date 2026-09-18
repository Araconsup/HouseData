"""
Management command to seed realistic mock Tehran real estate listings,
historical snapshots, search partitions, API logs, anomaly results,
and market statistics for immediate demonstration.
"""

import random
import time
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone as django_tz

from analytics.pipeline import AnomalyPipelineService
from analytics.statistics import MarketStatisticsService
from core.constants import (
    CATEGORY_APARTMENT_RENT,
    CATEGORY_APARTMENT_SALE,
    CATEGORY_HOUSE_VILLA_SALE,
    EVENT_INITIAL,
    EVENT_PRICE_DECREASE,
    EVENT_PRICE_INCREASE,
    EVENT_UNCHANGED,
)
from core.tehran_data import TEHRAN_DISTRICTS
from ingestion.coverage import CoverageEngine
from ingestion.models import ApiRequestLog, SearchPartition
from listings.models import DivarListing, ListingSnapshot, SearchPartitionExecution


class Command(BaseCommand):
    help = "Seeds database with realistic Tehran listings, snapshots, and partitions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=350,
            help="Number of listings to generate (default: 350)",
        )

    def handle(self, *args, **options):
        count = options["count"]
        self.stdout.write(self.style.NOTICE(f"Generating {count} realistic Tehran listings..."))

        # 1. Generate standard search partitions
        partitions_created = CoverageEngine.generate_standard_partitions()
        self.stdout.write(self.style.SUCCESS(f"Generated {partitions_created} search partitions."))
        all_partitions = list(SearchPartition.objects.all())

        now = django_tz.now()

        # 2. Generate listings across all 22 districts
        districts_pool = list(range(1, 23))

        created_listings = []
        for i in range(count):
            dist_id = random.choice(districts_pool)
            dist_data = TEHRAN_DISTRICTS[dist_id]
            nh = random.choice(dist_data["neighborhoods"])

            # 85% Sale, 15% Rent
            is_rent = random.random() < 0.15
            category = CATEGORY_APARTMENT_RENT if is_rent else (
                CATEGORY_HOUSE_VILLA_SALE if random.random() < 0.10 else CATEGORY_APARTMENT_SALE
            )

            # Area modeling
            area = random.choice([55, 68, 75, 85, 92, 105, 118, 135, 150, 175, 210, 260]) + random.randint(-4, 4)

            # Rooms modeling
            if area < 65:
                rooms = 1
            elif area < 110:
                rooms = 2
            elif area < 185:
                rooms = 3
            else:
                rooms = 4

            # Price modeling by district tier (in Tomans)
            if dist_id in (1, 2, 3):
                base_sqm = random.randint(155_000_000, 310_000_000)
            elif dist_id in (5, 6, 7):
                base_sqm = random.randint(95_000_000, 170_000_000)
            elif dist_id in (4, 8, 22):
                base_sqm = random.randint(75_000_000, 125_000_000)
            elif dist_id in (9, 10, 11, 12, 13, 14):
                base_sqm = random.randint(52_000_000, 88_000_000)
            else:
                base_sqm = random.randint(35_000_000, 62_000_000)

            # Plant intentional statistical anomalies in ~7% of listings
            is_planted_anomaly = False
            if i % 14 == 0 and not is_rent:
                is_planted_anomaly = True
                anomaly_type = random.choice(["underpriced", "overpriced"])
                if anomaly_type == "underpriced":
                    # 32% - 40% below peer median
                    base_sqm = int(base_sqm * random.uniform(0.60, 0.68))
                else:
                    # 35% - 50% above peer median
                    base_sqm = int(base_sqm * random.uniform(1.35, 1.50))

            sale_price = base_sqm * area if not is_rent else None
            deposit = int(base_sqm * area * 0.16) if is_rent else None
            monthly_rent = int(deposit * 0.025) if is_rent else None

            # Coordinates
            lat_c, lon_c = dist_data["center"]
            lat = lat_c + random.uniform(-0.012, 0.012)
            lon = lon_c + random.uniform(-0.012, 0.012)

            age = random.randint(0, 22)
            floor = random.randint(1, 7)
            total_floors = floor + random.randint(0, 3)

            parking = random.random() > 0.15
            elevator = random.random() > 0.20 if total_floors > 3 else (random.random() > 0.5)
            storage = random.random() > 0.10
            balcony = random.random() > 0.25

            token = f"teh_{dist_id}_{int(time.time())}_{i}_{random.randint(1000, 9999)}"
            pub_days_ago = random.randint(0, 30)
            published_at = now - timedelta(days=pub_days_ago, hours=random.randint(1, 23))

            title = (
                f"آپارتمان {area} متری {rooms} خوابه در {nh}"
                if category == CATEGORY_APARTMENT_SALE
                else f"ملک {area} متری در {nh}"
            )

            listing = DivarListing.objects.create(
                divar_token=token,
                title=title,
                description=f"{title} دارای نور عالی، پلان مهندسی‌شده، متریال مرغوب و دسترسی سریع به بزرگراه‌ها و مراکز خرید.",
                category=category,
                city="tehran",
                district=dist_id,
                neighborhood=nh,
                latitude=round(lat, 5),
                longitude=round(lon, 5),
                price=sale_price,
                price_mode="total",
                rent=monthly_rent,
                deposit=deposit,
                area_m2=area,
                price_per_m2=base_sqm if not is_rent else None,
                deposit_per_m2=int(deposit / area) if is_rent and deposit else None,
                rent_per_m2=int(monthly_rent / area) if is_rent and monthly_rent else None,
                rooms=rooms,
                floor=floor,
                total_floors=total_floors,
                building_age=age,
                parking=parking,
                elevator=elevator,
                storage=storage,
                balcony=balcony,
                construction_type="اسکلت بتنی" if age < 15 else "اسکلت فلزی",
                property_type="آپارتمان",
                seller_type="شخصی" if random.random() > 0.6 else "مشاور املاک",
                published_at=published_at,
                first_seen_at=published_at,
                last_seen_at=now,
                status="active",
                source_url=f"https://divar.ir/v/{token}",
            )

            # Snapshots: create initial snapshot
            snap_time = published_at
            ListingSnapshot.objects.create(
                listing=listing,
                captured_at=snap_time,
                price=listing.price,
                rent=listing.rent,
                deposit=listing.deposit,
                area_m2=listing.area_m2,
                price_per_m2=listing.price_per_m2,
                status="active",
                title=listing.title,
                event_type=EVENT_INITIAL,
            )

            # Create price change snapshots on ~25% of properties
            if pub_days_ago > 7 and random.random() < 0.25 and listing.price:
                # Prior higher price (price reduction detected!)
                old_price = int(listing.price * random.uniform(1.04, 1.10))
                old_sqm = int(old_price / listing.area_m2)
                ListingSnapshot.objects.create(
                    listing=listing,
                    captured_at=snap_time + timedelta(days=random.randint(3, 6)),
                    price=listing.price,
                    rent=listing.rent,
                    deposit=listing.deposit,
                    area_m2=listing.area_m2,
                    price_per_m2=listing.price_per_m2,
                    status="active",
                    title=listing.title,
                    price_change_absolute=listing.price - old_price,
                    price_change_percent=round(((listing.price - old_price) / old_price) * 100, 2),
                    price_per_m2_change=listing.price_per_m2 - old_sqm,
                    event_type=EVENT_PRICE_DECREASE,
                )

            # Link to partition
            matching_p = [p for p in all_partitions if p.district == dist_id and p.category == category]
            if matching_p:
                p = matching_p[0]
                SearchPartitionExecution.objects.create(
                    partition=p,
                    listing=listing,
                    is_new_listing=True,
                )
                p.result_count += 1
                p.unique_listings_count += 1
                p.last_run = now
                p.successful = True
                p.save()

            created_listings.append(listing)

        # 3. Create realistic ApiRequestLog entries
        for p in random.sample(all_partitions, min(len(all_partitions), 30)):
            ApiRequestLog.objects.create(
                partition=p,
                endpoint="https://open-api.divar.ir/v2/open-platform/finder/post",
                http_status=200,
                response_time_ms=random.randint(180, 520),
                number_of_results=p.result_count or random.randint(15, 80),
                request_id=f"req_{random.randint(100000, 999999)}",
            )

        self.stdout.write(self.style.NOTICE("Running anomaly detection pipeline..."))
        # 4. Run anomaly detection
        batch_res = AnomalyPipelineService.run_batch_detection()
        self.stdout.write(self.style.SUCCESS(f"Anomaly detection complete: {batch_res}"))

        self.stdout.write(self.style.NOTICE("Computing comprehensive market statistics..."))
        # 5. Compute market statistics
        stat_count = MarketStatisticsService.compute_all_statistics()
        self.stdout.write(self.style.SUCCESS(f"Market statistics complete: {stat_count} records saved."))

        self.stdout.write(self.style.SUCCESS("All seed data successfully generated!"))
