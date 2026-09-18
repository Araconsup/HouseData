"""
Intelligent Coverage Engine.
Generates and manages search partitions across Tehran districts, categories,
and property size buckets to maximize unique listing coverage within Divar's
100-result search limit without pagination.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Count, Q, Sum
from core.constants import (
    AREA_BUCKETS,
    CATEGORY_APARTMENT_SALE,
    CATEGORY_HOUSE_VILLA_SALE,
    CATEGORY_LAND_SALE,
    CATEGORY_APARTMENT_RENT,
    SALE_CATEGORIES,
    RENT_CATEGORIES,
)
from core.tehran_data import TEHRAN_DISTRICTS
from ingestion.models import SearchPartition

logger = logging.getLogger(__name__)


class CoverageEngine:
    """
    Manages partition generation, execution tracking, and coverage matrix reporting.
    """

    @classmethod
    def generate_standard_partitions(
        cls,
        districts: Optional[List[int]] = None,
        categories: Optional[List[str]] = None,
        include_area_buckets: bool = True,
    ) -> int:
        """
        Generate systematic search partitions for Tehran districts and categories.
        Avoids duplicates if a partition with identical parameters already exists.
        Returns count of newly created partitions.
        """
        target_districts = districts or list(TEHRAN_DISTRICTS.keys())
        target_categories = categories or [
            CATEGORY_APARTMENT_SALE,
            CATEGORY_HOUSE_VILLA_SALE,
            CATEGORY_LAND_SALE,
            CATEGORY_APARTMENT_RENT,
        ]

        created_count = 0

        for dist in target_districts:
            dist_data = TEHRAN_DISTRICTS.get(dist, {})
            dist_name = dist_data.get("name_fa", f"منطقه {dist}")

            for cat in target_categories:
                cat_label = cat.replace("-", " ").title()

                if include_area_buckets and "apartment" in cat:
                    for bucket in AREA_BUCKETS:
                        name = f"{dist_name} - {cat_label} ({bucket['name']})"
                        _, created = SearchPartition.objects.get_or_create(
                            city="tehran",
                            district=dist,
                            category=cat,
                            min_area=bucket["min_area"],
                            max_area=bucket["max_area"],
                            defaults={
                                "name": name,
                                "active": True,
                            }
                        )
                        if created:
                            created_count += 1
                else:
                    # Broad category partition for whole district
                    name = f"{dist_name} - {cat_label}"
                    _, created = SearchPartition.objects.get_or_create(
                        city="tehran",
                        district=dist,
                        category=cat,
                        min_area=None,
                        max_area=None,
                        defaults={
                            "name": name,
                            "active": True,
                        }
                    )
                    if created:
                        created_count += 1

        logger.info(f"Generated {created_count} new search partitions")
        return created_count

    @classmethod
    def get_coverage_matrix(cls) -> Dict[str, Any]:
        """
        Build the visual collection matrix:
        Rows: Districts 1-22
        Columns: Supported Categories
        Cell: {
            partition_count,
            executed_count,
            unique_listings,
            status: 'covered' | 'partial' | 'pending' | 'failed'
        }
        """
        categories = [
            CATEGORY_APARTMENT_SALE,
            CATEGORY_HOUSE_VILLA_SALE,
            CATEGORY_LAND_SALE,
            CATEGORY_APARTMENT_RENT,
        ]

        # Fetch all partitions grouped by district and category
        partitions = SearchPartition.objects.filter(city="tehran")
        stats_map: Dict[Tuple[int, str], Dict] = {}

        for p in partitions:
            if not p.district:
                continue
            key = (p.district, p.category)
            if key not in stats_map:
                stats_map[key] = {
                    "total_partitions": 0,
                    "executed_partitions": 0,
                    "successful_executions": 0,
                    "results_count": 0,
                    "unique_count": 0,
                    "duplicate_count": 0,
                }
            stats_map[key]["total_partitions"] += 1
            if p.last_run:
                stats_map[key]["executed_partitions"] += 1
                if p.successful:
                    stats_map[key]["successful_executions"] += 1
                stats_map[key]["results_count"] += p.result_count
                stats_map[key]["unique_count"] += p.unique_listings_count
                stats_map[key]["duplicate_count"] += p.duplicate_listings_count

        matrix_rows = []
        for dist in range(1, 23):
            dist_info = TEHRAN_DISTRICTS.get(dist, {})
            row = {
                "district": dist,
                "district_name_fa": dist_info.get("name_fa", f"منطقه {dist}"),
                "district_name_en": dist_info.get("name_en", f"District {dist}"),
                "cells": {},
            }

            for cat in categories:
                key = (dist, cat)
                data = stats_map.get(key, {
                    "total_partitions": 0,
                    "executed_partitions": 0,
                    "successful_executions": 0,
                    "results_count": 0,
                    "unique_count": 0,
                    "duplicate_count": 0,
                })

                total = data["total_partitions"]
                executed = data["executed_partitions"]
                unique = data["unique_count"]

                if total == 0:
                    status = "not_configured"
                elif executed == 0:
                    status = "pending"
                elif executed == total and data["successful_executions"] == total:
                    status = "covered"
                elif data["successful_executions"] > 0:
                    status = "partial"
                else:
                    status = "failed"

                row["cells"][cat] = {
                    "total_partitions": total,
                    "executed_partitions": executed,
                    "results_count": data["results_count"],
                    "unique_count": unique,
                    "efficiency": round((unique / data["results_count"] * 100), 1) if data["results_count"] > 0 else 0,
                    "status": status,
                }

            matrix_rows.append(row)

        return {
            "categories": categories,
            "rows": matrix_rows,
            "total_partitions": partitions.count(),
            "active_partitions": partitions.filter(active=True).count(),
        }
