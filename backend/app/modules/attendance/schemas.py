"""
NexusTalent Attendance Schemas
Pydantic v2 DTOs for Clock-in/out, Shifts, and Leave Management.
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime, time
from pydantic import BaseModel, Field
from backend.app.modules.attendance.models import AttendanceType, LeaveType, LeaveStatus


class ClockInRequest(BaseModel):
    employee_id: str
    attendance_type: AttendanceType = AttendanceType.OFFICE
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ClockOutRequest(BaseModel):
    employee_id: str


class LeaveRequestCreate(BaseModel):
    employee_id: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str


class LeaveApprovalAction(BaseModel):
    action: str = Field(..., description="approve or reject")  # approve, reject
    comment: Optional[str] = None


class AttendanceSummary(BaseModel):
    total_present_today: int
    total_on_leave_today: int
    total_late_today: int
    records: List[Dict[str, Any]]
