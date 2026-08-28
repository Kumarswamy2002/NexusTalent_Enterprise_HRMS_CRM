"""
NexusTalent Payroll Schemas
Pydantic v2 DTOs for Salary Structures, Payroll Batches & Payslip generation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.modules.payroll.models import PayrollRunStatus


class SalaryStructureCreate(BaseModel):
    name: str
    currency: str = "USD"
    basic_percentage: float = 50.0
    hra_percentage: float = 20.0
    special_allowance_formula: str = "CTC - (BASIC + HRA)"
    pf_deduction_rate: float = 12.0
    tax_rate_estimated: float = 15.0


class PayrollRunCreate(BaseModel):
    period_month: int = Field(ge=1, le=12)
    period_year: int = Field(ge=2020, le=2050)


class PayslipOut(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    employee_code: str
    designation: str
    department: str
    period: str
    basic_pay: float
    hra: float
    allowances: float
    gross_earnings: float
    provident_fund: float
    tax_deduction: float
    loss_of_pay: float
    total_deductions: float
    net_pay: float
    currency: str
    verification_hash: str
