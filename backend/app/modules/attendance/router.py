"""
NexusTalent Time, Attendance & Leaves Router
REST API endpoints for Clock-in/out, Geofence Verification, Daily Reports, and Leave Approvals.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, UserContext, require_permission
from backend.app.modules.attendance.schemas import (
    ClockInRequest, ClockOutRequest, LeaveRequestCreate, LeaveApprovalAction
)
from backend.app.modules.attendance.service import AttendanceService
from backend.app.core.workflow_engine import TransitionError

router = APIRouter(prefix="/attendance", tags=["Time, Attendance & Leaves"])


@router.post("/clock-in", status_code=status.HTTP_201_CREATED)
async def clock_in(
    data: ClockInRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("attendance:self_clock"))
):
    try:
        client_ip = request.client.host if request.client else "127.0.0.1"
        rec = await AttendanceService.clock_in(db, data, user.tenant_id, client_ip)
        return {
            "status": "success",
            "message": "Clock-in recorded successfully",
            "record": rec.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/clock-out")
async def clock_out(
    data: ClockOutRequest,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("attendance:self_clock"))
):
    try:
        rec = await AttendanceService.clock_out(db, data, user.tenant_id)
        return {
            "status": "success",
            "message": "Clock-out recorded successfully",
            "record": rec.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/daily-dashboard")
async def get_daily_dashboard(
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("attendance:read"))
):
    return await AttendanceService.get_daily_dashboard(db, user.tenant_id)


@router.post("/leaves", status_code=status.HTTP_201_CREATED)
async def request_leave(
    data: LeaveRequestCreate,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("attendance:leave_request"))
):
    try:
        req = await AttendanceService.submit_leave_request(db, data, user.tenant_id)
        return req.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/leaves/{leave_id}/action")
async def approve_or_reject_leave(
    leave_id: str,
    data: LeaveApprovalAction,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("attendance:approve"))
):
    try:
        req = await AttendanceService.process_leave_action(
            session=db,
            leave_id=leave_id,
            action=data.action,
            actor_id=user.user_id,
            actor_roles=user.roles,
            tenant_id=user.tenant_id,
            comment=data.comment
        )
        return {"status": "success", "leave_id": req.id, "current_status": req.status.value}
    except (TransitionError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
