from backend.app.services.compensation_equity_service import CompensationEquityService

def test_compa_ratio_healthy():
    res = CompensationEquityService.evaluate_compa_ratio(100000, 80000, 100000, 120000)
    assert res["compa_ratio"] == 100.0
    assert res["equity_status"] == "HEALTHY"
