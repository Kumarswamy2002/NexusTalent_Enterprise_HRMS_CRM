"""
NexusTalent HRMS Schemas
Pydantic v2 DTOs with dynamic attributes support
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field
from backend.app.modules.hrms.models import EmploymentType, EmployeeStatus


class DepartmentCreate(BaseModel):
    name: str
    code: str
    budget: float = 0.0
    location: str = "Headquarters"
    head_employee_id: Optional[str] = None


class DepartmentOut(BaseModel):
    id: str
    name: str
    code: str
    budget: float
    location: str
    head_employee_id: Optional[str]
    employee_count: int = 0
    
    class Config:
        from_attributes = True


class EmployeeCreate(BaseModel):
    employee_code: Optional[str] = None
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    department_id: Optional[str] = None
    designation: str = "Software Engineer"
    manager_id: Optional[str] = None
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    date_of_joining: Optional[date] = None
    work_location: str = "San Francisco HQ"
    is_remote: bool = False
    base_annual_salary: float = 85000.0
    currency: str = "USD"
    extra_attributes: Dict[str, Any] = Field(default_factory=dict)


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    department_id: Optional[str] = None
    designation: Optional[str] = None
    manager_id: Optional[str] = None
    employment_type: Optional[EmploymentType] = None
    status: Optional[EmployeeStatus] = None
    work_location: Optional[str] = None
    is_remote: Optional[bool] = None
    base_annual_salary: Optional[float] = None
    currency: Optional[str] = None
    extra_attributes: Optional[Dict[str, Any]] = None


class EmployeeOut(BaseModel):
    id: str
    tenant_id: str
    employee_code: str
    first_name: str
    last_name: str
    full_name: str
    email: str
    phone: Optional[str]
    department_id: Optional[str]
    department_name: Optional[str] = None
    designation: str
    manager_id: Optional[str]
    manager_name: Optional[str] = None
    employment_type: str
    status: str
    date_of_joining: date
    work_location: str
    is_remote: bool
    base_annual_salary: float
    currency: str
    extra_attributes: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class OrgNode(BaseModel):
    id: str
    name: str
    title: str
    department: str
    avatar_url: Optional[str] = None
    reports: List["OrgNode"] = []
