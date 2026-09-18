"""
URL routing for Frontend Web Application.
"""

from django.urls import path
from frontend import views

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("listings/", views.listings_view, name="listings"),
    path("listings/<str:token>/", views.listing_detail_view, name="listing-detail"),
    path("map/", views.map_view, name="map"),
    path("anomalies/", views.anomalies_view, name="anomalies"),
    path("statistics/", views.statistics_view, name="statistics"),
    path("collection/", views.collection_admin_view, name="collection"),
    path("admin/data-collection/", views.collection_admin_view, name="admin-data-collection"),
]
