"""
Tests for Data Science Outlier & Anomaly Detection Engine:
IQR, Robust Z-score (MAD), Isolation Forest, Local Comparable, and Ensemble Detector.
"""

import pytest
from core.constants import (
    CATEGORY_APARTMENT_SALE,
    CONFIDENCE_INSUFFICIENT,
    CONFIDENCE_STRONG,
)
from listings.models import DivarListing
from analytics.detectors import (
    ComparableDeviationDetector,
    EnsembleAnomalyDetector,
    IQRDetector,
    IsolationForestDetector,
    RobustZScoreDetector,
)


@pytest.fixture
def comparable_pool(db):
    """Fixture providing a pool of 20 comparable listings with median ~100M/m²."""
    pool = []
    # 20 listings ranging from 90M to 110M
    for i in range(20):
        sqm = 90_000_000 + (i * 1_000_000)
        item = DivarListing.objects.create(
            divar_token=f"peer_norm_{i}",
            title=f"آپارتمان همتا {i}",
            category=CATEGORY_APARTMENT_SALE,
            district=2,
            neighborhood="سعادت‌آباد",
            area_m2=100,
            rooms=2,
            building_age=5,
            floor=3,
            parking=True,
            elevator=True,
            storage=True,
            price=sqm * 100,
            price_per_m2=sqm,
        )
        pool.append(item)
    return pool


@pytest.mark.django_db
def test_iqr_detector(comparable_pool):
    detector = IQRDetector()

    # Normal target (100M / m²)
    normal_target = DivarListing(price_per_m2=100_000_000)
    res_normal = detector.detect(normal_target, comparable_pool)
    assert res_normal["is_anomaly"] is False

    # Anomalous low target (50M / m²)
    low_target = DivarListing(price_per_m2=50_000_000)
    res_low = detector.detect(low_target, comparable_pool)
    assert res_low["is_anomaly"] is True
    assert "Unusually low" in res_low["explanation"]


@pytest.mark.django_db
def test_robust_zscore_detector(comparable_pool):
    detector = RobustZScoreDetector()

    # Normal target
    normal_target = DivarListing(price_per_m2=100_000_000)
    res_norm = detector.detect(normal_target, comparable_pool)
    assert res_norm["is_anomaly"] is False
    assert abs(res_norm["score"]) < 2.5

    # Anomalous high target (220M / m² vs ~100M median)
    high_target = DivarListing(price_per_m2=220_000_000)
    res_high = detector.detect(high_target, comparable_pool)
    assert res_high["is_anomaly"] is True
    assert res_high["score"] >= 2.5


@pytest.mark.django_db
def test_isolation_forest_detector(comparable_pool):
    detector = IsolationForestDetector()

    # Normal listing
    normal_target = DivarListing(
        price_per_m2=100_000_000,
        area_m2=100,
        rooms=2,
        building_age=5,
        floor=3,
        parking=True,
        elevator=True,
        storage=True,
    )
    res_norm = detector.detect(normal_target, comparable_pool)
    assert "score" in res_norm

    # Multi-dimensional outlier: tiny area with massive price, 15 rooms, 40 years age
    weird_target = DivarListing(
        price_per_m2=450_000_000,
        area_m2=25,
        rooms=10,
        building_age=45,
        floor=12,
        parking=False,
        elevator=False,
        storage=False,
    )
    res_weird = detector.detect(weird_target, comparable_pool)
    assert res_weird["is_anomaly"] is True


@pytest.mark.django_db
def test_ensemble_insufficient_sample():
    """Ensemble must require at least 15 samples; otherwise return confidence=insufficient_data."""
    ensemble = EnsembleAnomalyDetector(min_samples=15)
    target = DivarListing(price_per_m2=50_000_000)

    # Only 5 comparables
    small_pool = [DivarListing(price_per_m2=100_000_000) for _ in range(5)]
    res = ensemble.evaluate(target, small_pool)

    assert res["is_anomaly"] is False
    assert res["confidence"] == CONFIDENCE_INSUFFICIENT
    assert "Insufficient comparable data" in res["explanation"]


@pytest.mark.django_db
def test_ensemble_strong_anomaly(comparable_pool):
    """With 20 comparables, an extreme price deviation triggers strong anomaly confidence."""
    ensemble = EnsembleAnomalyDetector(min_samples=15)
    # Price is 45M vs 100M median (-55% deviation)
    target = DivarListing(
        price_per_m2=45_000_000,
        area_m2=100,
        rooms=2,
        building_age=5,
        floor=3,
        parking=True,
        elevator=True,
        storage=True,
    )
    res = ensemble.evaluate(target, comparable_pool)

    assert res["is_anomaly"] is True
    assert res["confidence"] == CONFIDENCE_STRONG
    assert res["flagged_count"] >= 3
    # Verify objective explanation phrasing
    assert "Statistically unusual relative to comparable observed listings" in res["explanation"]
    assert "bargain" not in res["explanation"].lower()
    assert "investment" not in res["explanation"].lower()
