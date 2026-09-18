"""
Management command to fetch real live listings from Divar Kenar Open API,
enrich them with full post details, and update anomaly detection & statistics.
"""

import time
from django.core.management.base import BaseCommand
from analytics.pipeline import AnomalyPipelineService
from analytics.statistics import MarketStatisticsService
from core.constants import (
    CATEGORY_APARTMENT_RENT,
    CATEGORY_APARTMENT_SALE,
    CATEGORY_HOUSE_VILLA_SALE,
)
from core.normalizers import format_toman
from ingestion.client import DivarApiClient
from listings.models import DivarListing
from listings.pipeline import ListingIngestionService


class Command(BaseCommand):
    help = "Pulls real live listings from Divar Kenar Open API into local database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=60,
            help="Maximum number of detailed listings to fetch (default: 60)",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        client = DivarApiClient()

        if client.mock_mode:
            self.stdout.write(self.style.WARNING("Warning: Divar client is in Mock mode!"))
        else:
            self.stdout.write(self.style.SUCCESS("Connecting to live Divar Kenar Open API..."))

        categories = [
            CATEGORY_APARTMENT_SALE,
            CATEGORY_APARTMENT_RENT,
            CATEGORY_HOUSE_VILLA_SALE,
        ]

        total_ingested = 0

        for cat in categories:
            self.stdout.write(self.style.NOTICE(f"Searching Divar for {cat}..."))
            try:
                posts = client.search_posts(city="tehran", category=cat)
                self.stdout.write(self.style.SUCCESS(f"Divar returned {len(posts)} posts for {cat}"))

                # Ingest listings directly from search results
                cat_count = 0
                for p in posts:
                    if total_ingested >= limit:
                        break

                    token = p.get("token")
                    if not token:
                        continue

                    try:
                        listing, is_new = ListingIngestionService.ingest_listing(p)
                        if listing:
                            total_ingested += 1
                            cat_count += 1
                            price_str = format_toman(listing.price) if listing.price else f"ودیعه: {format_toman(listing.deposit)}"
                            self.stdout.write(
                                f"  ✓ [{token}] {listing.title[:38]} | D{listing.district or '—'} | "
                                f"{int(listing.area_m2 or 0)}m² | {price_str}"
                            )
                    except Exception as exc:
                        self.stdout.write(self.style.WARNING(f"  ✗ Error on {token}: {exc}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error querying {cat}: {e}"))

            if total_ingested >= limit:
                break

        self.stdout.write(self.style.SUCCESS(f"Ingested {total_ingested} real listings from Divar."))

        # Run anomaly detection
        self.stdout.write(self.style.NOTICE("Running anomaly detection on live dataset..."))
        anom_res = AnomalyPipelineService.run_batch_detection()
        self.stdout.write(self.style.SUCCESS(f"Anomaly detection complete: {anom_res}"))

        # Update market statistics
        self.stdout.write(self.style.NOTICE("Updating Tehran market statistics..."))
        stats_count = MarketStatisticsService.compute_all_statistics()
        self.stdout.write(self.style.SUCCESS(f"Market statistics updated: {stats_count} records."))
