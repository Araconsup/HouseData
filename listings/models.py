"""
Normalized property listing and historical snapshot database models.
"""

from django.db import models
from core.constants import CATEGORY_CHOICES, EVENT_INITIAL
from ingestion.models import SearchPartition


class DivarListing(models.Model):
    """
    Normalized Tehran real-estate listing from Divar Kenar Open API.
    Preserves raw JSON while indexing key analytical columns.
    """
    divar_token = models.CharField(max_length=64, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=64, choices=CATEGORY_CHOICES, db_index=True)
    city = models.CharField(max_length=64, default="tehran", db_index=True)
    district = models.IntegerField(null=True, blank=True, db_index=True, help_text="Tehran District 1-22")
    neighborhood = models.CharField(max_length=128, blank=True, db_index=True)

    # Geographic coordinates
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    address_text = models.CharField(max_length=512, blank=True)

    # Price attributes in normalized Tomans
    price = models.BigIntegerField(null=True, blank=True, db_index=True, help_text="Total price in Tomans (sale)")
    price_mode = models.CharField(max_length=32, default="total", help_text="total, agreement, per_meter")
    rent = models.BigIntegerField(null=True, blank=True, help_text="Monthly rent in Tomans")
    deposit = models.BigIntegerField(null=True, blank=True, help_text="Mortgage / deposit in Tomans")

    # Property specifications
    area_m2 = models.FloatField(null=True, blank=True, db_index=True)
    price_per_m2 = models.BigIntegerField(null=True, blank=True, db_index=True, help_text="Sale price per m² in Tomans")
    rent_per_m2 = models.BigIntegerField(null=True, blank=True, help_text="Rent per m² in Tomans")
    deposit_per_m2 = models.BigIntegerField(null=True, blank=True, help_text="Deposit per m² in Tomans")

    rooms = models.IntegerField(null=True, blank=True)
    floor = models.IntegerField(null=True, blank=True)
    total_floors = models.IntegerField(null=True, blank=True)
    building_age = models.IntegerField(null=True, blank=True, help_text="Age in years")

    # Amenities
    parking = models.BooleanField(default=False)
    elevator = models.BooleanField(default=False)
    storage = models.BooleanField(default=False)
    balcony = models.BooleanField(default=False)

    construction_type = models.CharField(max_length=64, blank=True)
    property_type = models.CharField(max_length=64, blank=True)
    seller_type = models.CharField(max_length=64, blank=True, help_text="personal, real_estate_agency")

    # Temporal & Tracking
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_modified_at = models.DateTimeField(null=True, blank=True, db_index=True)
    first_seen_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=32, default="active", db_index=True)
    source_url = models.URLField(max_length=512, blank=True)
    raw_json = models.JSONField(default=dict)

    # Anomaly Detection Summary Cache
    anomaly_score = models.FloatField(null=True, blank=True, db_index=True)
    is_anomaly = models.BooleanField(default=False, db_index=True)
    anomaly_summary = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-first_seen_at"]
        indexes = [
            models.Index(fields=["city", "district", "category"]),
            models.Index(fields=["district", "area_m2", "price_per_m2"]),
            models.Index(fields=["is_anomaly", "anomaly_score"]),
            models.Index(fields=["published_at", "status"]),
        ]

    def __str__(self):
        dist = f"منطقه {self.district}" if self.district else "تهران"
        area = f"{int(self.area_m2)}m²" if self.area_m2 else ""
        return f"{self.title[:45]} [{dist} - {area}]"

    def calculate_price_per_meter(self):
        """Calculate and update price_per_m2, rent_per_m2, and deposit_per_m2."""
        if self.area_m2 and self.area_m2 > 0:
            if self.price and self.price > 0:
                self.price_per_m2 = int(round(self.price / self.area_m2))
            if self.rent and self.rent > 0:
                self.rent_per_m2 = int(round(self.rent / self.area_m2))
            if self.deposit and self.deposit > 0:
                self.deposit_per_m2 = int(round(self.deposit / self.area_m2))


class ListingSnapshot(models.Model):
    """
    Historical observation snapshot for tracking price and attribute changes over time.
    """
    listing = models.ForeignKey(
        DivarListing,
        related_name="snapshots",
        on_delete=models.CASCADE,
        db_index=True
    )
    captured_at = models.DateTimeField(auto_now_add=True, db_index=True)
    price = models.BigIntegerField(null=True, blank=True)
    rent = models.BigIntegerField(null=True, blank=True)
    deposit = models.BigIntegerField(null=True, blank=True)
    area_m2 = models.FloatField(null=True, blank=True)
    price_per_m2 = models.BigIntegerField(null=True, blank=True)
    status = models.CharField(max_length=32, default="active")
    title = models.CharField(max_length=255, blank=True)
    raw_json = models.JSONField(default=dict)

    # Change tracking relative to previous snapshot
    price_change_absolute = models.BigIntegerField(default=0)
    price_change_percent = models.FloatField(default=0.0)
    price_per_m2_change = models.BigIntegerField(default=0)
    event_type = models.CharField(max_length=32, default=EVENT_INITIAL, db_index=True)

    class Meta:
        ordering = ["-captured_at"]
        indexes = [
            models.Index(fields=["listing", "captured_at"]),
            models.Index(fields=["event_type", "captured_at"]),
        ]

    def __str__(self):
        return f"Snapshot {self.listing.divar_token} @ {self.captured_at.strftime('%Y-%m-%d %H:%M')}: {self.event_type}"


class SearchPartitionExecution(models.Model):
    """
    Many-to-many link tracking which search partition executions discovered each listing.
    """
    partition = models.ForeignKey(
        SearchPartition,
        related_name="executions",
        on_delete=models.CASCADE,
        db_index=True
    )
    listing = models.ForeignKey(
        DivarListing,
        related_name="partition_executions",
        on_delete=models.CASCADE,
        db_index=True
    )
    executed_at = models.DateTimeField(auto_now_add=True)
    is_new_listing = models.BooleanField(default=False)

    class Meta:
        ordering = ["-executed_at"]
        unique_together = ("partition", "listing")
        indexes = [
            models.Index(fields=["partition", "executed_at"]),
        ]

    def __str__(self):
        return f"Partition {self.partition_id} -> Listing {self.listing.divar_token}"
