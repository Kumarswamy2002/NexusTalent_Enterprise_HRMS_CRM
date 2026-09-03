"""
NexusTalent Time, Attendance & Leaves Models
Attendance Logs, Geofence Boundaries, Shifts, Leave Allocations & Requests
"""

from datetime import datetime, date, time, timezone
from typing import Optional, List
from sqlalchemy import String, Date, DateTime, Time, Float, ForeignKey, Integer, Text, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
import enum


class AttendanceType(str, enum.Enum):
    OFFICE = "office"
    REMOTE = "remote"
    FIELD = "field"


class LeaveType(str, enum.Enum):
    PAID_TIME_OFF = "paid_time_off"
    SICK_LEAVE = "sick_leave"
    CASUAL_LEAVE = "casual_leave"
    MATERNITY_PATERNITY = "parental_leave"
    UNPAID = "unpaid"


class LeaveStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    MANAGER_APPROVED = "manager_approved"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Shift(Base):
    """Working shift definitions."""
    __tablename__ = "attendance_shifts"

    name: Mapped[str] = mapped_column(String(60))  # e.g. General US, Night Shift
    start_time: Mapped[time] = mapped_column(Time, default=time(9, 0))
    end_time: Mapped[time] = mapped_column(Time, default=time(17, 0))
    grace_period_minutes: Mapped[int] = mapped_column(Integer, default=15)
    break_duration_minutes: Mapped[int] = mapped_column(Integer, default=60)


class AttendanceRecord(Base):
    """Daily clock-in/out record with GPS geofence audit."""
    __tablename__ = "attendance_records"

    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("hrms_employees.id"), index=True)
    work_date: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    clock_in: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    clock_out: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Geofence validation
    attendance_type: Mapped[AttendanceType] = mapped_column(String(20), default=AttendanceType.OFFICE)
    latitude_in: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude_in: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    distance_from_hq_meters: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_geofence_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Calculated hours
    total_work_minutes: Mapped[int] = mapped_column(Integer, default=0)
    overtime_minutes: Mapped[int] = mapped_column(Integer, default=0)
    is_late: Mapped[bool] = mapped_column(Boolean, default=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    employee: Mapped["backend.app.modules.hrms.models.Employee"] = relationship("Employee")


class LeaveBalance(Base):
    """Leave quotas & balances per employee."""
    __tablename__ = "attendance_leave_balances"

    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("hrms_employees.id"), index=True)
    leave_type: Mapped[LeaveType] = mapped_column(String(30))
    total_allocated: Mapped[float] = mapped_column(Float, default=18.0)
    used_days: Mapped[float] = mapped_column(Float, default=0.0)
    pending_days: Mapped[float] = mapped_column(Float, default=0.0)

    @property
    def remaining_days(self) -> float:
        return self.total_allocated - self.used_days - self.pending_days


class LeaveRequest(Base):
    """Leave Application processed via Universal Workflow Engine."""
    __tablename__ = "attendance_leave_requests"

    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("hrms_employees.id"), index=True)
    leave_type: Mapped[LeaveType] = mapped_column(String(30))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    total_days: Mapped[float] = mapped_column(Float, default=1.0)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[LeaveStatus] = mapped_column(String(30), default=LeaveStatus.SUBMITTED, index=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    rejection_comment: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    employee: Mapped["backend.app.modules.hrms.models.Employee"] = relationship("Employee")
