"""
NexusTalent Payroll Service Layer
Batch Payroll Calculation, Dynamic Formula Evaluation, Tax Deductions & Cryptographic Payslip Verification.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload

from backend.app.modules.payroll.models import SalaryStructure, PayrollRun, Payslip, PayrollRunStatus
from backend.app.modules.payroll.schemas import SalaryStructureCreate, PayrollRunCreate
from backend.app.modules.payroll.formula_evaluator import SafeFormulaEvaluator
from backend.app.modules.hrms.models import Employee, EmployeeStatus
from backend.app.core.event_bus import event_bus, DomainEvent, EventTypes
from backend.app.core.workflow_engine import WORKFLOW_REGISTRY, TransitionError


class PayrollService:

    @staticmethod
    async def create_structure(session: AsyncSession, data: SalaryStructureCreate, tenant_id: str) -> SalaryStructure:
        struct = SalaryStructure(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=data.name,
            currency=data.currency,
            basic_percentage=data.basic_percentage,
            hra_percentage=data.hra_percentage,
            special_allowance_formula=data.special_allowance_formula,
            pf_deduction_rate=data.pf_deduction_rate,
            tax_rate_estimated=data.tax_rate_estimated
        )
        session.add(struct)
        await session.commit()
        await session.refresh(struct)
        return struct

    @staticmethod
    async def execute_payroll_run(
        session: AsyncSession,
        data: PayrollRunCreate,
        tenant_id: str,
        actor_id: str
    ) -> PayrollRun:
        # Check if already executed
        stmt = select(PayrollRun).where(
            PayrollRun.period_month == data.period_month,
            PayrollRun.period_year == data.period_year,
            PayrollRun.tenant_id == tenant_id
        )
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            raise ValueError(f"Payroll for {data.period_month}/{data.period_year} is already initiated.")

        # Get active employees
        emp_stmt = select(Employee).where(
            Employee.tenant_id == tenant_id,
            Employee.status == EmployeeStatus.ACTIVE
        )
        emp_res = await session.execute(emp_stmt)
        employees = emp_res.scalars().all()

        if not employees:
            raise ValueError("No active employees found to process payroll.")

        # Fetch active salary structure (or fallback default)
        struct_stmt = select(SalaryStructure).where(SalaryStructure.tenant_id == tenant_id).limit(1)
        struct_res = await session.execute(struct_stmt)
        struct = struct_res.scalar_one_or_none()

        basic_pct = struct.basic_percentage if struct else 50.0
        hra_pct = struct.hra_percentage if struct else 20.0
        pf_rate = struct.pf_deduction_rate if struct else 12.0
        tax_rate = struct.tax_rate_estimated if struct else 15.0

        payroll_run = PayrollRun(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            period_month=data.period_month,
            period_year=data.period_year,
            status=PayrollRunStatus.CALCULATED,
            total_employees_processed=len(employees)
        )
        session.add(payroll_run)
        await session.flush()

        total_gross = 0.0
        total_ded = 0.0
        total_net = 0.0

        for emp in employees:
            monthly_ctc = emp.base_annual_salary / 12.0
            basic = monthly_ctc * (basic_pct / 100.0)
            hra = monthly_ctc * (hra_pct / 100.0)

            # Use AST safe formula evaluator for special allowance
            vars_map = {"CTC": monthly_ctc, "BASIC": basic, "HRA": hra}
            try:
                formula_str = struct.special_allowance_formula if struct else "CTC - (BASIC + HRA)"
                allowance = SafeFormulaEvaluator.evaluate(formula_str, vars_map)
                if allowance < 0:
                    allowance = 0.0
            except Exception:
                allowance = monthly_ctc - (basic + hra)

            gross = basic + hra + allowance
            pf = basic * (pf_rate / 100.0)
            tax = gross * (tax_rate / 100.0)
            deductions = pf + tax
            net = gross - deductions

            total_gross += gross
            total_ded += deductions
            total_net += net

            # Generate tamper-evident payslip verification hash
            hash_payload = f"{emp.id}|{payroll_run.id}|{round(net, 2)}|{emp.tenant_id}"
            v_hash = hashlib.sha256(hash_payload.encode()).hexdigest()

            payslip = Payslip(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                payroll_run_id=payroll_run.id,
                employee_id=emp.id,
                basic_pay=round(basic, 2),
                hra=round(hra, 2),
                allowances=round(allowance, 2),
                gross_earnings=round(gross, 2),
                provident_fund=round(pf, 2),
                tax_deduction=round(tax, 2),
                total_deductions=round(deductions, 2),
                net_pay=round(net, 2),
                currency=emp.currency,
                verification_hash=v_hash
            )
            session.add(payslip)

        payroll_run.total_gross_disbursed = round(total_gross, 2)
        payroll_run.total_deductions = round(total_ded, 2)
        payroll_run.total_net_disbursed = round(total_net, 2)

        await session.commit()
        await session.refresh(payroll_run)

        await event_bus.publish(DomainEvent(
            event_type=EventTypes.PAYROLL_CALCULATED,
            tenant_id=tenant_id,
            actor_id=actor_id,
            payload={
                "payroll_run_id": payroll_run.id,
                "month": data.period_month,
                "year": data.period_year,
                "total_net": payroll_run.total_net_disbursed,
                "processed_count": payroll_run.total_employees_processed
            }
        ))
        return payroll_run

    @staticmethod
    async def list_payslips_for_run(session: AsyncSession, run_id: str, tenant_id: str) -> List[Dict[str, Any]]:
        stmt = (
            select(Payslip)
            .options(
                selectinload(Payslip.employee).selectinload(Employee.department),
                selectinload(Payslip.payroll_run)
            )
            .where(Payslip.payroll_run_id == run_id, Payslip.tenant_id == tenant_id)
        )
        res = await session.execute(stmt)
        payslips = res.scalars().all()

        output = []
        for p in payslips:
            d = p.to_dict()
            d["employee_name"] = p.employee.full_name if p.employee else "Unknown"
            d["employee_code"] = p.employee.employee_code if p.employee else "N/A"
            d["designation"] = p.employee.designation if p.employee else "Associate"
            d["department"] = p.employee.department.name if (p.employee and p.employee.department) else "General"
            d["period"] = f"{p.payroll_run.period_month:02d}/{p.payroll_run.period_year}" if p.payroll_run else ""
            output.append(d)
        return output
