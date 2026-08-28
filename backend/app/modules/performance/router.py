"""
NexusTalent Performance Router
REST API endpoints for OKRs, Key Results tracking, and 9-Box Calibration Matrix.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, UserContext, require_permission
from backend.app.modules.performance.schemas import ObjectiveCreate, KeyResultUpdate, NineBoxSubmit
from backend.app.modules.performance.service import PerformanceService

router = APIRouter(prefix="/performance", tags=["Performance Management & 9-Box Matrix"])


@router.post("/objectives", status_code=status.HTTP_201_CREATED)
async def create_objective(
    data: ObjectiveCreate,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("performance:write"))
):
    obj = await PerformanceService.create_objective(db, data, user.tenant_id)
    return obj.to_dict()


@router.get("/objectives")
async def list_objectives(
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("performance:read"))
):
    return await PerformanceService.list_objectives(db, user.tenant_id)


@router.post("/key-results/{kr_id}/progress")
async def update_key_result_progress(
    kr_id: str,
    data: KeyResultUpdate,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("performance:self_review"))
):
    try:
        return await PerformanceService.update_key_result_progress(db, kr_id, data.current_value, user.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/nine-box", status_code=status.HTTP_201_CREATED)
async def submit_nine_box(
    data: NineBoxSubmit,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("performance:calibrate"))
):
    assessment = await PerformanceService.submit_nine_box(db, data, user.user_id, user.tenant_id)
    return assessment.to_dict()


@router.get("/nine-box-matrix")
async def get_nine_box_matrix(
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("performance:read"))
):
    return await PerformanceService.get_nine_box_matrix(db, user.tenant_id)
