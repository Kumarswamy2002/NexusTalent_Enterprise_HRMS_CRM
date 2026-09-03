"""
NexusTalent Attendance Service Layer
Manages Real-time Clocking, Geofencing Checks, Leave Accrual & Multi-tier Workflow Approvals.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload

from backend.app.modules.attendance.models import (
    AttendanceRecord, LeaveBalance, LeaveRequest, AttendanceType, LeaveStatus, LeaveType
)
from backend.app.modules.attendance.schemas import (
    ClockInRequest, ClockOutRequest, LeaveRequestCreate, LeaveApprovalAction
)
from backend.app.core.workflow_engine import WORKFLOW_REGISTRY, TransitionError
from backend.app.core.event_bus import event_bus, DomainEvent, EventTypes
from backend.app.modules.hrms.models import Employee
from backend.app.modules.attendance.geofence_engine import GeofenceEngine


def _get_val(enum_or_str: Any) -> str:
    return enum_or_str.value if hasattr(enum_or_str, "value") else str(enum_or_str)


class AttendanceService:

    @staticmethod
    async def clock_in(
        session: AsyncSession,
        data: ClockInRequest,
        tenant_id: str,
        ip_address: Optional[str] = None
    ) -> AttendanceRecord:
        today = date.today()
        now = datetime.now(timezone.utc)

        # Check existing clock-in today
        stmt = select(AttendanceRecord).where(
            AttendanceRecord.employee_id == data.employee_id,
            AttendanceRecord.work_date == today,
            AttendanceRecord.tenant_id == tenant_id
        )
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            raise ValueError("Employee is already clocked in for today.")

        # Geofence check
        is_verified = True
        dist = 0.0
        if data.attendance_type == AttendanceType.OFFICE and data.latitude and data.longitude:
            is_verified, dist = GeofenceEngine.verify_location(data.latitude, data.longitude)

        # Check late status (if after 9:15 AM)
        is_late = now.hour > 9 or (now.hour == 9 and now.minute > 15)

        record = AttendanceRecord(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            employee_id=data.employee_id,
            work_date=today,
            clock_in=now,
            attendance_type=data.attendance_type,
            latitude_in=data.latitude,
            longitude_in=data.longitude,
            distance_from_hq_meters=dist,
            is_geofence_verified=is_verified,
            is_late=is_late,
            ip_address=ip_address
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)

        await event_bus.publish(DomainEvent(
            event_type=EventTypes.ATTENDANCE_CLOCKED,
            tenant_id=tenant_id,
            actor_id=data.employee_id,
            payload={"id": record.id, "type": "clock_in", "is_late": is_late, "geofence_verified": is_verified}
        ))
        return record

    @staticmethod
    async def clock_out(
        session: AsyncSession,
        data: ClockOutRequest,
        tenant_id: str
    ) -> AttendanceRecord:
        today = date.today()
        now = datetime.now(timezone.utc)

        stmt = select(AttendanceRecord).where(
            AttendanceRecord.employee_id == data.employee_id,
            AttendanceRecord.work_date == today,
            AttendanceRecord.tenant_id == tenant_id
        )
        res = await session.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            raise ValueError("No clock-in record found for today.")
        if record.clock_out:
            raise ValueError("Employee has already clocked out today.")

        record.clock_out = now
        # Calculate minutes worked
        delta = now - record.clock_in.replace(tzinfo=timezone.utc if record.clock_in.tzinfo is None else None)
        minutes = int(delta.total_seconds() / 60)
        record.total_work_minutes = minutes
        if minutes > 480:  # > 8 hours
            record.overtime_minutes = minutes - 480

        await session.commit()
        await session.refresh(record)
        return record

    @staticmethod
    async def submit_leave_request(
        session: AsyncSession,
        data: LeaveRequestCreate,
        tenant_id: str
    ) -> LeaveRequest:
        delta_days = (data.end_date - data.start_date).days + 1
        if delta_days <= 0:
            raise ValueError("End date must be on or after start date.")

        req = LeaveRequest(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            employee_id=data.employee_id,
            leave_type=data.leave_type,
            start_date=data.start_date,
            end_date=data.end_date,
            total_days=float(delta_days),
            reason=data.reason,
            status=LeaveStatus.SUBMITTED
        )
        session.add(req)
        await session.commit()
        await session.refresh(req)

        await event_bus.publish(DomainEvent(
            event_type=EventTypes.LEAVE_REQUESTED,
            tenant_id=tenant_id,
            actor_id=data.employee_id,
            payload={"id": req.id, "days": req.total_days, "type": _get_val(req.leave_type)}
        ))
        return req

    @staticmethod
    async def get_leave_balances(session: AsyncSession, employee_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        stmt = select(LeaveBalance).where(LeaveBalance.employee_id == employee_id, LeaveBalance.tenant_id == tenant_id)
        res = await session.execute(stmt)
        balances = res.scalars().all()
        return [b.to_dict() for b in balances]

    @staticmethod
    async def process_leave_action(
        session: AsyncSession,
        leave_id: str,
        action: str,
        actor_id: str,
        actor_roles: set,
        tenant_id: str,
        comment: Optional[str] = None
    ) -> LeaveRequest:
        stmt = select(LeaveRequest).where(LeaveRequest.id == leave_id, LeaveRequest.tenant_id == tenant_id)
        res = await session.execute(stmt)
        req = res.scalar_one_or_none()
        if not req:
            raise ValueError("Leave request not found.")

        target_state = "approved" if action == "approve" else "rejected"
        workflow = WORKFLOW_REGISTRY["leave_request"]

        # Universal state machine verification
        current_status_val = _get_val(req.status)
        if not workflow.can_transition(current_status_val, target_state, actor_roles):
            raise TransitionError(f"Cannot transition leave from '{current_status_val}' to '{target_state}'")

        req.status = LeaveStatus.APPROVED if action == "approve" else LeaveStatus.REJECTED
        req.approved_by = actor_id
        req.rejection_comment = comment

        await session.commit()
        await session.refresh(req)

        await event_bus.publish(DomainEvent(
            event_type=EventTypes.LEAVE_APPROVED if action == "approve" else EventTypes.LEAVE_REJECTED,
            tenant_id=tenant_id,
            actor_id=actor_id,
            payload={"id": req.id, "status": _get_val(req.status)}
        ))
        return req

    @staticmethod
    async def get_daily_dashboard(session: AsyncSession, tenant_id: str) -> Dict[str, Any]:
        today = date.today()
        stmt = (
            select(AttendanceRecord)
            .options(selectinload(AttendanceRecord.employee))
            .where(AttendanceRecord.work_date == today, AttendanceRecord.tenant_id == tenant_id)
        )
        res = await session.execute(stmt)
        records = res.scalars().all()

        total_present = len(records)
        total_late = len([r for r in records if r.is_late])

        formatted_records = []
        for r in records:
            d = r.to_dict()
            d["employee_name"] = r.employee.full_name if r.employee else "Unknown"
            d["clock_in_time"] = r.clock_in.strftime("%H:%M:%S") if r.clock_in else "-"
            d["clock_out_time"] = r.clock_out.strftime("%H:%M:%S") if r.clock_out else "Active"
            formatted_records.append(d)

        return {
            "total_present_today": total_present,
            "total_on_leave_today": 2,  # Mocked baseline
            "total_late_today": total_late,
            "records": formatted_records
        }
