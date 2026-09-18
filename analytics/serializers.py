"""
Serializers for Anomaly Results and Market Statistics.
"""

from rest_framework import serializers
from analytics.models import AnomalyResult, MarketStatistic
from core.normalizers import format_toman
from listings.serializers import DivarListingListSerializer


class AnomalyResultSerializer(serializers.ModelSerializer):
    listing = DivarListingListSerializer(read_only=True)
    confidence_display = serializers.CharField(source="get_confidence_display", read_only=True)

    class Meta:
        model = AnomalyResult
        fields = [
            "id",
            "listing",
            "detector_name",
            "score",
            "is_anomaly",
            "explanation",
            "sample_size",
            "confidence",
            "confidence_display",
            "metrics",
            "calculated_at",
        ]


class MarketStatisticSerializer(serializers.ModelSerializer):
    median_price_formatted = serializers.SerializerMethodField()
    median_price_per_m2_formatted = serializers.SerializerMethodField()

    class Meta:
        model = MarketStatistic
        fields = [
            "id",
            "dimension",
            "dimension_value",
            "dimension_label_fa",
            "transaction_type",
            "listing_count",
            "median_price",
            "mean_price",
            "median_price_per_m2",
            "mean_price_per_m2",
            "min_price_per_m2",
            "max_price_per_m2",
            "q1_price_per_m2",
            "q3_price_per_m2",
            "std_dev",
            "mad",
            "percentiles",
            "median_price_formatted",
            "median_price_per_m2_formatted",
            "updated_at",
        ]

    def get_median_price_formatted(self, obj):
        return format_toman(obj.median_price, persian_digits=True)

    def get_median_price_per_m2_formatted(self, obj):
        return format_toman(obj.median_price_per_m2, persian_digits=True)
