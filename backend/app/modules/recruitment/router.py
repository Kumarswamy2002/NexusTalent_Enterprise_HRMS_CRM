"""
NexusTalent Recruitment & Talent CRM Router
REST API endpoints for Job Requisitions, Candidates, Kanban Pipeline, and Scorecards.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, UserContext, require_permission
from backend.app.modules.recruitment.schemas import (
    RequisitionCreate, CandidateCreate, StageTransitionRequest, ScorecardCreate
)
from backend.app.modules.recruitment.service import RecruitmentService
from backend.app.core.workflow_engine import TransitionError

router = APIRouter(prefix="/recruitment", tags=["Recruitment & Talent CRM"])


@router.post("/requisitions", status_code=status.HTTP_201_CREATED)
async def create_requisition(
    data: RequisitionCreate,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("recruitment:write"))
):
    req = await RecruitmentService.create_requisition(db, data, user.tenant_id)
    return req.to_dict()


@router.get("/requisitions")
async def list_requisitions(
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("recruitment:read"))
):
    return await RecruitmentService.list_requisitions(db, user.tenant_id)


@router.post("/candidates", status_code=status.HTTP_201_CREATED)
async def create_candidate(
    data: CandidateCreate,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("recruitment:sourcing"))
):
    cand = await RecruitmentService.create_candidate(db, data, user.tenant_id, user.user_id)
    return cand.to_dict()


@router.get("/kanban/{requisition_id}")
async def get_kanban_board(
    requisition_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("recruitment:read"))
):
    return await RecruitmentService.get_kanban_board(db, requisition_id, user.tenant_id)


@router.post("/applications/{application_id}/transition")
async def transition_stage(
    application_id: str,
    data: StageTransitionRequest,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("recruitment:write"))
):
    try:
        app = await RecruitmentService.transition_stage(
            session=db,
            application_id=application_id,
            target_stage=data.target_stage,
            actor_id=user.user_id,
            actor_roles=user.roles,
            tenant_id=user.tenant_id,
            rejection_reason=data.rejection_reason
        )
        stage_val = app.stage.value if hasattr(app.stage, "value") else str(app.stage)
        return {"status": "success", "application_id": app.id, "current_stage": stage_val}
    except TransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/applications/{application_id}/scorecards", status_code=status.HTTP_201_CREATED)
async def submit_scorecard(
    application_id: str,
    data: ScorecardCreate,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("recruitment:scorecard"))
):
    scorecard = await RecruitmentService.submit_scorecard(
        session=db,
        application_id=application_id,
        data=data,
        tenant_id=user.tenant_id,
        actor_id=user.user_id
    )
    return scorecard.to_dict()
