"""
NexusTalent HRMS Service Layer
Handles Employee Lifecycle, Dynamic Fields, and Org Chart Graph Construction.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload
import uuid

from backend.app.modules.hrms.models import Employee, Department, Designation, EmployeeStatus
from backend.app.modules.hrms.schemas import EmployeeCreate, EmployeeUpdate, DepartmentCreate, OrgNode
from backend.app.core.event_bus import event_bus, DomainEvent, EventTypes


class HRMSService:

    @staticmethod
    async def create_department(session: AsyncSession, data: DepartmentCreate, tenant_id: str) -> Department:
        dept = Department(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=data.name,
            code=data.code.upper(),
            budget=data.budget,
            location=data.location,
            head_employee_id=data.head_employee_id
        )
        session.add(dept)
        await session.commit()
        await session.refresh(dept)
        return dept

    @staticmethod
    async def list_departments(session: AsyncSession, tenant_id: str) -> List[Dict[str, Any]]:
        stmt = (
            select(Department, func.count(Employee.id).label("emp_count"))
            .outerjoin(Employee, Department.id == Employee.department_id)
            .where(Department.tenant_id == tenant_id)
            .group_by(Department.id)
        )
        result = await session.execute(stmt)
        dept_list = []
        for dept, count in result.all():
            dept_dict = dept.to_dict()
            dept_dict["employee_count"] = count
            dept_list.append(dept_dict)
        return dept_list

    @staticmethod
    async def create_employee(session: AsyncSession, data: EmployeeCreate, tenant_id: str, actor_id: str) -> Employee:
        # Generate employee code if not provided
        if not data.employee_code:
            count_stmt = select(func.count(Employee.id)).where(Employee.tenant_id == tenant_id)
            count_res = await session.execute(count_stmt)
            count = count_res.scalar() or 0
            code = f"NX-{1001 + count}"
        else:
            code = data.employee_code

        emp = Employee(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            employee_code=code,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            department_id=data.department_id,
            designation=data.designation,
            manager_id=data.manager_id,
            employment_type=data.employment_type,
            status=data.status,
            date_of_joining=data.date_of_joining,
            work_location=data.work_location,
            is_remote=data.is_remote,
            base_annual_salary=data.base_annual_salary,
            currency=data.currency,
            extra_attributes=data.extra_attributes
        )
        session.add(emp)
        await session.commit()
        await session.refresh(emp)

        # Publish event
        await event_bus.publish(DomainEvent(
            event_type=EventTypes.EMPLOYEE_CREATED,
            tenant_id=tenant_id,
            actor_id=actor_id,
            payload={"id": emp.id, "name": emp.full_name, "email": emp.email, "department_id": emp.department_id}
        ))
        return emp

    @staticmethod
    async def get_employee_by_id(session: AsyncSession, employee_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        stmt = (
            select(Employee)
            .options(selectinload(Employee.department), selectinload(Employee.manager))
            .where(Employee.id == employee_id, Employee.tenant_id == tenant_id)
        )
        res = await session.execute(stmt)
        emp = res.scalar_one_or_none()
        if not emp:
            return None

        emp_dict = emp.to_dict()
        emp_dict["full_name"] = emp.full_name
        emp_dict["department_name"] = emp.department.name if emp.department else "Unassigned"
        emp_dict["manager_name"] = emp.manager.full_name if emp.manager else "None"
        return emp_dict

    @staticmethod
    async def list_employees(
        session: AsyncSession,
        tenant_id: str,
        department_id: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(Employee)
            .options(selectinload(Employee.department), selectinload(Employee.manager))
            .where(Employee.tenant_id == tenant_id, Employee.is_active == True)
        )
        if department_id:
            stmt = stmt.where(Employee.department_id == department_id)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                (Employee.first_name.ilike(pattern)) |
                (Employee.last_name.ilike(pattern)) |
                (Employee.email.ilike(pattern)) |
                (Employee.designation.ilike(pattern))
            )

        stmt = stmt.order_by(Employee.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        employees = result.scalars().all()

        output = []
        for emp in employees:
            item = emp.to_dict()
            item["full_name"] = emp.full_name
            item["department_name"] = emp.department.name if emp.department else "Unassigned"
            item["manager_name"] = emp.manager.full_name if emp.manager else "None"
            output.append(item)
        return output

    @staticmethod
    async def build_org_chart(session: AsyncSession, tenant_id: str) -> List[Dict[str, Any]]:
        """Constructs an interactive hierarchical Org Chart tree."""
        stmt = select(Employee).options(selectinload(Employee.department)).where(
            Employee.tenant_id == tenant_id,
            Employee.status == EmployeeStatus.ACTIVE
        )
        result = await session.execute(stmt)
        all_emps = result.scalars().all()

        # Build lookup table
        node_map: Dict[str, Dict[str, Any]] = {}
        for emp in all_emps:
            node_map[emp.id] = {
                "id": emp.id,
                "name": emp.full_name,
                "title": emp.designation,
                "department": emp.department.name if emp.department else "General",
                "email": emp.email,
                "avatar": f"https://api.dicebear.com/7.x/bottts/svg?seed={emp.email}",
                "manager_id": emp.manager_id,
                "reports": []
            }

        roots = []
        for emp_id, node in node_map.items():
            mgr_id = node.get("manager_id")
            if mgr_id and mgr_id in node_map and mgr_id != emp_id:
                node_map[mgr_id]["reports"].append(node)
            else:
                roots.append(node)

        return roots
