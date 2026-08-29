from backend.app.services.leave_engine_service import LeaveAccrualEngine

def test_leave_accrual():
    res = LeaveAccrualEngine.calculate_monthly_accrual(24.0, 6, 4.0, 5.0)
    assert res["accrued_days"] == 12.0
    assert res["current_balance_days"] == 8.0
    assert res["eligible_for_rollover"] == 5.0
