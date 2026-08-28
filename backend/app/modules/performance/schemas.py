"""
NexusTalent Performance Schemas
Pydantic v2 DTOs for OKRs, Key Results, and 9-Box Calibration.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from backend.app.modules.performance.models import OKRLevel, GoalStatus


class KeyResultCreate(BaseModel):
    title: str
    target_value: float = 100.0
    metric_unit: str = "%"


class ObjectiveCreate(BaseModel):
    title: str
    level: OKRLevel = OKRLevel.INDIVIDUAL
    owner_id: str
    department_id: Optional[str] = None
    quarter: str = "Q1-2026"
    key_results: List[KeyResultCreate] = []


class KeyResultUpdate(BaseModel):
    current_value: float


class NineBoxSubmit(BaseModel):
    employee_id: str
    performance_score: int = Field(ge=1, le=3)
    potential_score: int = Field(ge=1, le=3)
    notes: str = ""
