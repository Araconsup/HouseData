"""
Batch Anomaly Processing Pipeline.
Iterates over active listings, extracts comparable pools, evaluates ensemble signals,
and records AnomalyResult records.
"""

import logging
from typing import Dict, Optional
from django.utils import timezone as django_tz

from analytics.comparables import ComparableService
from analytics.detectors import EnsembleAnomalyDetector
from analytics.models import AnomalyResult
from listings.models import DivarListing

logger = logging.getLogger(__name__)


class AnomalyPipelineService:
    """
    Coordinates batch anomaly detection runs across observed listings.
    """

    @classmethod
    def evaluate_listing(cls, listing: DivarListing) -> Dict:
        """
        Runs the full anomaly detection pipeline for a single listing.
        Updates listing fields and persists AnomalyResult records.
        """
        comparables, criteria = ComparableService.get_comparables(listing)
        ensemble = EnsembleAnomalyDetector()
        eval_result = ensemble.evaluate(listing, comparables)

        is_anomaly = eval_result.get("is_anomaly", False)
        confidence = eval_result.get("confidence", "insufficient_data")
        sample_size = eval_result.get("sample_size", 0)
        explanation = eval_result.get("explanation", "")
        summary = eval_result.get("summary", "")
        diff_score = eval_result.get("score")

        # Update cache columns on the listing model
        listing.is_anomaly = is_anomaly
        listing.anomaly_score = diff_score
        listing.anomaly_summary = summary
        listing.save(update_fields=["is_anomaly", "anomaly_score", "anomaly_summary"])

        # Persist individual detector results
        signals = eval_result.get("signals", {})
        for detector_name, sig_data in signals.items():
            AnomalyResult.objects.update_or_create(
                listing=listing,
                detector_name=detector_name,
                defaults={
                    "is_anomaly": sig_data.get("is_anomaly", False),
                    "score": sig_data.get("score"),
                    "explanation": sig_data.get("explanation", ""),
                    "sample_size": sample_size,
                    "confidence": confidence,
                    "metrics": sig_data.get("metrics", {}),
                }
            )

        # Persist overall ensemble record
        AnomalyResult.objects.update_or_create(
            listing=listing,
            detector_name="ensemble",
            defaults={
                "is_anomaly": is_anomaly,
                "score": diff_score,
                "explanation": explanation,
                "sample_size": sample_size,
                "confidence": confidence,
                "metrics": eval_result.get("metrics", {}),
            }
        )

        return eval_result

    @classmethod
    def run_batch_detection(cls, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Batch evaluate all active listings that have price per square meter.
        """
        qs = DivarListing.objects.filter(
            status="active",
            price_per_m2__isnull=False,
            city="tehran"
        ).order_by("-updated_at")

        if limit:
            qs = qs[:limit]

        processed = 0
        anomalies_found = 0

        for listing in qs:
            try:
                res = cls.evaluate_listing(listing)
                processed += 1
                if res.get("is_anomaly"):
                    anomalies_found += 1
            except Exception as e:
                logger.error(f"Error evaluating listing {listing.divar_token}: {e}")

        logger.info(f"Anomaly detection complete: {processed} processed, {anomalies_found} anomalies identified")
        return {"processed": processed, "anomalies_found": anomalies_found}
