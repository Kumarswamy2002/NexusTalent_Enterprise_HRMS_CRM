"""
Enterprise ATS Candidate Pipeline & Interview Scoring Service
"""
from typing import List, Dict, Any

class CandidatePipelineService:
    @staticmethod
    def aggregate_interview_scores(candidate_id: str, scorecards: List[Dict[str, float]]) -> Dict[str, Any]:
        if not scorecards:
            return {"candidate_id": candidate_id, "average_score": 0.0, "recommendation": "NO_FEEDBACK"}
        total = sum(s.get("score", 0.0) for s in scorecards)
        avg = total / len(scorecards)
        recommendation = "STRONG_HIRE" if avg >= 4.5 else ("HIRE" if avg >= 3.5 else "REJECT")
        return {
            "candidate_id": candidate_id,
            "card_count": len(scorecards),
            "average_score": round(avg, 2),
            "recommendation": recommendation
        }
