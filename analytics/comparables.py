"""
Comparable Property Engine.
Finds statistically and geographically comparable properties for a target listing
and computes local market benchmarks without mixing sale and rental data.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from django.db.models import Q
from core.constants import SALE_CATEGORIES, RENT_CATEGORIES
from listings.models import DivarListing


# Tehran District Socio-Economic Price Tiers
DISTRICT_TIERS = {
    1: [1, 2, 3],       # High-end Shemiran / Northern Tehran
    2: [1, 2, 3],
    3: [1, 2, 3],
    5: [5, 6, 7, 22],   # Upper-mid Western & Central Tehran
    6: [5, 6, 7],
    7: [5, 6, 7, 8],
    4: [4, 8],          # Eastern Tehran
    8: [4, 8],
    22: [5, 21, 22],
    9: [9, 10, 11, 12, 13, 14],   # Mid & Central/South-West
    10: [9, 10, 11, 12],
    11: [9, 10, 11, 12],
    12: [11, 12, 13, 14],
    13: [8, 13, 14],
    14: [13, 14, 15],
    15: [15, 16, 17, 18, 19, 20], # Southern Tehran
    16: [15, 16, 17, 18, 19, 20],
    17: [15, 16, 17, 18, 19, 20],
    18: [15, 16, 17, 18, 19, 20],
    19: [15, 16, 17, 18, 19, 20],
    20: [15, 16, 17, 18, 19, 20],
    21: [21, 22, 5],
}


class ComparableService:
    """
    Finds comparable listings for valuation and anomaly detection.
    """

    @classmethod
    def get_comparables(
        cls,
        target: DivarListing,
        max_results: int = 60,
    ) -> Tuple[List[DivarListing], List[str]]:
        """
        Finds comparable listings for the target property.
        Returns:
            (comparables_list, criteria_descriptions)
        """
        criteria_used = []

        # 1. Strictly separate Sale vs Rent - never mix!
        is_rent = target.category in RENT_CATEGORIES
        if is_rent:
            base_qs = DivarListing.objects.filter(
                category__in=RENT_CATEGORIES,
                status="active",
                city="tehran"
            ).exclude(id=target.id)
            criteria_used.append("نوع معامله: رهن و اجاره")
        else:
            base_qs = DivarListing.objects.filter(
                category__in=SALE_CATEGORIES,
                status="active",
                city="tehran",
                price_per_m2__isnull=False
            ).exclude(id=target.id)
            criteria_used.append("نوع معامله: خرید و فروش")

        target_area = target.area_m2 or 80.0

        # Step A: Local Neighborhood search with tight bounds (+/- 20% area)
        min_a = max(15.0, target_area * 0.80)
        max_a = target_area * 1.20

        if target.neighborhood:
            nh_qs = base_qs.filter(
                neighborhood=target.neighborhood,
                area_m2__gte=min_a,
                area_m2__lte=max_a,
            )
            if target.rooms is not None:
                nh_qs = nh_qs.filter(rooms__gte=max(0, target.rooms - 1), rooms__lte=target.rooms + 1)

            if nh_qs.count() >= 15:
                criteria_used.append(f"محله: {target.neighborhood}")
                criteria_used.append(f"متراژ: {int(min_a)} تا {int(max_a)} مترمربع")
                return list(nh_qs[:max_results]), criteria_used

        # Step B: Municipal District search with area (+/- 25%)
        if target.district:
            min_a2 = max(15.0, target_area * 0.75)
            max_a2 = target_area * 1.25
            dist_qs = base_qs.filter(
                district=target.district,
                area_m2__gte=min_a2,
                area_m2__lte=max_a2,
            )
            if dist_qs.count() >= 15:
                criteria_used.append(f"منطقه شهرداری: {target.district}")
                criteria_used.append(f"متراژ: {int(min_a2)} تا {int(max_a2)} مترمربع")
                return list(dist_qs[:max_results]), criteria_used

            # Step C: Broader District Tier (socio-economically comparable districts)
            tier_districts = DISTRICT_TIERS.get(target.district, [target.district])
            tier_qs = base_qs.filter(
                district__in=tier_districts,
                area_m2__gte=min_a2,
                area_m2__lte=max_a2,
            )
            if tier_qs.count() >= 15:
                criteria_used.append(f"مناطق همگن اقتصادی (مناطق {', '.join(str(d) for d in tier_districts)})")
                criteria_used.append(f"متراژ: {int(min_a2)} تا {int(max_a2)} مترمربع")
                return list(tier_qs[:max_results]), criteria_used

            # If still < 15, return whatever matched in the district (will be marked Insufficient Data)
            criteria_used.append(f"منطقه {target.district} (تعداد نمونه ناکافی)")
            return list(dist_qs[:max_results]), criteria_used

        # Fallback
        criteria_used.append("محدوده عمومی تهران")
        return list(base_qs.filter(area_m2__gte=min_a, area_m2__lte=max_a)[:max_results]), criteria_used

    @classmethod
    def calculate_comparable_metrics(
        cls,
        target: DivarListing,
        comparables: List[DivarListing],
    ) -> Dict[str, Any]:
        """
        Calculates median, Q1, Q3, min, max price per m², and percentage deviation.
        """
        sqm_values = [c.price_per_m2 for c in comparables if c.price_per_m2 and c.price_per_m2 > 0]
        if not sqm_values:
            return {
                "sample_size": 0,
                "median_sqm": None,
                "mean_sqm": None,
                "q1_sqm": None,
                "q3_sqm": None,
                "min_sqm": None,
                "max_sqm": None,
                "deviation_percent": None,
            }

        arr = np.array(sqm_values, dtype=float)
        median_sqm = float(np.median(arr))
        mean_sqm = float(np.mean(arr))
        q1_sqm = float(np.percentile(arr, 25))
        q3_sqm = float(np.percentile(arr, 75))
        min_sqm = float(np.min(arr))
        max_sqm = float(np.max(arr))

        target_sqm = target.price_per_m2
        dev_pct = None
        if target_sqm and median_sqm > 0:
            dev_pct = round(((target_sqm - median_sqm) / median_sqm) * 100.0, 2)

        return {
            "sample_size": len(arr),
            "median_sqm": int(median_sqm),
            "mean_sqm": int(mean_sqm),
            "q1_sqm": int(q1_sqm),
            "q3_sqm": int(q3_sqm),
            "min_sqm": int(min_sqm),
            "max_sqm": int(max_sqm),
            "deviation_percent": dev_pct,
        }
