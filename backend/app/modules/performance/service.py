"""
NexusTalent Performance Service Layer
Cascading OKR Tracking, Automated Progress Rollup & 9-Box Calibration Grid Engine.
"""

from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload

from backend.app.modules.performance.models import (
    Objective, KeyResult, NineBoxAssessment, OKRLevel, GoalStatus
)
from backend.app.modules.performance.schemas import ObjectiveCreate, KeyResultUpdate, NineBoxSubmit
from backend.app.modules.performance.nine_box_engine import NineBoxEngine
from backend.app.modules.hrms.models import Employee


class PerformanceService:

    @staticmethod
    async def create_objective(session: AsyncSession, data: ObjectiveCreate, tenant_id: str) -> Objective:
        obj = Objective(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            title=data.title,
            level=data.level,
            owner_id=data.owner_id,
            department_id=data.department_id,
            quarter=data.quarter,
            progress_percentage=0.0,
            status=GoalStatus.IN_PROGRESS
        )
        session.add(obj)
        await session.flush()

        for kr_data in data.key_results:
            kr = KeyResult(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                objective_id=obj.id,
                title=kr_data.title,
                target_value=kr_data.target_value,
                current_value=0.0,
                metric_unit=kr_data.metric_unit
            )
            session.add(kr)

        await session.commit()
        await session.refresh(obj)
        return obj

    @staticmethod
    async def list_objectives(session: AsyncSession, tenant_id: str) -> List[Dict[str, Any]]:
        stmt = (
            select(Objective)
            .options(
                selectinload(Objective.key_results),
                selectinload(Objective.owner)
            )
            .where(Objective.tenant_id == tenant_id)
        )
        res = await session.execute(stmt)
        objectives = res.scalars().all()

        output = []
        for obj in objectives:
            d = obj.to_dict()
            d["owner_name"] = obj.owner.full_name if obj.owner else "Company"
            d["key_results"] = [kr.to_dict() for kr in obj.key_results]
            output.append(d)
        return output

    @staticmethod
    async def update_key_result_progress(
        session: AsyncSession,
        key_result_id: str,
        current_value: float,
        tenant_id: str
    ) -> Dict[str, Any]:
        stmt = (
            select(KeyResult)
            .options(selectinload(KeyResult.objective).selectinload(Objective.key_results))
            .where(KeyResult.id == key_result_id, KeyResult.tenant_id == tenant_id)
        )
        res = await session.execute(stmt)
        kr = res.scalar_one_or_none()
        if not kr:
            raise ValueError("Key result not found.")

        kr.current_value = current_value
        obj = kr.objective

        if obj.key_results:
            total_pct = sum([min(100.0, (k.current_value / k.target_value) * 100.0) for k in obj.key_results if k.target_value > 0])
            obj.progress_percentage = round(total_pct / len(obj.key_results), 1)
            if obj.progress_percentage >= 100.0:
                obj.status = GoalStatus.COMPLETED
            elif obj.progress_percentage > 60.0:
                obj.status = GoalStatus.ON_TRACK
            else:
                obj.status = GoalStatus.IN_PROGRESS

        await session.commit()
        return {"status": "success", "objective_progress": obj.progress_percentage}

    @staticmethod
    async def submit_nine_box(
        session: AsyncSession,
        data: NineBoxSubmit,
        reviewer_id: str,
        tenant_id: str
    ) -> NineBoxAssessment:
        classification = NineBoxEngine.classify(data.performance_score, data.potential_score)

        assessment = NineBoxAssessment(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            employee_id=data.employee_id,
            reviewer_id=reviewer_id,
            performance_score=data.performance_score,
            potential_score=data.potential_score,
            box_category=classification["category"],
            notes=data.notes
        )
        session.add(assessment)
        await session.commit()
        await session.refresh(assessment)
        return assessment

    @staticmethod
    async def get_nine_box_matrix(session: AsyncSession, tenant_id: str) -> Dict[str, Any]:
        """Returns employees grouped into the 9-Box Grid layout."""
        stmt = (
            select(NineBoxAssessment)
            .options(selectinload(NineBoxAssessment.employee).selectinload(Employee.department))
            .where(NineBoxAssessment.tenant_id == tenant_id)
        )
        res = await session.execute(stmt)
        assessments = res.scalars().all()

        grid: Dict[str, List[Dict[str, Any]]] = {}
        for key, meta in NineBoxEngine.MATRIX_CATEGORIES.items():
            grid[meta["category"]] = []

        for a in assessments:
            cat = a.box_category
            if cat not in grid:
                grid[cat] = []
            grid[cat].append({
                "assessment_id": a.id,
                "employee_id": a.employee_id,
                "name": a.employee.full_name if a.employee else "Unknown",
                "designation": a.employee.designation if a.employee else "-",
                "department": a.employee.department.name if (a.employee and a.employee.department) else "General",
                "performance_score": a.performance_score,
                "potential_score": a.potential_score,
                "notes": a.notes
            })

        return {"matrix": grid, "meta": NineBoxEngine.MATRIX_CATEGORIES}
