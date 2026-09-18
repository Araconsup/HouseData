"""
Ingestion models for search partitions, execution tracking, and API logs.
"""

from django.db import models
from core.constants import CATEGORY_CHOICES, CATEGORY_APARTMENT_SALE


class SearchPartition(models.Model):
    """
    Configurable search partition for segmenting Divar queries
    within the 100-result search limit.
    """
    name = models.CharField(max_length=255, help_text="Human-readable partition label")
    category = models.CharField(
        max_length=64,
        choices=CATEGORY_CHOICES,
        default=CATEGORY_APARTMENT_SALE,
        db_index=True
    )
    city = models.CharField(max_length=64, default="tehran", db_index=True)
    district = models.IntegerField(null=True, blank=True, db_index=True, help_text="Tehran District (1-22)")
    neighborhood = models.CharField(max_length=128, blank=True, db_index=True)
    min_area = models.IntegerField(null=True, blank=True)
    max_area = models.IntegerField(null=True, blank=True)
    min_price = models.BigIntegerField(null=True, blank=True, help_text="Minimum price in Tomans")
    max_price = models.BigIntegerField(null=True, blank=True, help_text="Maximum price in Tomans")
    min_rooms = models.IntegerField(null=True, blank=True)
    max_rooms = models.IntegerField(null=True, blank=True)
    only_with_parking = models.BooleanField(default=False)
    only_with_elevator = models.BooleanField(default=False)

    active = models.BooleanField(default=True, db_index=True)
    last_run = models.DateTimeField(null=True, blank=True)
    result_count = models.IntegerField(default=0, help_text="Listings found in last execution")
    unique_listings_count = models.IntegerField(default=0, help_text="Unique new listings found")
    duplicate_listings_count = models.IntegerField(default=0, help_text="Duplicate listings already observed")
    successful = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["district", "category", "min_area"]
        indexes = [
            models.Index(fields=["city", "district", "category"]),
            models.Index(fields=["active", "last_run"]),
        ]

    def __str__(self):
        dist_str = f"D{self.district}" if self.district else "All"
        area_str = f"{self.min_area}-{self.max_area}m²" if self.min_area or self.max_area else "Any-Area"
        return f"{self.name} [{dist_str} | {self.category} | {area_str}]"

    @property
    def coverage_efficiency(self) -> float:
        """Percentage of returned listings that were brand new to our dataset."""
        total = self.result_count
        if total == 0:
            return 0.0
        return round((self.unique_listings_count / total) * 100.0, 1)


class ApiRequestLog(models.Model):
    """
    Audit log of all outbound Divar API requests for accounting and safety.
    """
    request_time = models.DateTimeField(auto_now_add=True, db_index=True)
    partition = models.ForeignKey(
        SearchPartition,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="api_logs"
    )
    endpoint = models.CharField(max_length=255)
    http_status = models.IntegerField(null=True, blank=True)
    response_time_ms = models.IntegerField(help_text="Response time in milliseconds")
    number_of_results = models.IntegerField(default=0)
    error = models.TextField(blank=True)
    request_id = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ["-request_time"]
        indexes = [
            models.Index(fields=["request_time", "http_status"]),
        ]

    def __str__(self):
        status = self.http_status or "ERR"
        return f"{self.request_time.strftime('%Y-%m-%d %H:%M:%S')} - {self.endpoint} [{status}] ({self.number_of_results} results)"
