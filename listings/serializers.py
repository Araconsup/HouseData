"""
Serializers for Listings, Snapshots, and History.
"""

from rest_framework import serializers
from core.normalizers import format_toman, to_persian_digits
from listings.models import DivarListing, ListingSnapshot


class ListingSnapshotSerializer(serializers.ModelSerializer):
    price_formatted = serializers.SerializerMethodField()
    price_per_m2_formatted = serializers.SerializerMethodField()

    class Meta:
        model = ListingSnapshot
        fields = [
            "id",
            "captured_at",
            "price",
            "rent",
            "deposit",
            "area_m2",
            "price_per_m2",
            "price_formatted",
            "price_per_m2_formatted",
            "status",
            "title",
            "price_change_absolute",
            "price_change_percent",
            "price_per_m2_change",
            "event_type",
        ]

    def get_price_formatted(self, obj):
        return format_toman(obj.price, persian_digits=True)

    def get_price_per_m2_formatted(self, obj):
        return format_toman(obj.price_per_m2, persian_digits=True)


class DivarListingListSerializer(serializers.ModelSerializer):
    price_formatted = serializers.SerializerMethodField()
    price_per_m2_formatted = serializers.SerializerMethodField()
    deposit_formatted = serializers.SerializerMethodField()
    rent_formatted = serializers.SerializerMethodField()

    class Meta:
        model = DivarListing
        fields = [
            "divar_token",
            "title",
            "category",
            "city",
            "district",
            "neighborhood",
            "latitude",
            "longitude",
            "price",
            "rent",
            "deposit",
            "area_m2",
            "price_per_m2",
            "price_formatted",
            "price_per_m2_formatted",
            "deposit_formatted",
            "rent_formatted",
            "rooms",
            "floor",
            "building_age",
            "parking",
            "elevator",
            "storage",
            "balcony",
            "published_at",
            "is_anomaly",
            "anomaly_score",
            "anomaly_summary",
            "status",
        ]

    def get_price_formatted(self, obj):
        return format_toman(obj.price, persian_digits=True)

    def get_price_per_m2_formatted(self, obj):
        return format_toman(obj.price_per_m2, persian_digits=True)

    def get_deposit_formatted(self, obj):
        return format_toman(obj.deposit, persian_digits=True)

    def get_rent_formatted(self, obj):
        return format_toman(obj.rent, persian_digits=True)


class DivarListingDetailSerializer(DivarListingListSerializer):
    snapshots = ListingSnapshotSerializer(many=True, read_only=True)

    class Meta(DivarListingListSerializer.Meta):
        fields = DivarListingListSerializer.Meta.fields + [
            "description",
            "address_text",
            "construction_type",
            "property_type",
            "seller_type",
            "first_seen_at",
            "last_seen_at",
            "source_url",
            "snapshots",
        ]
