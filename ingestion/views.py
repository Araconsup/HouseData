"""
Collection and Ingestion Management API Views.
"""

from django.utils import timezone as django_tz
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from ingestion.client import DivarApiClient
from ingestion.coverage import CoverageEngine
from ingestion.models import ApiRequestLog, SearchPartition
from ingestion.serializers import ApiRequestLogSerializer, SearchPartitionSerializer
from ingestion.tasks import collect_partition


class SearchPartitionViewSet(viewsets.ModelViewSet):
    """
    CRUD and execution trigger for Search Partitions.
    """
    queryset = SearchPartition.objects.all().order_by("district", "category", "min_area")
    serializer_class = SearchPartitionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "district", "city", "active", "successful"]
    search_fields = ["name", "neighborhood"]
    ordering_fields = ["district", "category", "last_run", "result_count", "unique_listings_count"]

    @action(detail=True, methods=["post"], url_path="run")
    def run_partition(self, request, pk=None):
        """Trigger execution of a specific partition."""
        partition = self.get_object()
        # In test/local environments, we can execute synchronously or via Celery
        use_celery = request.data.get("async", False)
        if use_celery:
            collect_partition.delay(partition.id)
            return Response({"status": "queued", "partition_id": partition.id})
        else:
            result = collect_partition(partition.id)
            return Response(result)

    @action(detail=False, methods=["post"], url_path="generate-standard")
    def generate_standard(self, request):
        """Generate systematic coverage partitions for all 22 Tehran districts."""
        created = CoverageEngine.generate_standard_partitions()
        return Response({
            "status": "success",
            "partitions_created": created,
            "total_partitions": SearchPartition.objects.count(),
        })


@api_view(["GET"])
def collection_status_view(request):
    """
    Overall data collection status, quota meter, and coverage matrix.
    """
    client = DivarApiClient()
    today_start = django_tz.now().replace(hour=0, minute=0, second=0, microsecond=0)
    requests_today = ApiRequestLog.objects.filter(request_time__gte=today_start).count()
    successful_requests = ApiRequestLog.objects.filter(
        request_time__gte=today_start, http_status=200
    ).count()
    failed_requests = requests_today - successful_requests

    last_log = ApiRequestLog.objects.first()
    matrix = CoverageEngine.get_coverage_matrix()

    return Response({
        "api": {
            "mode": "mock" if client.mock_mode else "official_kenar",
            "mock_mode": client.mock_mode,
            "daily_limit": client.daily_quota,
            "requests_used_today": requests_today,
            "requests_remaining": max(0, client.daily_quota - requests_today),
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "last_request_time": last_log.request_time if last_log else None,
        },
        "coverage_matrix": matrix,
    })


@api_view(["GET"])
def api_request_logs_view(request):
    """List recent outbound Divar API audit logs."""
    logs = ApiRequestLog.objects.all().order_by("-request_time")[:100]
    serializer = ApiRequestLogSerializer(logs, many=True)
    return Response(serializer.data)
