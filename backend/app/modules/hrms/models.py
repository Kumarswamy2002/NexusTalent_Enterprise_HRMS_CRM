"""
NexusTalent Core HRMS Models
Department, Designation, Employee Master, Employment History & Documents
"""

from datetime import date
from typing import Optional, List
from sqlalchemy import String, Date, Float, ForeignKey, Integer, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
import enum


class EmploymentType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACTOR = "contractor"
    INTERN = "intern"


class EmployeeStatus(str, enum.Enum):
    PROBATION = "probation"
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    NOTICE_PERIOD = "notice_period"
    TERMINATED = "terminated"


class Department(Base):
    __tablename__ = "hrms_departments"

    name: Mapped[str] = mapped_column(String(100), index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    head_employee_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    budget: Mapped[float] = mapped_column(Float, default=0.0)
    location: Mapped[str] = mapped_column(String(100), default="Headquarters")

    employees: Mapped[List["Employee"]] = relationship("Employee", back_populates="department", foreign_keys="Employee.department_id")


class Designation(Base):
    __tablename__ = "hrms_designations"

    title: Mapped[str] = mapped_column(String(100), index=True)
    level: Mapped[int] = mapped_column(Integer, default=1)  # 1 (Junior) to 10 (C-Suite)
    band: Mapped[str] = mapped_column(String(20), default="B1")
    min_salary: Mapped[float] = mapped_column(Float, default=40000.0)
    max_salary: Mapped[float] = mapped_column(Float, default=80000.0)


class Employee(Base):
    """Core Employee Master Record."""
    __tablename__ = "hrms_employees"

    employee_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(60))
    last_name: Mapped[str] = mapped_column(String(60))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    
    # Org Placement
    department_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("hrms_departments.id"), nullable=True)
    designation: Mapped[str] = mapped_column(String(100), default="Associate")
    manager_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("hrms_employees.id"), nullable=True)
    
    # Employment Details
    employment_type: Mapped[EmploymentType] = mapped_column(String(30), default=EmploymentType.FULL_TIME)
    status: Mapped[EmployeeStatus] = mapped_column(String(30), default=EmployeeStatus.ACTIVE)
    date_of_joining: Mapped[date] = mapped_column(Date, default=date.today)
    date_of_exit: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Location & Work Model
    work_location: Mapped[str] = mapped_column(String(100), default="San Francisco, CA")
    is_remote: Mapped[bool] = mapped_column(default=False)
    
    # Compensation Base
    base_annual_salary: Mapped[float] = mapped_column(Float, default=75000.0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    
    # Relationships
    department: Mapped[Optional[Department]] = relationship("Department", back_populates="employees", foreign_keys=[department_id])
    manager: Mapped[Optional["Employee"]] = relationship("Employee", remote_side="Employee.id", foreign_keys=[manager_id])

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
