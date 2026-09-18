"""
Tests for Coverage Engine, Search Partition generation, and Visual Collection Matrix.
"""

import pytest
from ingestion.coverage import CoverageEngine
from ingestion.models import SearchPartition


@pytest.mark.django_db
def test_generate_standard_partitions():
    SearchPartition.objects.all().delete()
    initial_count = SearchPartition.objects.count()
    assert initial_count == 0

    created = CoverageEngine.generate_standard_partitions(districts=[1, 2], include_area_buckets=True)
    assert created > 0

    # Running again should prevent duplicate partitions
    second_run = CoverageEngine.generate_standard_partitions(districts=[1, 2], include_area_buckets=True)
    assert second_run == 0


@pytest.mark.django_db
def test_coverage_matrix():
    CoverageEngine.generate_standard_partitions(districts=[1, 2])
    matrix = CoverageEngine.get_coverage_matrix()

    assert "categories" in matrix
    assert "rows" in matrix
    assert len(matrix["rows"]) == 22

    # District 1 should have cells
    row1 = matrix["rows"][0]
    assert row1["district"] == 1
    assert "apartment-sale" in row1["cells"]
    cell = row1["cells"]["apartment-sale"]
    assert "total_partitions" in cell
    assert "status" in cell
