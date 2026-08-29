"""
Employee Onboarding & Asset Provisioning Orchestrator
"""
from typing import List, Dict, Any

class OnboardingOrchestrator:
    STANDARD_TASKS = [
        {"id": "t1", "title": "Sign NDA & Offer Letter", "department": "HR"},
        {"id": "t2", "title": "Provision Laptop & Email", "department": "IT"},
        {"id": "t3", "title": "Direct Deposit Setup", "department": "Payroll"},
        {"id": "t4", "title": "Team Introduction Meeting", "department": "Engineering"}
    ]

    @classmethod
    def initialize_onboarding_plan(cls, employee_id: str, role: str) -> Dict[str, Any]:
        return {
            "employee_id": employee_id,
            "role": role,
            "tasks": cls.STANDARD_TASKS,
            "total_tasks": len(cls.STANDARD_TASKS),
            "completed_tasks": 0,
            "progress_percent": 0.0
        }
