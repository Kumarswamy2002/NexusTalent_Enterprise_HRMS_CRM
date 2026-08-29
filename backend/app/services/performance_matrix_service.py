"""
360-Degree Performance Review & OKR Tracking Engine
"""
from typing import Dict, Any, List

class PerformanceMatrixService:
    WEIGHTS = {"manager": 0.50, "peer": 0.25, "self": 0.15, "direct_report": 0.10}

    @classmethod
    def calculate_calibrated_rating(cls, ratings_by_role: Dict[str, float]) -> Dict[str, Any]:
        weighted_score = 0.0
        total_weight = 0.0
        for role, weight in cls.WEIGHTS.items():
            if role in ratings_by_role:
                weighted_score += ratings_by_role[role] * weight
                total_weight += weight
        final_rating = (weighted_score / total_weight) if total_weight > 0 else 0.0
        tier = "EXCEEDS_EXPECTATIONS" if final_rating >= 4.2 else ("MEETS_EXPECTATIONS" if final_rating >= 3.0 else "NEEDS_IMPROVEMENT")
        return {
            "calibrated_rating": round(final_rating, 2),
            "performance_tier": tier
        }
