"""
Compensation Equity & Salary Band Benchmarking Service
"""
from typing import Dict, Any

class CompensationEquityService:
    @staticmethod
    def evaluate_compa_ratio(salary: float, band_min: float, band_mid: float, band_max: float) -> Dict[str, Any]:
        compa_ratio = (salary / band_mid) * 100 if band_mid > 0 else 100.0
        range_penetration = ((salary - band_min) / (band_max - band_min)) * 100 if band_max > band_min else 50.0
        status = "HEALTHY" if 85.0 <= compa_ratio <= 115.0 else ("UNDERPAID" if compa_ratio < 85.0 else "OVER_BAND")
        return {
            "compa_ratio": round(compa_ratio, 2),
            "range_penetration_pct": round(max(0.0, min(100.0, range_penetration)), 2),
            "equity_status": status
        }
