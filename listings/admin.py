"""
Admin interface for Listings and Price History Snapshots.
"""

from django.contrib import admin
from listings.models import DivarListing, ListingSnapshot, SearchPartitionExecution


class ListingSnapshotInline(admin.TabularInline):
    model = ListingSnapshot
    extra = 0
    readonly_fields = [
        "captured_at", "price", "rent", "deposit", "price_per_m2",
        "price_change_percent", "event_type"
    ]
    can_delete = False


@admin.register(DivarListing)
class DivarListingAdmin(admin.ModelAdmin):
    list_display = [
        "divar_token", "title", "district", "neighborhood",
        "category", "price", "price_per_m2", "area_m2",
        "is_anomaly", "anomaly_score", "status", "first_seen_at"
    ]
    list_filter = ["category", "district", "is_anomaly", "status", "parking", "elevator"]
    search_fields = ["divar_token", "title", "neighborhood", "description"]
    readonly_fields = [
        "divar_token", "first_seen_at", "last_seen_at",
        "price_per_m2", "rent_per_m2", "deposit_per_m2",
        "is_anomaly", "anomaly_score", "anomaly_summary",
        "raw_json"
    ]
    inlines = [ListingSnapshotInline]


@admin.register(ListingSnapshot)
class ListingSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        "listing", "captured_at", "price", "price_per_m2",
        "event_type", "price_change_percent", "price_change_absolute"
    ]
    list_filter = ["event_type", "captured_at"]
    search_fields = ["listing__divar_token", "listing__title"]
    readonly_fields = ["captured_at", "raw_json"]


@admin.register(SearchPartitionExecution)
class SearchPartitionExecutionAdmin(admin.ModelAdmin):
    list_display = ["partition", "listing", "executed_at", "is_new_listing"]
    list_filter = ["is_new_listing", "executed_at"]
