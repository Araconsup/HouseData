"""
Analytics models: Anomaly detection results and pre-calculated market statistics.
"""

from django.db import models
from core.constants import CONFIDENCE_CHOICES, CONFIDENCE_INSUFFICIENT
from listings.models import DivarListing


class AnomalyResult(models.Model):
    """
    Detailed anomaly detection results per listing and per detector method.
    """
    listing = models.ForeignKey(
        DivarListing,
        related_name="anomaly_results",
        on_delete=models.CASCADE,
        db_index=True
    )
    detector_name = models.CharField(
        max_length=64,
        db_index=True,
        help_text="iqr, robust_zscore, isolation_forest, comparable_deviation, ensemble"
    )
    score = models.FloatField(null=True, blank=True)
    is_anomaly = models.BooleanField(default=False, db_index=True)
    explanation = models.TextField(blank=True)
    sample_size = models.IntegerField(default=0)
    confidence = models.CharField(
        max_length=32,
        choices=CONFIDENCE_CHOICES,
        default=CONFIDENCE_INSUFFICIENT,
        db_index=True
    )
    metrics = models.JSONField(default=dict, help_text="Stored metrics (median, Q1, Q3, MAD, deviation %)")
    calculated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["-calculated_at"]
        indexes = [
            models.Index(fields=["listing", "detector_name"]),
            models.Index(fields=["is_anomaly", "confidence"]),
        ]

    def __str__(self):
        status = "ANOMALY" if self.is_anomaly else "NORMAL"
        return f"{self.listing.divar_token} [{self.detector_name}] -> {status} ({self.confidence})"


class MarketStatistic(models.Model):
    """
    Aggregated statistical summary for Tehran overall, districts, neighborhoods,
    property types, and area buckets.
    """
    dimension = models.CharField(
        max_length=32,
        db_index=True,
        help_text="tehran, district, neighborhood, property_type, area_range, age_range"
    )
    dimension_value = models.CharField(
        max_length=128,
        db_index=True,
        help_text="overall, district-1, saadat-abad, 50-70, etc."
    )
    dimension_label_fa = models.CharField(max_length=128, blank=True)
    transaction_type = models.CharField(
        max_length=16,
        default="sale",
        db_index=True,
        help_text="sale or rent"
    )

    listing_count = models.IntegerField(default=0)
    median_price = models.BigIntegerField(null=True, blank=True)
    mean_price = models.BigIntegerField(null=True, blank=True)
    median_price_per_m2 = models.BigIntegerField(null=True, blank=True)
    mean_price_per_m2 = models.BigIntegerField(null=True, blank=True)
    min_price_per_m2 = models.BigIntegerField(null=True, blank=True)
    max_price_per_m2 = models.BigIntegerField(null=True, blank=True)
    q1_price_per_m2 = models.BigIntegerField(null=True, blank=True)
    q3_price_per_m2 = models.BigIntegerField(null=True, blank=True)
    std_dev = models.FloatField(null=True, blank=True)
    mad = models.FloatField(null=True, blank=True)
    percentiles = models.JSONField(default=dict)

    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["dimension", "dimension_value"]
        unique_together = ("dimension", "dimension_value", "transaction_type")
        indexes = [
            models.Index(fields=["dimension", "transaction_type"]),
        ]

    def __str__(self):
        return f"Stat [{self.dimension}:{self.dimension_value}] ({self.transaction_type}) - {self.listing_count} listings"
