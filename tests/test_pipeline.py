"""
Tests for Data Cleaning, Normalization Pipeline, Duplicate Token Handling,
and Historical Price Snapshot Tracking.
"""

import pytest
from core.constants import EVENT_INITIAL, EVENT_PRICE_DECREASE, EVENT_PRICE_INCREASE
from listings.models import DivarListing, ListingSnapshot
from listings.pipeline import ListingDataCleaner, ListingIngestionService


def test_listing_cleaner_validation():
    # Missing token returns None
    assert ListingDataCleaner.clean_and_normalize({"title": "بی توکن"}) is None

    # Normalization of Persian digits and area
    raw = {
        "token": "tok_test_101",
        "title": "آپارتمان ۱۰۰ متری در سعادت‌آباد",
        "area_m2": "۱۰۰",
        "price": "۱۲,۰۰۰,۰۰۰,۰۰۰ تومان",
        "district": "۲",
        "rooms": "۲",
        "parking": "دارد",
        "elevator": True,
    }
    cleaned = ListingDataCleaner.clean_and_normalize(raw)
    assert cleaned is not None
    assert cleaned["divar_token"] == "tok_test_101"
    assert cleaned["area_m2"] == 100.0
    assert cleaned["price"] == 12_000_000_000
    assert cleaned["price_per_m2"] == 120_000_000  # 12B / 100
    assert cleaned["district"] == 2
    assert cleaned["rooms"] == 2
    assert cleaned["parking"] is True
    assert cleaned["elevator"] is True


@pytest.mark.django_db
def test_ingestion_new_listing_and_initial_snapshot():
    raw = {
        "token": "tok_unique_001",
        "title": "آپارتمان ۷۵ متری",
        "area_m2": 75,
        "price": 7_500_000_000,
        "district": 5,
    }
    listing, is_new = ListingIngestionService.ingest_listing(raw)
    assert is_new is True
    assert listing.divar_token == "tok_unique_001"
    assert listing.price_per_m2 == 100_000_000

    # Verify initial snapshot
    assert listing.snapshots.count() == 1
    snap = listing.snapshots.first()
    assert snap.event_type == EVENT_INITIAL
    assert snap.price == 7_500_000_000


@pytest.mark.django_db
def test_duplicate_token_and_price_history_tracking():
    raw_initial = {
        "token": "tok_price_change_002",
        "title": "آپارتمان در نیاوران",
        "area_m2": 100,
        "price": 20_000_000_000,
        "district": 1,
    }
    listing, is_new = ListingIngestionService.ingest_listing(raw_initial)
    assert is_new is True

    # Re-ingest same token with lower price (Price reduction!)
    raw_reduced = {
        "token": "tok_price_change_002",
        "title": "آپارتمان در نیاوران",
        "area_m2": 100,
        "price": 18_000_000_000,  # dropped by 2 billion
        "district": 1,
    }
    listing_updated, is_new_2 = ListingIngestionService.ingest_listing(raw_reduced)
    assert is_new_2 is False
    assert listing_updated.id == listing.id  # No duplicate record created!
    assert DivarListing.objects.filter(divar_token="tok_price_change_002").count() == 1

    # Verify snapshots
    assert listing_updated.snapshots.count() == 2
    latest_snap = listing_updated.snapshots.first()
    assert latest_snap.event_type == EVENT_PRICE_DECREASE
    assert latest_snap.price == 18_000_000_000
    assert latest_snap.price_change_absolute == -2_000_000_000
    assert latest_snap.price_change_percent == -10.0  # -10% drop
