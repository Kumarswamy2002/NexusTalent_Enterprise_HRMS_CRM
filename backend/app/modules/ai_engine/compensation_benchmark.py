"""
NexusTalent Compensation Benchmark & Market Equity Analyzer
Compares internal employee salary bands against industry percentiles.
"""

from typing import Dict, Any, List


class CompensationBenchmarkEngine:
    # Industry 25th, 50th (Median), and 75th percentiles (USD Annual)
    MARKET_BENCHMARKS: Dict[str, Dict[str, float]] = {
        "Software Engineer": {"p25": 95000.0, "median": 120000.0, "p75": 145000.0},
        "Senior Software Engineer": {"p25": 135000.0, "median": 165000.0, "p75": 195000.0},
        "Staff Engineer": {"p25": 180000.0, "median": 220000.0, "p75": 260000.0},
        "Engineering Manager": {"p25": 160000.0, "median": 195000.0, "p75": 235000.0},
        "Product Manager": {"p25": 110000.0, "median": 140000.0, "p75": 170000.0},
        "HR Business Partner": {"p25": 75000.0, "median": 95000.0, "p75": 115000.0},
        "Technical Recruiter": {"p25": 70000.0, "median": 90000.0, "p75": 110000.0},
        "Account Executive": {"p25": 80000.0, "median": 105000.0, "p75": 135000.0},
        "Financial Analyst": {"p25": 80000.0, "median": 100000.0, "p75": 125000.0},
    }

    @classmethod
    def analyze_employee_equity(cls, designation: str, current_salary: float) -> Dict[str, Any]:
        bench = cls.MARKET_BENCHMARKS.get(designation, {"p25": 70000.0, "median": 90000.0, "p75": 115000.0})
        compa_ratio = round((current_salary / bench["median"]) * 100.0, 1)

        if compa_ratio < 85.0:
            status = "Underpaid / Retention Threat"
            color = "#EF4444"
        elif compa_ratio <= 115.0:
            status = "Market Competitive / Healthy"
            color = "#10B981"
        else:
            status = "Above Market Top Tier"
            color = "#8B5CF6"

        return {
            "designation": designation,
            "current_salary": current_salary,
            "market_p25": bench["p25"],
            "market_median": bench["median"],
            "market_p75": bench["p75"],
            "compa_ratio": compa_ratio,
            "status": status,
            "status_color": color
        }
