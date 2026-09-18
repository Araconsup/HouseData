"""
Serializers for Ingestion and Search Partition Management.
"""

from rest_framework import serializers
from ingestion.models import SearchPartition, ApiRequestLog


class SearchPartitionSerializer(serializers.ModelSerializer):
    coverage_efficiency = serializers.FloatField(read_only=True)

    class Meta:
        model = SearchPartition
        fields = [
            "id",
            "name",
            "category",
            "city",
            "district",
            "neighborhood",
            "min_area",
            "max_area",
            "min_price",
            "max_price",
            "min_rooms",
            "max_rooms",
            "only_with_parking",
            "only_with_elevator",
            "active",
            "last_run",
            "result_count",
            "unique_listings_count",
            "duplicate_listings_count",
            "coverage_efficiency",
            "successful",
            "error_message",
            "created_at",
            "updated_at",
        ]


class ApiRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiRequestLog
        fields = [
            "id",
            "request_time",
            "endpoint",
            "http_status",
            "response_time_ms",
            "number_of_results",
            "error",
            "request_id",
        ]
