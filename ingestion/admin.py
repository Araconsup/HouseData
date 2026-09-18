"""
Admin interface for Search Partitions and Outbound Divar API Audit Logs.
"""

from django.contrib import admin
from ingestion.models import SearchPartition, ApiRequestLog
from ingestion.tasks import collect_partition


@admin.register(SearchPartition)
class SearchPartitionAdmin(admin.ModelAdmin):
    list_display = [
        "name", "district", "category", "min_area", "max_area",
        "active", "result_count", "unique_listings_count",
        "coverage_efficiency_display", "successful", "last_run"
    ]
    list_filter = ["district", "category", "active", "successful"]
    search_fields = ["name", "neighborhood"]
    actions = ["execute_selected_partitions", "activate_partitions", "deactivate_partitions"]

    @admin.display(description="Efficiency (%)")
    def coverage_efficiency_display(self, obj):
        return f"{obj.coverage_efficiency}%"

    @admin.action(description="Run selected search partitions immediately")
    def execute_selected_partitions(self, request, queryset):
        count = 0
        for partition in queryset.filter(active=True):
            collect_partition(partition.id)
            count += 1
        self.message_user(request, f"Triggered collection for {count} partitions.")

    @admin.action(description="Activate selected partitions")
    def activate_partitions(self, request, queryset):
        queryset.update(active=True)

    @admin.action(description="Deactivate selected partitions")
    def deactivate_partitions(self, request, queryset):
        queryset.update(active=False)


@admin.register(ApiRequestLog)
class ApiRequestLogAdmin(admin.ModelAdmin):
    list_display = [
        "request_time", "endpoint", "http_status",
        "response_time_ms", "number_of_results", "request_id"
    ]
    list_filter = ["http_status", "request_time"]
    search_fields = ["endpoint", "request_id", "error"]
    readonly_fields = [
        "request_time", "partition", "endpoint", "http_status",
        "response_time_ms", "number_of_results", "error", "request_id"
    ]
