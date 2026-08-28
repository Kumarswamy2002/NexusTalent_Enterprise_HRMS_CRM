"""
NexusTalent Payroll Router
REST API endpoints for Salary Structures, Monthly Batches & Payslip inspection.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, UserContext, require_permission
from backend.app.modules.payroll.models import PayrollRun
from backend.app.modules.payroll.schemas import SalaryStructureCreate, PayrollRunCreate
from backend.app.modules.payroll.service import PayrollService

router = APIRouter(prefix="/payroll", tags=["Global Payroll & Tax Engine"])


@router.post("/structures", status_code=status.HTTP_201_CREATED)
async def create_salary_structure(
    data: SalaryStructureCreate,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("payroll:write"))
):
    struct = await PayrollService.create_structure(db, data, user.tenant_id)
    return struct.to_dict()


@router.post("/runs", status_code=status.HTTP_201_CREATED)
async def execute_payroll_run(
    data: PayrollRunCreate,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("payroll:execute"))
):
    try:
        run = await PayrollService.execute_payroll_run(db, data, user.tenant_id, user.user_id)
        return run.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/runs")
async def list_payroll_runs(
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("payroll:read"))
):
    stmt = select(PayrollRun).where(PayrollRun.tenant_id == user.tenant_id).order_by(PayrollRun.period_year.desc(), PayrollRun.period_month.desc())
    res = await db.execute(stmt)
    runs = res.scalars().all()
    return [r.to_dict() for r in runs]


@router.get("/runs/{run_id}/payslips")
async def list_payslips_for_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("payroll:read"))
):
    return await PayrollService.list_payslips_for_run(db, run_id, user.tenant_id)
