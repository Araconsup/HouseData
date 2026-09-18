"""
Analytics API views: Market Statistics, Anomaly Explorer, and Dashboard KPIs.
"""

from datetime import timedelta
import numpy as np
from django.db.models import Avg, Count, F, Q
from django.utils import timezone as django_tz
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

from analytics.models import AnomalyResult, MarketStatistic
from analytics.serializers import AnomalyResultSerializer, MarketStatisticSerializer
from core.constants import (
    AREA_BUCKETS,
    EVENT_PRICE_DECREASE,
    SALE_CATEGORIES,
    RENT_CATEGORIES,
)
from core.normalizers import format_toman
from core.tehran_data import TEHRAN_DISTRICTS
from listings.models import DivarListing, ListingSnapshot


class AnomalyFilter(django_filters.FilterSet):
    district = django_filters.NumberFilter(field_name="listing__district")
    neighborhood = django_filters.CharFilter(field_name="listing__neighborhood", lookup_expr="icontains")
    category = django_filters.CharFilter(field_name="listing__category")
    detector_name = django_filters.CharFilter(field_name="detector_name")
    confidence = django_filters.CharFilter(field_name="confidence")
    min_score = django_filters.NumberFilter(field_name="score", lookup_expr="gte")
    max_score = django_filters.NumberFilter(field_name="score", lookup_expr="lte")

    class Meta:
        model = AnomalyResult
        fields = ["detector_name", "confidence", "is_anomaly"]


class AnomalyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for exploring detected real-estate statistical anomalies.
    """
    queryset = AnomalyResult.objects.filter(is_anomaly=True).select_related("listing").order_by("-calculated_at")
    serializer_class = AnomalyResultSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = AnomalyFilter
    ordering_fields = ["score", "sample_size", "calculated_at"]
    ordering = ["-calculated_at"]


@api_view(["GET"])
def tehran_statistics_view(request):
    """Overall Tehran statistics for sale and rent."""
    stats = MarketStatistic.objects.filter(dimension="tehran", dimension_value="overall")
    serializer = MarketStatisticSerializer(stats, many=True)
    return Response({
        "tehran": serializer.data
    })


@api_view(["GET"])
def district_statistics_view(request):
    """Breakdown of statistics across Tehran municipal districts 1-22."""
    tx_type = request.query_params.get("type", "sale")
    stats = MarketStatistic.objects.filter(dimension="district", transaction_type=tx_type).order_by("dimension_value")
    serializer = MarketStatisticSerializer(stats, many=True)
    return Response({
        "transaction_type": tx_type,
        "districts": serializer.data
    })


@api_view(["GET"])
def dashboard_summary_view(request):
    """
    Aggregated KPIs and Chart series for the main interactive dashboard.
    """
    now = django_tz.now()
    seven_days_ago = now - timedelta(days=7)

    # 1. Total counts
    total_listings = DivarListing.objects.count()
    active_listings = DivarListing.objects.filter(status="active").count()
    new_this_week = DivarListing.objects.filter(first_seen_at__gte=seven_days_ago).count()
    price_reductions = ListingSnapshot.objects.filter(event_type=EVENT_PRICE_DECREASE).count()
    anomalies_count = DivarListing.objects.filter(is_anomaly=True, status="active").count()

    # 2. Tehran Sale Median Metrics
    tehran_sale_stat = MarketStatistic.objects.filter(
        dimension="tehran",
        dimension_value="overall",
        transaction_type="sale"
    ).first()

    median_sqm = tehran_sale_stat.median_price_per_m2 if tehran_sale_stat else None
    median_total = tehran_sale_stat.median_price if tehran_sale_stat else None

    # Fallback to direct calculation if stat cache empty
    if median_sqm is None:
        sqms = list(DivarListing.objects.filter(
            category__in=SALE_CATEGORIES,
            status="active",
            price_per_m2__isnull=False
        ).values_list("price_per_m2", flat=True)[:500])
        if sqms:
            median_sqm = int(np.median(sqms))
            totals = list(DivarListing.objects.filter(
                category__in=SALE_CATEGORIES,
                status="active",
                price__isnull=False
            ).values_list("price", flat=True)[:500])
            median_total = int(np.median(totals)) if totals else None

    # 3. District Comparison Chart Data
    district_data = []
    for dist in range(1, 23):
        stat = MarketStatistic.objects.filter(
            dimension="district",
            dimension_value=f"district-{dist}",
            transaction_type="sale"
        ).first()
        dist_info = TEHRAN_DISTRICTS.get(dist, {})
        label = dist_info.get("name_fa", f"منطقه {dist}")

        if stat and stat.listing_count > 0:
            district_data.append({
                "district": dist,
                "label": label,
                "median_price_per_m2": stat.median_price_per_m2,
                "listing_count": stat.listing_count,
            })
        else:
            # Calculate ad-hoc if cache hasn't run
            d_sqms = list(DivarListing.objects.filter(
                district=dist,
                category__in=SALE_CATEGORIES,
                price_per_m2__isnull=False
            ).values_list("price_per_m2", flat=True))
            if d_sqms:
                district_data.append({
                    "district": dist,
                    "label": label,
                    "median_price_per_m2": int(np.median(d_sqms)),
                    "listing_count": len(d_sqms),
                })

    # Sort district data by district number
    district_data.sort(key=lambda x: x["district"])

    # 4. Price/m² Distribution Buckets
    distribution_buckets = []
    all_sqms = list(DivarListing.objects.filter(
        category__in=SALE_CATEGORIES,
        status="active",
        price_per_m2__isnull=False
    ).values_list("price_per_m2", flat=True)[:2000])

    if all_sqms:
        ranges = [
            (0, 50_000_000, "زیر ۵۰ میلیون"),
            (50_000_000, 80_000_000, "۵۰ تا ۸۰ میلیون"),
            (80_000_000, 120_000_000, "۸۰ تا ۱۲۰ میلیون"),
            (120_000_000, 160_000_000, "۱۲۰ تا ۱۶۰ میلیون"),
            (160_000_000, 220_000_000, "۱۶۰ تا ۲۲۰ میلیون"),
            (220_000_000, 300_000_000, "۲۲۰ تا ۳۰۰ میلیون"),
            (300_000_000, 1_000_000_000, "بالای ۳۰۰ میلیون"),
        ]
        arr = np.array(all_sqms)
        for low, high, label in ranges:
            count = int(np.sum((arr >= low) & (arr < high)))
            distribution_buckets.append({
                "label": label,
                "count": count,
            })

    # 5. Area vs Price Scatter Points sample
    scatter_points = list(DivarListing.objects.filter(
        category__in=SALE_CATEGORIES,
        area_m2__isnull=False,
        price__isnull=False,
        status="active"
    ).values("area_m2", "price", "district", "is_anomaly")[:150])

    # 6. Building Age vs Price/m²
    age_analysis = []
    for age_bracket in [(0, 2, "نوساز (۰-۲)"), (3, 7, "۳ تا ۷ سال"), (8, 15, "۸ تا ۱۵ سال"), (16, 30, "۱۶+ سال")]:
        low, high, label = age_bracket
        sub_sqms = list(DivarListing.objects.filter(
            category__in=SALE_CATEGORIES,
            building_age__gte=low,
            building_age__lte=high,
            price_per_m2__isnull=False
        ).values_list("price_per_m2", flat=True))
        if sub_sqms:
            age_analysis.append({
                "label": label,
                "median_sqm": int(np.median(sub_sqms)),
                "count": len(sub_sqms),
            })

    return Response({
        "kpis": {
            "total_listings_collected": total_listings,
            "active_listings": active_listings,
            "new_listings_week": new_this_week,
            "price_reductions_count": price_reductions,
            "anomalies_count": anomalies_count,
            "median_price_per_m2": median_sqm,
            "median_price_per_m2_formatted": format_toman(median_sqm, True) if median_sqm else "—",
            "median_total_price": median_total,
            "median_total_price_formatted": format_toman(median_total, True) if median_total else "—",
        },
        "charts": {
            "districts": district_data,
            "distribution": distribution_buckets,
            "scatter": scatter_points,
            "building_age": age_analysis,
        }
    })
