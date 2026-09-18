"""
HOUSEDATA URL Configuration.
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from analytics.views import (
    AnomalyViewSet,
    dashboard_summary_view,
    district_statistics_view,
    tehran_statistics_view,
)
from ingestion.views import (
    SearchPartitionViewSet,
    api_request_logs_view,
    collection_status_view,
)
from listings.views import DivarListingViewSet

# DRF Router
router = DefaultRouter()
router.register(r"listings", DivarListingViewSet, basename="listing")
router.register(r"anomalies", AnomalyViewSet, basename="anomaly")
router.register(r"collection/partitions", SearchPartitionViewSet, basename="partition")

from django.conf import settings
from django.http import FileResponse, HttpResponse
from frontend.views import collection_admin_view

def service_worker_view(request):
    """Serve PWA service worker from root scope."""
    path = settings.BASE_DIR / "static/js/sw.js"
    response = FileResponse(open(path, "rb"), content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response

def manifest_view(request):
    """Serve PWA manifest."""
    path = settings.BASE_DIR / "static/manifest.json"
    response = FileResponse(open(path, "rb"), content_type="application/manifest+json")
    response["Cache-Control"] = "no-cache"
    return response

urlpatterns = [
    # PWA Endpoints
    path("sw.js", service_worker_view, name="service-worker"),
    path("manifest.json", manifest_view, name="pwa-manifest"),

    # Custom admin ingestion management panel
    path("admin/data-collection/", collection_admin_view, name="admin-data-collection"),
    path("admin/", admin.site.urls),

    # REST API endpoints
    path("api/", include(router.urls)),
    path("api/statistics/tehran/", tehran_statistics_view, name="api-tehran-stats"),
    path("api/statistics/districts/", district_statistics_view, name="api-district-stats"),
    path("api/statistics/dashboard-summary/", dashboard_summary_view, name="api-dashboard-summary"),
    path("api/collection/status/", collection_status_view, name="api-collection-status"),
    path("api/collection/logs/", api_request_logs_view, name="api-collection-logs"),

    # Frontend web application pages
    path("", include("frontend.urls")),
]
