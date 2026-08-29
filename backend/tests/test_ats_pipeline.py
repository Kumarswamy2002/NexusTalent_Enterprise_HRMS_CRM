from backend.app.services.ats_service import CandidatePipelineService

def test_ats_score_aggregation():
    scores = [{"score": 4.5}, {"score": 5.0}, {"score": 4.0}]
    res = CandidatePipelineService.aggregate_interview_scores("cand-1", scores)
    assert res["average_score"] == 4.5
    assert res["recommendation"] == "STRONG_HIRE"
