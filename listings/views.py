"""
REST API ViewSets for Listings, Historical Price Tracking, and Comparables.
"""

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

from analytics.comparables import ComparableService
from core.normalizers import format_toman
from listings.models import DivarListing, ListingSnapshot
from listings.serializers import (
    DivarListingDetailSerializer,
    DivarListingListSerializer,
    ListingSnapshotSerializer,
)


class StandardResultsPagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = "page_size"
    max_page_size = 100


class DivarListingFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    min_area = django_filters.NumberFilter(field_name="area_m2", lookup_expr="gte")
    max_area = django_filters.NumberFilter(field_name="area_m2", lookup_expr="lte")
    min_sqm = django_filters.NumberFilter(field_name="price_per_m2", lookup_expr="gte")
    max_sqm = django_filters.NumberFilter(field_name="price_per_m2", lookup_expr="lte")
    district = django_filters.NumberFilter(field_name="district")
    neighborhood = django_filters.CharFilter(field_name="neighborhood", lookup_expr="icontains")
    category = django_filters.CharFilter(field_name="category")
    rooms = django_filters.NumberFilter(field_name="rooms")
    parking = django_filters.BooleanFilter(field_name="parking")
    elevator = django_filters.BooleanFilter(field_name="elevator")
    storage = django_filters.BooleanFilter(field_name="storage")
    is_anomaly = django_filters.BooleanFilter(field_name="is_anomaly")

    class Meta:
        model = DivarListing
        fields = [
            "district", "neighborhood", "category", "rooms",
            "parking", "elevator", "storage", "is_anomaly",
            "status", "city",
        ]


class DivarListingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for searching and viewing Tehran listings.
    Lookup by divar_token.
    """
    queryset = DivarListing.objects.all().order_by("-first_seen_at")
    lookup_field = "divar_token"
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DivarListingFilter
    search_fields = ["title", "description", "neighborhood", "address_text"]
    ordering_fields = [
        "price", "price_per_m2", "area_m2", "published_at",
        "first_seen_at", "building_age", "anomaly_score",
    ]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return DivarListingDetailSerializer
        return DivarListingListSerializer

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, divar_token=None):
        """Get price and attribute history snapshots for a listing."""
        listing = self.get_object()
        snapshots = listing.snapshots.all().order_by("captured_at")
        serializer = ListingSnapshotSerializer(snapshots, many=True)
        return Response({
            "listing_token": listing.divar_token,
            "title": listing.title,
            "current_price": listing.price,
            "current_price_formatted": format_toman(listing.price, True),
            "snapshots_count": snapshots.count(),
            "snapshots": serializer.data,
        })

    @action(detail=True, methods=["get"], url_path="comparables")
    def comparables(self, request, divar_token=None):
        """
        Get local comparable properties and comparative metrics for a target property.
        """
        listing = self.get_object()
        comparables, criteria = ComparableService.get_comparables(listing)
        metrics = ComparableService.calculate_comparable_metrics(listing, comparables)

        serializer = DivarListingListSerializer(comparables, many=True)
        return Response({
            "target": DivarListingDetailSerializer(listing).data,
            "criteria_used": criteria,
            "metrics": {
                **metrics,
                "median_sqm_formatted": format_toman(metrics["median_sqm"], True) if metrics["median_sqm"] else None,
                "target_sqm_formatted": format_toman(listing.price_per_m2, True) if listing.price_per_m2 else None,
            },
            "comparables": serializer.data,
        })

    @action(detail=False, methods=["get"], url_path="map-points")
    def map_points(self, request):
        """
        High-performance endpoint returning geo coordinates and essential metrics
        for the Leaflet map and heatmap.
        """
        qs = self.filter_queryset(
            self.get_queryset().filter(latitude__isnull=False, longitude__isnull=False)
        )
        # Limit to 1,500 points for fluid browser rendering
        data = list(qs.values(
            "divar_token",
            "title",
            "latitude",
            "longitude",
            "price",
            "price_per_m2",
            "area_m2",
            "rooms",
            "district",
            "neighborhood",
            "is_anomaly",
            "anomaly_score",
            "category",
            "published_at",
        )[:1500])

        for item in data:
            item["price_formatted"] = format_toman(item["price"], True)
            item["price_per_m2_formatted"] = format_toman(item["price_per_m2"], True)

        return Response({
            "count": len(data),
            "points": data,
        })
