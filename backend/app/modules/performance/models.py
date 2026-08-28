"""
NexusTalent Performance Models
Cascading OKRs, Key Results, 360 Reviews & 9-Box Talent Matrix
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, Date, DateTime, Float, ForeignKey, Integer, Text, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
import enum


class OKRLevel(str, enum.Enum):
    COMPANY = "company"
    DEPARTMENT = "department"
    INDIVIDUAL = "individual"


class GoalStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    COMPLETED = "completed"


class Objective(Base):
    """Cascading OKR Objective."""
    __tablename__ = "perf_objectives"

    title: Mapped[str] = mapped_column(String(200), index=True)
    level: Mapped[OKRLevel] = mapped_column(String(30), default=OKRLevel.INDIVIDUAL)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("hrms_employees.id"), index=True)
    department_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    quarter: Mapped[str] = mapped_column(String(10), default="Q1-2026")
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[GoalStatus] = mapped_column(String(30), default=GoalStatus.IN_PROGRESS)

    key_results: Mapped[List["KeyResult"]] = relationship("KeyResult", back_populates="objective")
    owner: Mapped["backend.app.modules.hrms.models.Employee"] = relationship("Employee")


class KeyResult(Base):
    """Measurable Key Result under an Objective."""
    __tablename__ = "perf_key_results"

    objective_id: Mapped[str] = mapped_column(String(36), ForeignKey("perf_objectives.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    target_value: Mapped[float] = mapped_column(Float, default=100.0)
    current_value: Mapped[float] = mapped_column(Float, default=0.0)
    metric_unit: Mapped[str] = mapped_column(String(30), default="%")  # %, USD, Count, SLA

    objective: Mapped[Objective] = relationship("Objective", back_populates="key_results")


class NineBoxAssessment(Base):
    """
    9-Box Grid Assessment for Succession Planning & Talent Calibration:
    Performance (1-3) vs Potential (1-3)
    """
    __tablename__ = "perf_nine_box"

    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("hrms_employees.id"), index=True)
    reviewer_id: Mapped[str] = mapped_column(String(36), ForeignKey("hrms_employees.id"))
    cycle_name: Mapped[str] = mapped_column(String(100), default="Annual Calibration 2026")
    
    # 1=Low, 2=Medium, 3=High
    performance_score: Mapped[int] = mapped_column(Integer, default=2)
    potential_score: Mapped[int] = mapped_column(Integer, default=2)
    box_category: Mapped[str] = mapped_column(String(60), default="Core Player")
    notes: Mapped[str] = mapped_column(Text, default="")

    employee: Mapped["backend.app.modules.hrms.models.Employee"] = relationship("Employee", foreign_keys=[employee_id])
