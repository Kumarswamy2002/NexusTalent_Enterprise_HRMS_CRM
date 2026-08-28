"""
NexusTalent HRMS Router
REST API endpoints for Employee Master, Departments, and Org Chart.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, UserContext, require_permission
from backend.app.modules.hrms.schemas import EmployeeCreate, EmployeeUpdate, DepartmentCreate
from backend.app.modules.hrms.service import HRMSService

router = APIRouter(prefix="/hrms", tags=["Core HRMS & Org Hierarchy"])


@router.post("/departments", status_code=status.HTTP_201_CREATED)
async def create_department(
    data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("settings:manage"))
):
    dept = await HRMSService.create_department(db, data, user.tenant_id)
    return dept.to_dict()


@router.get("/departments")
async def list_departments(
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    return await HRMSService.list_departments(db, user.tenant_id)


@router.post("/employees", status_code=status.HTTP_201_CREATED)
async def create_employee(
    data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("employees:write"))
):
    emp = await HRMSService.create_employee(db, data, user.tenant_id, user.user_id)
    return emp.to_dict()


@router.get("/employees")
async def list_employees(
    department_id: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("employees:read"))
):
    return await HRMSService.list_employees(
        session=db,
        tenant_id=user.tenant_id,
        department_id=department_id,
        search=search,
        limit=limit,
        offset=offset
    )


@router.get("/employees/{employee_id}")
async def get_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("employees:read"))
):
    emp = await HRMSService.get_employee_by_id(db, employee_id, user.tenant_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.get("/org-chart")
async def get_org_chart(
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    return await HRMSService.build_org_chart(db, user.tenant_id)
