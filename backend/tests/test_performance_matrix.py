from backend.app.services.performance_matrix_service import PerformanceMatrixService

def test_performance_calibration():
    scores = {"manager": 4.5, "peer": 4.0, "self": 4.0, "direct_report": 4.2}
    res = PerformanceMatrixService.calculate_calibrated_rating(scores)
    assert res["calibrated_rating"] >= 4.0
    assert res["performance_tier"] == "EXCEEDS_EXPECTATIONS"
