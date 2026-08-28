"""
NexusTalent Recruitment Schemas
Pydantic v2 DTOs for Job Requisitions, Candidates, Pipeline Transitions, and Scorecards.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from backend.app.modules.recruitment.models import (
    RequisitionStatus, CandidateSource, PipelineStage
)


class RequisitionCreate(BaseModel):
    title: str
    code: Optional[str] = None
    department_id: Optional[str] = None
    hiring_manager_id: Optional[str] = None
    open_positions: int = 1
    location: str = "Remote / Hybrid"
    experience_years_min: int = 2
    min_budget: float = 80000.0
    max_budget: float = 130000.0
    currency: str = "USD"
    job_description: str = ""
    required_skills: str = ""


class CandidateCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    current_company: Optional[str] = None
    current_title: Optional[str] = None
    years_of_experience: float = 0.0
    skills_tags: str = ""
    source: CandidateSource = CandidateSource.CAREER_PORTAL
    resume_url: Optional[str] = None
    requisition_id: Optional[str] = None  # Auto-attach to pipeline if provided


class StageTransitionRequest(BaseModel):
    target_stage: PipelineStage
    rejection_reason: Optional[str] = None
    comment: Optional[str] = None


class ScorecardCreate(BaseModel):
    interviewer_id: str
    round_name: str = "Technical Round 1"
    technical_score: int = Field(default=3, ge=1, le=5)
    communication_score: int = Field(default=3, ge=1, le=5)
    cultural_fit_score: int = Field(default=3, ge=1, le=5)
    recommendation: str = "yes"
    feedback_notes: str = ""


class KanbanColumn(BaseModel):
    stage: str
    label: str
    count: int
    applications: List[Dict[str, Any]]
