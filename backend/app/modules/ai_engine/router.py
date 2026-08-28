"""
NexusTalent AI & Workforce Intelligence Router
REST API endpoints for Resume Parsing, Match Scores, and Attrition Flight Risk Prediction.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, UserContext, require_permission
from backend.app.modules.ai_engine.resume_parser import SkillMatcher
from backend.app.modules.ai_engine.attrition_predictor import attrition_ai_model
from backend.app.modules.ai_engine.compensation_benchmark import CompensationBenchmarkEngine
from backend.app.modules.hrms.models import Employee

router = APIRouter(prefix="/ai", tags=["AI & Workforce Intelligence"])


class ResumeMatchRequest(BaseModel):
    resume_text: str
    job_description: str
    experience_years: float = 3.0
    min_experience_required: float = 2.0


class AttritionCheckRequest(BaseModel):
    salary_ratio: float = 1.0
    overtime_hours_month: float = 5.0
    tenure_years: float = 2.0
    years_since_last_promotion: float = 1.0
    performance_score: float = 2.5
    is_remote: bool = False


@router.post("/match-resume")
async def match_resume(
    data: ResumeMatchRequest,
    user: UserContext = Depends(require_permission("recruitment:read"))
):
    cand_skills = SkillMatcher.extract_skills_from_text(data.resume_text)
    req_skills = SkillMatcher.extract_skills_from_text(data.job_description)
    
    score_res = SkillMatcher.calculate_match_score(
        candidate_skills=cand_skills,
        required_skills=req_skills,
        experience_years=data.experience_years,
        min_experience_required=data.min_experience_required
    )
    score_res["extracted_candidate_skills"] = cand_skills
    score_res["extracted_job_skills"] = req_skills
    return score_res


@router.post("/attrition-risk")
async def predict_attrition(
    data: AttritionCheckRequest,
    user: UserContext = Depends(require_permission("performance:read"))
):
    return attrition_ai_model.predict_employee_risk(
        salary_ratio=data.salary_ratio,
        overtime_hours_month=data.overtime_hours_month,
        tenure_years=data.tenure_years,
        years_since_last_promotion=data.years_since_last_promotion,
        performance_score=data.performance_score,
        is_remote=data.is_remote
    )


@router.get("/employee-risk/{employee_id}")
async def get_employee_attrition_risk(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("performance:read"))
):
    stmt = select(Employee).where(Employee.id == employee_id, Employee.tenant_id == user.tenant_id)
    res = await db.execute(stmt)
    emp = res.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Analyze compensation benchmark
    comp_analysis = CompensationBenchmarkEngine.analyze_employee_equity(emp.designation, emp.base_annual_salary)
    ratio = comp_analysis["compa_ratio"] / 100.0

    risk = attrition_ai_model.predict_employee_risk(
        salary_ratio=ratio,
        overtime_hours_month=12.0,  # Estimated baseline
        tenure_years=2.5,
        years_since_last_promotion=1.8,
        performance_score=2.6,
        is_remote=emp.is_remote
    )
    risk["employee_name"] = emp.full_name
    risk["designation"] = emp.designation
    risk["compensation_analysis"] = comp_analysis
    return risk
