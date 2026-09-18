"""
Celery background tasks for Divar ingestion and collection partitioning.
"""

import logging
from celery import shared_task
from django.utils import timezone as django_tz

from ingestion.client import DivarApiClient, DivarApiError, DivarQuotaExceededError
from ingestion.models import SearchPartition
from listings.pipeline import ListingDataCleaner, ListingIngestionService
from listings.models import DivarListing, ListingSnapshot

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def collect_partition(self, partition_id: int):
    """
    Executes a single search partition query against the Divar Open API,
    ingests returned listings, updates snapshot records, and logs performance.
    """
    partition = SearchPartition.objects.filter(id=partition_id, active=True).first()
    if not partition:
        logger.warning(f"SearchPartition {partition_id} not found or inactive")
        return {"status": "skipped", "reason": "partition_not_found"}

    client = DivarApiClient()
    try:
        posts = client.search_posts(
            city=partition.city,
            category=partition.category,
            district=partition.district,
            neighborhood=partition.neighborhood or None,
            min_area=partition.min_area,
            max_area=partition.max_area,
            min_price=partition.min_price,
            max_price=partition.max_price,
            min_rooms=partition.min_rooms,
            max_rooms=partition.max_rooms,
            only_with_parking=partition.only_with_parking,
            only_with_elevator=partition.only_with_elevator,
            partition_id=partition.id,
        )

        new_count = 0
        duplicate_count = 0

        for post in posts:
            _, is_new = ListingIngestionService.ingest_listing(post, partition=partition)
            if is_new:
                new_count += 1
            else:
                duplicate_count += 1

        partition.last_run = django_tz.now()
        partition.result_count = len(posts)
        partition.unique_listings_count = new_count
        partition.duplicate_listings_count = duplicate_count
        partition.successful = True
        partition.error_message = ""
        partition.save()

        logger.info(
            f"Partition {partition.name} complete: {len(posts)} found ({new_count} new, {duplicate_count} seen)"
        )
        return {
            "status": "success",
            "partition_id": partition_id,
            "total_results": len(posts),
            "new_listings": new_count,
            "duplicate_listings": duplicate_count,
        }

    except DivarQuotaExceededError as exc:
        logger.warning(f"Quota exceeded during partition {partition_id}: {exc}")
        partition.error_message = f"Quota exceeded: {exc}"
        partition.successful = False
        partition.save()
        return {"status": "quota_exceeded", "error": str(exc)}

    except DivarApiError as exc:
        logger.error(f"Divar API error during partition {partition_id}: {exc}")
        partition.error_message = str(exc)
        partition.successful = False
        partition.save()
        try:
            self.retry(exc=exc)
        except Exception:
            pass
        return {"status": "failed", "error": str(exc)}


@shared_task
def fetch_listing_details(token: str):
    """
    Fetches full listing details for a token from Divar Kenar v1 API.
    """
    client = DivarApiClient()
    try:
        data = client.get_post_details(token)
        listing = DivarListing.objects.filter(divar_token=token).first()
        if listing:
            listing.raw_json = data
            listing.save(update_fields=["raw_json"])
        return {"status": "success", "token": token}
    except Exception as e:
        logger.error(f"Failed to fetch details for {token}: {e}")
        return {"status": "error", "error": str(e)}


@shared_task
def normalize_listing(raw_data: dict):
    """
    Normalizes a single raw listing dictionary and persists it.
    """
    listing, is_new = ListingIngestionService.ingest_listing(raw_data)
    if listing:
        return {"status": "success", "token": listing.divar_token, "is_new": is_new}
    return {"status": "invalid_data"}


@shared_task
def create_snapshot(listing_id: int):
    """
    Creates an explicit historical snapshot for a listing.
    """
    listing = DivarListing.objects.filter(id=listing_id).first()
    if not listing:
        return {"status": "listing_not_found"}

    snap = ListingSnapshot.objects.create(
        listing=listing,
        price=listing.price,
        rent=listing.rent,
        deposit=listing.deposit,
        area_m2=listing.area_m2,
        price_per_m2=listing.price_per_m2,
        status=listing.status,
        title=listing.title,
        raw_json=listing.raw_json,
    )
    return {"status": "success", "snapshot_id": snap.id}
