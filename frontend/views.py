"""
Frontend Web Views for HOUSEDATA.
"""

from django.shortcuts import get_object_or_404, render
from analytics.comparables import ComparableService
from core.constants import CATEGORY_CHOICES, CONFIDENCE_CHOICES
from core.tehran_data import TEHRAN_DISTRICTS
from listings.models import DivarListing


def dashboard_view(request):
    """Main interactive Tehran real-estate dashboard."""
    return render(request, "frontend/dashboard.html", {
        "title": "داشبورد تحلیلی مسکن تهران | HOUSEDATA",
        "districts": TEHRAN_DISTRICTS,
        "categories": CATEGORY_CHOICES,
    })


def listings_view(request):
    """Filterable listings catalog."""
    return render(request, "frontend/listings.html", {
        "title": "کاوشگر املاک تهران | HOUSEDATA",
        "districts": TEHRAN_DISTRICTS,
        "categories": CATEGORY_CHOICES,
    })


def listing_detail_view(request, token):
    """Property details page with price history and comparable market analysis."""
    listing = get_object_or_404(DivarListing, divar_token=token)
    comparables, criteria = ComparableService.get_comparables(listing)
    metrics = ComparableService.calculate_comparable_metrics(listing, comparables)
    snapshots = listing.snapshots.all().order_by("captured_at")
    anomaly_results = listing.anomaly_results.all()

    return render(request, "frontend/listing_detail.html", {
        "title": f"{listing.title} | HOUSEDATA",
        "listing": listing,
        "comparables": comparables,
        "criteria": criteria,
        "metrics": metrics,
        "snapshots": snapshots,
        "anomaly_results": anomaly_results,
    })


def map_view(request):
    """Interactive Tehran real-estate map with heatmaps and clusters."""
    return render(request, "frontend/map.html", {
        "title": "نقشه تعاملی مسکن تهران | HOUSEDATA",
        "districts": TEHRAN_DISTRICTS,
        "categories": CATEGORY_CHOICES,
    })


def anomalies_view(request):
    """Dedicated outlier and anomaly explorer."""
    return render(request, "frontend/anomalies.html", {
        "title": "کاوشگر املاک نامتعارف آماری | HOUSEDATA",
        "districts": TEHRAN_DISTRICTS,
        "categories": CATEGORY_CHOICES,
        "confidence_choices": CONFIDENCE_CHOICES,
    })


def statistics_view(request):
    """Market statistics and district comparison benchmarks."""
    return render(request, "frontend/statistics.html", {
        "title": "شاخص‌های آماری بازار مسکن تهران | HOUSEDATA",
        "districts": TEHRAN_DISTRICTS,
    })


def collection_admin_view(request):
    """Ingestion management panel with visual collection matrix."""
    return render(request, "frontend/collection.html", {
        "title": "مدیریت جمع‌آوری داده و پوشش API | HOUSEDATA",
        "districts": TEHRAN_DISTRICTS,
        "categories": CATEGORY_CHOICES,
    })
