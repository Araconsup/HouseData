"""
Data Science Anomaly Detection Engine for Tehran Real Estate.
Implements IQR, Robust Z-score (MAD), Isolation Forest, Local Comparable Deviation,
and an Ensemble Detector with statistical confidence estimation.
"""

import abc
import logging
from typing import Any, Dict, List, Optional

import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

from core.constants import (
    CONFIDENCE_INSUFFICIENT,
    CONFIDENCE_MODERATE,
    CONFIDENCE_STRONG,
    CONFIDENCE_WEAK,
    MIN_COMPARABLE_SAMPLE_SIZE,
)
from core.normalizers import format_toman
from listings.models import DivarListing

logger = logging.getLogger(__name__)


class BaseAnomalyDetector(abc.ABC):
    """Abstract base class for modular anomaly detectors."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    def detect(self, target: DivarListing, comparables: List[DivarListing]) -> Dict[str, Any]:
        """
        Run anomaly detection on the target listing relative to comparables.
        Returns dict with:
        - is_anomaly: bool
        - score: float
        - explanation: str
        - metrics: dict
        """
        pass


class IQRDetector(BaseAnomalyDetector):
    """
    Method 1: Interquartile Range (IQR) on price per square meter.
    Identifies values falling outside [Q1 - 1.5 * IQR, Q3 + 1.5 * IQR].
    """

    @property
    def name(self) -> str:
        return "iqr"

    def detect(self, target: DivarListing, comparables: List[DivarListing]) -> Dict[str, Any]:
        target_val = target.price_per_m2
        if not target_val or len(comparables) < 4:
            return {
                "is_anomaly": False,
                "score": 0.0,
                "explanation": "Insufficient sample for IQR calculation",
                "metrics": {},
            }

        sqm_values = np.array([c.price_per_m2 for c in comparables if c.price_per_m2 and c.price_per_m2 > 0])
        if len(sqm_values) < 4:
            return {"is_anomaly": False, "score": 0.0, "explanation": "Insufficient valid price/m² values", "metrics": {}}

        q1 = float(np.percentile(sqm_values, 25))
        q3 = float(np.percentile(sqm_values, 75))
        iqr = q3 - q1
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        is_low = target_val < lower_bound
        is_high = target_val > upper_bound
        is_anomaly = bool(is_low or is_high)

        # Normalized IQR distance score
        score = float((target_val - np.median(sqm_values)) / (iqr if iqr > 0 else 1.0))

        if is_low:
            exp = f"IQR: Unusually low price/m² ({format_toman(target_val)} vs lower bound {format_toman(lower_bound)})"
        elif is_high:
            exp = f"IQR: Unusually high price/m² ({format_toman(target_val)} vs upper bound {format_toman(upper_bound)})"
        else:
            exp = "IQR: Within expected range [Q1-1.5*IQR, Q3+1.5*IQR]"

        return {
            "is_anomaly": is_anomaly,
            "score": round(score, 3),
            "explanation": exp,
            "metrics": {
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "target_sqm": target_val,
            },
        }


class RobustZScoreDetector(BaseAnomalyDetector):
    """
    Method 2: Robust Z-score using Median and Median Absolute Deviation (MAD).
    More resilient against real-estate price skewness and extreme observations than mean/std.
    Formula: 0.6745 * (x - median) / MAD
    """

    @property
    def name(self) -> str:
        return "robust_zscore"

    def detect(self, target: DivarListing, comparables: List[DivarListing]) -> Dict[str, Any]:
        target_val = target.price_per_m2
        if not target_val or len(comparables) < 4:
            return {"is_anomaly": False, "score": 0.0, "explanation": "Insufficient sample for MAD calculation", "metrics": {}}

        sqm_values = np.array([c.price_per_m2 for c in comparables if c.price_per_m2 and c.price_per_m2 > 0], dtype=float)
        if len(sqm_values) < 4:
            return {"is_anomaly": False, "score": 0.0, "explanation": "Insufficient valid price/m² values", "metrics": {}}

        med = float(np.median(sqm_values))
        abs_deviations = np.abs(sqm_values - med)
        mad = float(np.median(abs_deviations))

        if mad == 0.0:
            # Handle degenerate case where > 50% values are identical
            mad = float(np.mean(abs_deviations)) or 1.0

        robust_z = 0.6745 * (target_val - med) / mad
        # Threshold of |z| >= 2.5 identifies ~1% statistical tail
        is_anomaly = abs(robust_z) >= 2.5

        if robust_z <= -2.5:
            exp = f"Robust Z-score ({robust_z:.2f}): Unusually low relative to median"
        elif robust_z >= 2.5:
            exp = f"Robust Z-score ({robust_z:.2f}): Unusually high relative to median"
        else:
            exp = f"Robust Z-score ({robust_z:.2f}): Normal statistical variation"

        return {
            "is_anomaly": is_anomaly,
            "score": round(float(robust_z), 3),
            "explanation": exp,
            "metrics": {
                "median": med,
                "mad": mad,
                "robust_z": round(float(robust_z), 3),
                "target_sqm": target_val,
            },
        }


class IsolationForestDetector(BaseAnomalyDetector):
    """
    Method 3: Multi-dimensional anomaly detection using scikit-learn IsolationForest.
    Analyzes combinations of price/m², area, rooms, age, floor, and amenities.
    """

    @property
    def name(self) -> str:
        return "isolation_forest"

    def detect(self, target: DivarListing, comparables: List[DivarListing]) -> Dict[str, Any]:
        if len(comparables) < 10:
            return {"is_anomaly": False, "score": 0.0, "explanation": "Isolation Forest requires >= 10 samples", "metrics": {}}

        def extract_features(item: DivarListing) -> List[float]:
            return [
                float(item.price_per_m2 or 0),
                float(item.area_m2 or 0),
                float(item.rooms or 2),
                float(item.building_age or 5),
                float(item.floor or 2),
                1.0 if item.parking else 0.0,
                1.0 if item.elevator else 0.0,
                1.0 if item.storage else 0.0,
            ]

        X_pool = [extract_features(c) for c in comparables]
        X_target = [extract_features(target)]

        all_X = np.array(X_pool + X_target, dtype=float)

        try:
            scaler = RobustScaler()
            X_scaled = scaler.fit_transform(all_X)

            clf = IsolationForest(contamination=0.08, random_state=42)
            clf.fit(X_scaled[:-1])

            # decision_function returns anomaly score (negative = outlier)
            raw_score = float(clf.decision_function(X_scaled[-1:])[0])
            pred = clf.predict(X_scaled[-1:])[0]  # -1 = anomaly, 1 = normal

            is_anomaly = bool(pred == -1)
            exp = "Isolation Forest: Multidimensional anomaly detected" if is_anomaly else "Isolation Forest: Normal feature combination"

            return {
                "is_anomaly": is_anomaly,
                "score": round(raw_score, 4),
                "explanation": exp,
                "metrics": {"decision_score": round(raw_score, 4)},
            }
        except Exception as e:
            logger.error(f"Isolation Forest error: {e}")
            return {"is_anomaly": False, "score": 0.0, "explanation": f"Model error: {e}", "metrics": {}}


class ComparableDeviationDetector(BaseAnomalyDetector):
    """
    Method 4: Local Comparable Median Deviation.
    Directly measures percentage difference between target price/m² and local median.
    """

    @property
    def name(self) -> str:
        return "comparable_deviation"

    def detect(self, target: DivarListing, comparables: List[DivarListing]) -> Dict[str, Any]:
        target_val = target.price_per_m2
        if not target_val or not comparables:
            return {"is_anomaly": False, "score": 0.0, "explanation": "No comparable properties found", "metrics": {}}

        sqm_values = [c.price_per_m2 for c in comparables if c.price_per_m2 and c.price_per_m2 > 0]
        if not sqm_values:
            return {"is_anomaly": False, "score": 0.0, "explanation": "No valid comparable price/m² values", "metrics": {}}

        med = float(np.median(sqm_values))
        diff_pct = ((target_val - med) / med) * 100.0

        # Substantial deviation threshold (e.g. 25% or more deviation from local median)
        is_anomaly = abs(diff_pct) >= 25.0

        direction = "below" if diff_pct < 0 else "above"
        exp = f"Local Comparable Model: {abs(diff_pct):.1f}% {direction} median ({format_toman(med)}/m²)"

        return {
            "is_anomaly": is_anomaly,
            "score": round(diff_pct, 2),
            "explanation": exp,
            "metrics": {
                "comparable_median_sqm": med,
                "target_sqm": target_val,
                "difference_percent": round(diff_pct, 2),
                "comparable_count": len(sqm_values),
            },
        }


class EnsembleAnomalyDetector:
    """
    Combines signals from IQR, Robust Z-score, Isolation Forest, and Local Comparable Deviation.
    Enforces minimum sample sizes to prevent false alarms on small samples.
    """

    def __init__(self, min_samples: int = MIN_COMPARABLE_SAMPLE_SIZE):
        self.min_samples = min_samples
        self.iqr_detector = IQRDetector()
        self.robust_z_detector = RobustZScoreDetector()
        self.iforest_detector = IsolationForestDetector()
        self.deviation_detector = ComparableDeviationDetector()

    def evaluate(self, target: DivarListing, comparables: List[DivarListing]) -> Dict[str, Any]:
        """
        Runs all detectors and synthesizes an ensemble decision.
        Returns full detailed breakdown.
        """
        sample_size = len(comparables)

        # Insufficient sample guard
        if sample_size < self.min_samples:
            return {
                "is_anomaly": False,
                "score": None,
                "confidence": CONFIDENCE_INSUFFICIENT,
                "sample_size": sample_size,
                "explanation": (
                    f"Insufficient comparable data ({sample_size} < {self.min_samples} required) "
                    "to reliably evaluate statistical anomaly."
                ),
                "summary": "داده‌های مقایسه‌ای کافی برای ارزیابی آماری موجود نیست.",
                "signals": {},
                "metrics": {
                    "sample_size": sample_size,
                    "target_sqm": target.price_per_m2,
                },
            }

        # Run each detector
        r_iqr = self.iqr_detector.detect(target, comparables)
        r_z = self.robust_z_detector.detect(target, comparables)
        r_iforest = self.iforest_detector.detect(target, comparables)
        r_dev = self.deviation_detector.detect(target, comparables)

        signals = {
            "iqr": r_iqr,
            "robust_zscore": r_z,
            "isolation_forest": r_iforest,
            "comparable_deviation": r_dev,
        }

        # Count positive anomaly triggers
        flagged_count = sum(1 for res in signals.values() if res["is_anomaly"])

        # Determine statistical confidence
        if flagged_count >= 3:
            confidence = CONFIDENCE_STRONG
            is_anomaly = True
        elif flagged_count == 2:
            confidence = CONFIDENCE_MODERATE
            is_anomaly = True
        elif flagged_count == 1:
            confidence = CONFIDENCE_WEAK
            is_anomaly = False
        else:
            confidence = CONFIDENCE_STRONG
            is_anomaly = False

        # Craft objective explanation adhering to critical accuracy rules
        dev_metrics = r_dev.get("metrics", {})
        med_sqm = dev_metrics.get("comparable_median_sqm", 0)
        diff_pct = dev_metrics.get("difference_percent", 0.0)

        direction_en = "lower-priced than" if diff_pct < 0 else "higher-priced than"
        direction_fa = "پایین‌تر از" if diff_pct < 0 else "بالاتر از"

        if is_anomaly:
            explanation = (
                f"Statistically unusual relative to comparable observed listings. "
                f"Price/m² ({format_toman(target.price_per_m2, False)}) is {abs(diff_pct):.1f}% {direction_en} "
                f"the local comparable median ({format_toman(med_sqm, False)}). "
                f"Triggered {flagged_count}/4 statistical models ({confidence} evidence, sample: {sample_size})."
            )
            summary = (
                f"از نظر آماری نسبت به املاک مشابه نامتعارف است: قیمت هر متر مربع {abs(diff_pct):.1f}٪ {direction_fa} "
                f"میانه منطقه است (شواهد {confidence}، بر اساس {sample_size} ملک مشابه)."
            )
        else:
            explanation = (
                f"Within normal statistical variance for local comparable group. "
                f"Deviation from median is {diff_pct:+.1f}% (sample: {sample_size})."
            )
            summary = f"در محدوده آماری طبیعی نسبت به املاک مشابه (انحراف: {diff_pct:+.1f}٪)."

        return {
            "is_anomaly": is_anomaly,
            "confidence": confidence,
            "sample_size": sample_size,
            "flagged_count": flagged_count,
            "score": round(diff_pct, 2),
            "explanation": explanation,
            "summary": summary,
            "signals": signals,
            "metrics": {
                "target_sqm": target.price_per_m2,
                "comparable_median_sqm": med_sqm,
                "difference_percent": diff_pct,
                "sample_size": sample_size,
                "iqr_score": r_iqr.get("score"),
                "robust_z_score": r_z.get("score"),
                "isolation_forest_score": r_iforest.get("score"),
            },
        }
