"""
Global Leave & Attendance Accrual Engine
"""
from decimal import Decimal
from typing import Dict, Any

class LeaveAccrualEngine:
    @staticmethod
    def calculate_monthly_accrual(annual_allowance_days: float, months_worked: int, days_taken: float, max_rollover: float = 5.0) -> Dict[str, Any]:
        monthly_rate = Decimal(str(annual_allowance_days)) / Decimal("12")
        accrued = monthly_rate * Decimal(str(months_worked))
        balance = max(Decimal("0.0"), accrued - Decimal(str(days_taken)))
        return {
            "accrued_days": float(round(accrued, 2)),
            "days_taken": days_taken,
            "current_balance_days": float(round(balance, 2)),
            "eligible_for_rollover": float(min(balance, Decimal(str(max_rollover))))
        }
