"""
NexusTalent Recruitment & Talent CRM Models
Job Requisitions, Candidate Leads, Applications, Scorecards & Offer Management
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Date, DateTime, Float, ForeignKey, Integer, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
import enum


class RequisitionStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    OPEN = "open"
    ON_HOLD = "on_hold"
    FILLED = "filled"
    CANCELLED = "cancelled"


class CandidateSource(str, enum.Enum):
    LINKEDIN = "linkedin"
    CAREER_PORTAL = "career_portal"
    REFERRAL = "referral"
    AGENCY = "agency"
    DIRECT_OUTREACH = "direct_outreach"


class PipelineStage(str, enum.Enum):
    SOURCED = "sourced"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEWING = "interviewing"
    TECH_ASSESSMENT = "tech_assessment"
    OFFER_EXTENDED = "offer_extended"
    OFFER_ACCEPTED = "offer_accepted"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class JobRequisition(Base):
    """Job Requisition / Vacancy."""
    __tablename__ = "recruitment_requisitions"

    title: Mapped[str] = mapped_column(String(120), index=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    department_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("hrms_departments.id"), nullable=True)
    hiring_manager_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("hrms_employees.id"), nullable=True)
    open_positions: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[RequisitionStatus] = mapped_column(String(30), default=RequisitionStatus.OPEN)
    location: Mapped[str] = mapped_column(String(100), default="Remote / Hybrid")
    experience_years_min: Mapped[int] = mapped_column(Integer, default=2)
    min_budget: Mapped[float] = mapped_column(Float, default=80000.0)
    max_budget: Mapped[float] = mapped_column(Float, default=130000.0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    job_description: Mapped[str] = mapped_column(Text, default="")
    required_skills: Mapped[str] = mapped_column(Text, default="")  # Comma-separated or JSON string

    applications: Mapped[List["CandidateApplication"]] = relationship("CandidateApplication", back_populates="requisition")


class Candidate(Base):
    """Candidate Lead Profile in Talent CRM."""
    __tablename__ = "recruitment_candidates"

    first_name: Mapped[str] = mapped_column(String(60))
    last_name: Mapped[str] = mapped_column(String(60))
    email: Mapped[str] = mapped_column(String(120), index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    current_company: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    current_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    years_of_experience: Mapped[float] = mapped_column(Float, default=0.0)
    skills_tags: Mapped[str] = mapped_column(Text, default="")  # Comma-separated
    source: Mapped[CandidateSource] = mapped_column(String(30), default=CandidateSource.CAREER_PORTAL)
    resume_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    parsed_skills: Mapped[str] = mapped_column(Text, default="[]")
    ai_match_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0 to 100%

    applications: Mapped[List["CandidateApplication"]] = relationship("CandidateApplication", back_populates="candidate")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class CandidateApplication(Base):
    """Application entity tracking stage in the recruitment pipeline."""
    __tablename__ = "recruitment_applications"

    candidate_id: Mapped[str] = mapped_column(String(36), ForeignKey("recruitment_candidates.id"), index=True)
    requisition_id: Mapped[str] = mapped_column(String(36), ForeignKey("recruitment_requisitions.id"), index=True)
    stage: Mapped[PipelineStage] = mapped_column(String(30), default=PipelineStage.APPLIED, index=True)
    stage_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    overall_rating: Mapped[float] = mapped_column(Float, default=0.0)  # 1.0 to 5.0

    candidate: Mapped[Candidate] = relationship("Candidate", back_populates="applications")
    requisition: Mapped[JobRequisition] = relationship("JobRequisition", back_populates="applications")
    scorecards: Mapped[List["InterviewScorecard"]] = relationship("InterviewScorecard", back_populates="application")


class InterviewScorecard(Base):
    """Structured Interview Feedback & Scorecard."""
    __tablename__ = "recruitment_scorecards"

    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("recruitment_applications.id"), index=True)
    interviewer_id: Mapped[str] = mapped_column(String(36), ForeignKey("hrms_employees.id"))
    round_name: Mapped[str] = mapped_column(String(100), default="Technical Round 1")
    technical_score: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    communication_score: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    cultural_fit_score: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    recommendation: Mapped[str] = mapped_column(String(30), default="strong_yes")  # strong_yes, yes, neutral, no, strong_no
    feedback_notes: Mapped[str] = mapped_column(Text, default="")

    application: Mapped[CandidateApplication] = relationship("CandidateApplication", back_populates="scorecards")
