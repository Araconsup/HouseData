"""
Tests for Comparable Property Selection Engine.
"""

import pytest
from core.constants import CATEGORY_APARTMENT_RENT, CATEGORY_APARTMENT_SALE
from listings.models import DivarListing
from analytics.comparables import ComparableService


@pytest.mark.django_db
def test_comparable_never_mixes_sale_and_rent():
    # Create target sale property
    target_sale = DivarListing.objects.create(
        divar_token="target_sale_1",
        title="فروش در منطقه ۲",
        category=CATEGORY_APARTMENT_SALE,
        district=2,
        area_m2=100,
        price=10_000_000_000,
        price_per_m2=100_000_000,
        rooms=2,
    )

    # Create rental property in same location and area
    rental = DivarListing.objects.create(
        divar_token="rental_prop_1",
        title="اجاره در منطقه ۲",
        category=CATEGORY_APARTMENT_RENT,
        district=2,
        area_m2=100,
        deposit=1_000_000_000,
        rent=30_000_000,
        rooms=2,
    )

    # Create peer sale properties
    for i in range(5):
        DivarListing.objects.create(
            divar_token=f"sale_peer_{i}",
            title=f"فروش مشابه {i}",
            category=CATEGORY_APARTMENT_SALE,
            district=2,
            area_m2=105,
            price=10_500_000_000,
            price_per_m2=100_000_000,
            rooms=2,
        )

    comparables, criteria = ComparableService.get_comparables(target_sale)

    # Verify rental property was NOT included in sale comparables
    comp_tokens = [c.divar_token for c in comparables]
    assert "rental_prop_1" not in comp_tokens
    assert any("خرید و فروش" in crit for crit in criteria)


@pytest.mark.django_db
def test_comparable_metrics_calculation():
    target = DivarListing.objects.create(
        divar_token="target_metric_1",
        title="ملک هدف",
        category=CATEGORY_APARTMENT_SALE,
        district=1,
        area_m2=100,
        price=15_000_000_000,
        price_per_m2=150_000_000,
    )

    # Create 5 comparables with median 100M/m²
    comps = []
    prices = [90_000_000, 95_000_000, 100_000_000, 105_000_000, 110_000_000]
    for idx, p in enumerate(prices):
        c = DivarListing.objects.create(
            divar_token=f"comp_metric_{idx}",
            title=f"ملک همتا {idx}",
            category=CATEGORY_APARTMENT_SALE,
            district=1,
            area_m2=100,
            price=p * 100,
            price_per_m2=p,
        )
        comps.append(c)

    metrics = ComparableService.calculate_comparable_metrics(target, comps)
    assert metrics["sample_size"] == 5
    assert metrics["median_sqm"] == 100_000_000
    # Target is 150M vs 100M median -> +50% deviation
    assert metrics["deviation_percent"] == 50.0
