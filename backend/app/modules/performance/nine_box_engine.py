"""
NexusTalent 9-Box Talent Calibration Matrix Engine
Calculates Performance (X-axis) vs Potential (Y-axis) classifications.
"""

from typing import Dict, Tuple, Any


class NineBoxEngine:
    """
    Standard McKinsey / GE 9-Box Talent Matrix.
    Scores range from 1 (Low) to 3 (High).
    """

    MATRIX_CATEGORIES: Dict[str, Dict[str, Any]] = {
        "3_3": {"category": "Star / Future Leader", "action": "Accelerate growth, assign to executive succession.", "color": "#10B981", "perf": 3, "pot": 3},
        "2_3": {"category": "High Potential", "action": "Stretch assignments, leadership coaching.", "color": "#3B82F6", "perf": 2, "pot": 3},
        "1_3": {"category": "Enigma / Diamond in Rough", "action": "Identify performance barriers, mentor closely.", "color": "#8B5CF6", "perf": 1, "pot": 3},
        "3_2": {"category": "High Performer", "action": "Recognize, reward, and provide technical mastery paths.", "color": "#06B6D4", "perf": 3, "pot": 2},
        "2_2": {"category": "Core Player", "action": "Solid performer; continuous development and stability.", "color": "#6366F1", "perf": 2, "pot": 2},
        "1_2": {"category": "Inconsistent Performer", "action": "Targeted skill training, performance milestones.", "color": "#F59E0B", "perf": 1, "pot": 2},
        "3_1": {"category": "Solid Professional", "action": "Valuable expert; retain and avoid overload.", "color": "#14B8A6", "perf": 3, "pot": 1},
        "2_1": {"category": "Effective Contributor", "action": "Coach on potential, monitor output.", "color": "#EC4899", "perf": 2, "pot": 1},
        "1_1": {"category": "Risk / Action Needed", "action": "Initiate Performance Improvement Plan (PIP).", "color": "#EF4444", "perf": 1, "pot": 1},
    }

    @classmethod
    def classify(cls, performance_score: int, potential_score: int) -> Dict[str, Any]:
        p_clamped = max(1, min(3, performance_score))
        pot_clamped = max(1, min(3, potential_score))
        key = f"{p_clamped}_{pot_clamped}"
        return cls.MATRIX_CATEGORIES.get(key, {
            "category": "Core Player",
            "action": "Development",
            "color": "#6366F1",
            "perf": 2,
            "pot": 2
        })
