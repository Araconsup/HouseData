"""
Admin interface for Anomaly Detection Results and Market Statistics.
"""

from django.contrib import admin
from analytics.models import AnomalyResult, MarketStatistic
from core.normalizers import format_toman


@admin.register(AnomalyResult)
class AnomalyResultAdmin(admin.ModelAdmin):
    list_display = [
        "listing", "detector_name", "is_anomaly", "score",
        "confidence", "sample_size", "calculated_at"
    ]
    list_filter = ["detector_name", "is_anomaly", "confidence"]
    search_fields = ["listing__divar_token", "listing__title", "explanation"]
    readonly_fields = [
        "listing", "detector_name", "score", "is_anomaly",
        "explanation", "sample_size", "confidence", "metrics", "calculated_at"
    ]


@admin.register(MarketStatistic)
class MarketStatisticAdmin(admin.ModelAdmin):
    list_display = [
        "dimension", "dimension_value", "dimension_label_fa",
        "transaction_type", "listing_count", "median_sqm_display",
        "updated_at"
    ]
    list_filter = ["dimension", "transaction_type"]
    search_fields = ["dimension_value", "dimension_label_fa"]

    @admin.display(description="Median Price / m²")
    def median_sqm_display(self, obj):
        return format_toman(obj.median_price_per_m2, True)
