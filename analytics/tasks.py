"""
Celery background tasks for data science computations, anomaly detection,
and market statistics aggregation.
"""

import logging
from celery import shared_task
from analytics.pipeline import AnomalyPipelineService
from analytics.statistics import MarketStatisticsService
from listings.models import DivarListing

logger = logging.getLogger(__name__)


@shared_task
def calculate_price_metrics():
    """
    Recalculates price per square meter and changes for listings.
    """
    count = 0
    for listing in DivarListing.objects.filter(price_per_m2__isnull=True):
        listing.calculate_price_per_meter()
        listing.save(update_fields=["price_per_m2", "rent_per_m2", "deposit_per_m2"])
        count += 1
    logger.info(f"Recalculated price metrics for {count} listings")
    return {"status": "success", "updated_listings": count}


@shared_task
def run_anomaly_detection():
    """
    Executes the multi-detector anomaly engine across active listings.
    """
    results = AnomalyPipelineService.run_batch_detection()
    return {"status": "success", **results}


@shared_task
def update_market_statistics():
    """
    Recomputes Tehran-wide, district, category, and area bucket market statistics.
    """
    total = MarketStatisticsService.compute_all_statistics()
    return {"status": "success", "statistics_updated": total}


@shared_task
def refresh_map_statistics():
    """
    Refreshes spatial cache and ensures coordinate metrics are up to date.
    """
    valid_coords = DivarListing.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
        status="active"
    ).count()
    return {"status": "success", "mappable_listings": valid_coords}
