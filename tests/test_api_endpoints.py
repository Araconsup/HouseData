"""
Tests for Django REST Framework API Endpoints.
"""

import pytest
from rest_framework.test import APIClient
from core.constants import CATEGORY_APARTMENT_SALE
from listings.models import DivarListing, ListingSnapshot
from analytics.models import AnomalyResult, MarketStatistic
from ingestion.models import SearchPartition


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def sample_listing(db):
    listing = DivarListing.objects.create(
        divar_token="test_tok_endpoint_1",
        title="آپارتمان در سعادت آباد",
        category=CATEGORY_APARTMENT_SALE,
        city="tehran",
        district=2,
        neighborhood="سعادت‌آباد",
        area_m2=100,
        price=12_000_000_000,
        price_per_m2=120_000_000,
        latitude=35.78,
        longitude=51.36,
        rooms=2,
        is_anomaly=True,
        anomaly_score=-32.5,
    )
    ListingSnapshot.objects.create(
        listing=listing,
        price=12_000_000_000,
        price_per_m2=120_000_000,
        area_m2=100,
    )
    AnomalyResult.objects.create(
        listing=listing,
        detector_name="ensemble",
        score=-32.5,
        is_anomaly=True,
        explanation="Statistically unusual relative to comparable observed listings.",
        sample_size=25,
        confidence="strong",
    )
    return listing


@pytest.mark.django_db
def test_listings_api_list(client, sample_listing):
    res = client.get("/api/listings/")
    assert res.status_code == 200
    assert res.data["count"] >= 1
    results = res.data["results"]
    assert results[0]["divar_token"] == sample_listing.divar_token
    assert "price_formatted" in results[0]


@pytest.mark.django_db
def test_listings_api_detail(client, sample_listing):
    res = client.get(f"/api/listings/{sample_listing.divar_token}/")
    assert res.status_code == 200
    assert res.data["divar_token"] == sample_listing.divar_token
    assert len(res.data["snapshots"]) >= 1


@pytest.mark.django_db
def test_listings_api_history(client, sample_listing):
    res = client.get(f"/api/listings/{sample_listing.divar_token}/history/")
    assert res.status_code == 200
    assert res.data["listing_token"] == sample_listing.divar_token
    assert len(res.data["snapshots"]) >= 1


@pytest.mark.django_db
def test_listings_api_comparables(client, sample_listing):
    res = client.get(f"/api/listings/{sample_listing.divar_token}/comparables/")
    assert res.status_code == 200
    assert "target" in res.data
    assert "metrics" in res.data
    assert "comparables" in res.data


@pytest.mark.django_db
def test_listings_api_map_points(client, sample_listing):
    res = client.get("/api/listings/map-points/")
    assert res.status_code == 200
    assert "points" in res.data
    assert res.data["count"] >= 1
    first_pt = res.data["points"][0]
    assert "latitude" in first_pt
    assert "longitude" in first_pt
    assert "price_per_m2_formatted" in first_pt


@pytest.mark.django_db
def test_anomalies_api(client, sample_listing):
    res = client.get("/api/anomalies/")
    assert res.status_code == 200
    assert res.data["count"] >= 1
    item = res.data["results"][0]
    assert item["is_anomaly"] is True
    assert item["listing"]["divar_token"] == sample_listing.divar_token


@pytest.mark.django_db
def test_statistics_endpoints(client, sample_listing):
    MarketStatistic.objects.create(
        dimension="tehran",
        dimension_value="overall",
        transaction_type="sale",
        listing_count=100,
        median_price_per_m2=110_000_000,
    )
    res_t = client.get("/api/statistics/tehran/")
    assert res_t.status_code == 200

    res_d = client.get("/api/statistics/districts/?type=sale")
    assert res_d.status_code == 200

    res_dash = client.get("/api/statistics/dashboard-summary/")
    assert res_dash.status_code == 200
    assert "kpis" in res_dash.data
    assert "charts" in res_dash.data


@pytest.mark.django_db
def test_collection_endpoints(client):
    SearchPartition.objects.create(name="منطقه ۱ - فروش", district=1, category="apartment-sale")
    res_status = client.get("/api/collection/status/")
    assert res_status.status_code == 200
    assert "api" in res_status.data
    assert "coverage_matrix" in res_status.data

    res_part = client.get("/api/collection/partitions/")
    assert res_part.status_code == 200
    assert res_part.data["count"] >= 1
