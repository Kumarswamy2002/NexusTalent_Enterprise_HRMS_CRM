"""
NexusTalent Payroll Models
Salary Components, Dynamic Structures, Monthly Payroll Runs & Itemized Payslips
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, Date, DateTime, Float, ForeignKey, Integer, Text, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
import enum


class ComponentType(str, enum.Enum):
    EARNING = "earning"
    DEDUCTION = "deduction"
    BENEFIT = "benefit"


class PayrollRunStatus(str, enum.Enum):
    DRAFT = "draft"
    CALCULATED = "calculated"
    AUDITED = "under_audit"
    APPROVED = "approved"
    DISBURSED = "disbursed"
    CANCELLED = "cancelled"


class SalaryStructure(Base):
    """Configurable Salary breakdown rule set."""
    __tablename__ = "payroll_salary_structures"

    name: Mapped[str] = mapped_column(String(100), index=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    basic_percentage: Mapped[float] = mapped_column(Float, default=50.0)  # 50% of CTC
    hra_percentage: Mapped[float] = mapped_column(Float, default=20.0)    # 20% of CTC
    special_allowance_formula: Mapped[str] = mapped_column(String(255), default="CTC - (BASIC + HRA)")
    pf_deduction_rate: Mapped[float] = mapped_column(Float, default=12.0)  # 12% of Basic
    tax_rate_estimated: Mapped[float] = mapped_column(Float, default=15.0) # 15% estimated


class PayrollRun(Base):
    """Monthly Batch Payroll Cycle Execution."""
    __tablename__ = "payroll_runs"

    period_month: Mapped[int] = mapped_column(Integer)  # 1 to 12
    period_year: Mapped[int] = mapped_column(Integer)   # e.g. 2026
    status: Mapped[PayrollRunStatus] = mapped_column(String(30), default=PayrollRunStatus.DRAFT, index=True)
    total_gross_disbursed: Mapped[float] = mapped_column(Float, default=0.0)
    total_deductions: Mapped[float] = mapped_column(Float, default=0.0)
    total_net_disbursed: Mapped[float] = mapped_column(Float, default=0.0)
    total_employees_processed: Mapped[int] = mapped_column(Integer, default=0)
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    payslips: Mapped[List["Payslip"]] = relationship("Payslip", back_populates="payroll_run")


class Payslip(Base):
    """Itemized Employee Monthly Payslip."""
    __tablename__ = "payroll_payslips"

    payroll_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("payroll_runs.id"), index=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("hrms_employees.id"), index=True)
    
    # Financial breakdown
    basic_pay: Mapped[float] = mapped_column(Float, default=0.0)
    hra: Mapped[float] = mapped_column(Float, default=0.0)
    allowances: Mapped[float] = mapped_column(Float, default=0.0)
    bonus: Mapped[float] = mapped_column(Float, default=0.0)
    gross_earnings: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Deductions
    provident_fund: Mapped[float] = mapped_column(Float, default=0.0)
    tax_deduction: Mapped[float] = mapped_column(Float, default=0.0)
    loss_of_pay: Mapped[float] = mapped_column(Float, default=0.0)
    total_deductions: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Net Pay
    net_pay: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    verification_hash: Mapped[str] = mapped_column(String(64), default="")

    payroll_run: Mapped[PayrollRun] = relationship("PayrollRun", back_populates="payslips")
    employee: Mapped["backend.app.modules.hrms.models.Employee"] = relationship("Employee")
