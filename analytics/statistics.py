"""
Market Statistics Aggregator.
Computes robust statistics (median, IQR, MAD, percentiles) for Tehran overall,
districts 1-22, neighborhoods, categories, and area buckets.
"""

import logging
from typing import Dict, List, Optional
import numpy as np
from django.db.models import Avg, Count, Max, Min, Q

from core.constants import AREA_BUCKETS, SALE_CATEGORIES, RENT_CATEGORIES
from core.tehran_data import TEHRAN_DISTRICTS
from listings.models import DivarListing
from analytics.models import MarketStatistic

logger = logging.getLogger(__name__)


class MarketStatisticsService:
    """
    Computes and caches comprehensive real-estate market statistics.
    """

    @classmethod
    def compute_all_statistics(cls) -> int:
        """
        Recomputes statistics across all dimensions and updates MarketStatistic rows.
        Returns total number of statistics updated.
        """
        updated_count = 0

        # Separate sale and rental
        for tx_type in ["sale", "rent"]:
            categories = SALE_CATEGORIES if tx_type == "sale" else RENT_CATEGORIES

            # 1. Tehran Overall
            overall_qs = DivarListing.objects.filter(
                city="tehran",
                category__in=categories,
                status="active"
            )
            cls._calculate_and_save_stat(
                dimension="tehran",
                dimension_value="overall",
                label_fa="کل شهر تهران",
                tx_type=tx_type,
                qs=overall_qs,
            )
            updated_count += 1

            # 2. Districts 1-22
            for dist in range(1, 23):
                dist_info = TEHRAN_DISTRICTS.get(dist, {})
                dist_label = dist_info.get("name_fa", f"منطقه {dist}")
                dist_qs = overall_qs.filter(district=dist)
                cls._calculate_and_save_stat(
                    dimension="district",
                    dimension_value=f"district-{dist}",
                    label_fa=dist_label,
                    tx_type=tx_type,
                    qs=dist_qs,
                )
                updated_count += 1

            # 3. Area Buckets
            for bucket in AREA_BUCKETS:
                bucket_qs = overall_qs
                if bucket["min_area"] is not None:
                    bucket_qs = bucket_qs.filter(area_m2__gte=bucket["min_area"])
                if bucket["max_area"] is not None:
                    bucket_qs = bucket_qs.filter(area_m2__lte=bucket["max_area"])

                cls._calculate_and_save_stat(
                    dimension="area_range",
                    dimension_value=bucket["slug"],
                    label_fa=f"متراژ {bucket['name']}",
                    tx_type=tx_type,
                    qs=bucket_qs,
                )
                updated_count += 1

            # 4. Property Categories
            for cat in categories:
                cat_qs = overall_qs.filter(category=cat)
                cls._calculate_and_save_stat(
                    dimension="property_type",
                    dimension_value=cat,
                    label_fa=cat.replace("-", " ").title(),
                    tx_type=tx_type,
                    qs=cat_qs,
                )
                updated_count += 1

        logger.info(f"Successfully computed {updated_count} market statistic records")
        return updated_count

    @classmethod
    def _calculate_and_save_stat(
        cls,
        dimension: str,
        dimension_value: str,
        label_fa: str,
        tx_type: str,
        qs,
    ):
        """Helper to compute robust summary statistics on a QuerySet and save to DB."""
        count = qs.count()
        if count == 0:
            MarketStatistic.objects.update_or_create(
                dimension=dimension,
                dimension_value=dimension_value,
                transaction_type=tx_type,
                defaults={
                    "dimension_label_fa": label_fa,
                    "listing_count": 0,
                    "median_price": None,
                    "mean_price": None,
                    "median_price_per_m2": None,
                    "mean_price_per_m2": None,
                    "min_price_per_m2": None,
                    "max_price_per_m2": None,
                    "q1_price_per_m2": None,
                    "q3_price_per_m2": None,
                    "std_dev": None,
                    "mad": None,
                    "percentiles": {},
                }
            )
            return

        # Fetch price values for numeric analysis
        price_field = "price" if tx_type == "sale" else "deposit"
        sqm_field = "price_per_m2" if tx_type == "sale" else "deposit_per_m2"

        prices = list(qs.filter(**{f"{price_field}__isnull": False}).values_list(price_field, flat=True))
        sqm_prices = list(qs.filter(**{f"{sqm_field}__isnull": False}).values_list(sqm_field, flat=True))

        median_price = int(np.median(prices)) if prices else None
        mean_price = int(np.mean(prices)) if prices else None

        if sqm_prices:
            arr_sqm = np.array(sqm_prices, dtype=float)
            median_sqm = int(np.median(arr_sqm))
            mean_sqm = int(np.mean(arr_sqm))
            min_sqm = int(np.min(arr_sqm))
            max_sqm = int(np.max(arr_sqm))
            q1_sqm = int(np.percentile(arr_sqm, 25))
            q3_sqm = int(np.percentile(arr_sqm, 75))
            std_dev = float(np.std(arr_sqm))

            # MAD: median absolute deviation
            mad = float(np.median(np.abs(arr_sqm - median_sqm)))

            percentiles = {
                "p10": int(np.percentile(arr_sqm, 10)),
                "p25": q1_sqm,
                "p50": median_sqm,
                "p75": q3_sqm,
                "p90": int(np.percentile(arr_sqm, 90)),
            }
        else:
            median_sqm = mean_sqm = min_sqm = max_sqm = q1_sqm = q3_sqm = None
            std_dev = mad = None
            percentiles = {}

        MarketStatistic.objects.update_or_create(
            dimension=dimension,
            dimension_value=dimension_value,
            transaction_type=tx_type,
            defaults={
                "dimension_label_fa": label_fa,
                "listing_count": count,
                "median_price": median_price,
                "mean_price": mean_price,
                "median_price_per_m2": median_sqm,
                "mean_price_per_m2": mean_sqm,
                "min_price_per_m2": min_sqm,
                "max_price_per_m2": max_sqm,
                "q1_price_per_m2": q1_sqm,
                "q3_price_per_m2": q3_sqm,
                "std_dev": round(std_dev, 2) if std_dev is not None else None,
                "mad": round(mad, 2) if mad is not None else None,
                "percentiles": percentiles,
            }
        )
