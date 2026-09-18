"""
Tests for Celery Background Tasks.
"""

import pytest
from analytics.tasks import (
    calculate_price_metrics,
    run_anomaly_detection,
    update_market_statistics,
)
from core.constants import CATEGORY_APARTMENT_SALE
from ingestion.models import SearchPartition
from ingestion.tasks import collect_partition
from listings.models import DivarListing


@pytest.mark.django_db
def test_collect_partition_task(settings):
    settings.MOCK_DIVAR_API = True
    partition = SearchPartition.objects.create(
        name="پارتیشن تست منطقه ۲",
        category=CATEGORY_APARTMENT_SALE,
        district=2,
        city="tehran",
        min_area=70,
        max_area=100,
        active=True,
    )

    result = collect_partition(partition.id)
    assert result["status"] == "success"
    assert result["total_results"] > 0
    partition.refresh_from_db()
    assert partition.last_run is not None
    assert partition.successful is True
    assert partition.result_count > 0


@pytest.mark.django_db
def test_calculate_price_metrics_task():
    listing = DivarListing.objects.create(
        divar_token="task_metric_tok",
        title="ملک محاسبه متری",
        category=CATEGORY_APARTMENT_SALE,
        area_m2=100,
        price=10_000_000_000,
        price_per_m2=None,  # missing
    )

    res = calculate_price_metrics()
    assert res["status"] == "success"
    listing.refresh_from_db()
    assert listing.price_per_m2 == 100_000_000


@pytest.mark.django_db
def test_analytics_and_statistics_tasks():
    # Populate a sample listing
    DivarListing.objects.create(
        divar_token="task_stat_tok",
        title="آپارتمان منطقه ۱",
        category=CATEGORY_APARTMENT_SALE,
        district=1,
        area_m2=120,
        price=24_000_000_000,
        price_per_m2=200_000_000,
        status="active",
    )

    # Anomaly detection task
    res_anom = run_anomaly_detection()
    assert res_anom["status"] == "success"

    # Market statistics task
    res_stats = update_market_statistics()
    assert res_stats["status"] == "success"
    assert res_stats["statistics_updated"] > 0
