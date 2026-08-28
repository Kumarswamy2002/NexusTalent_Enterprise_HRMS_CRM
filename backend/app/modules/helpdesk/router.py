"""
NexusTalent Helpdesk Router
REST API endpoints for Internal HR Service Desk, Tickets, and Comments.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, UserContext, require_permission
from backend.app.modules.helpdesk.schemas import (
    TicketCreate, TicketCommentCreate, TicketStatusUpdate, KBArticleCreate
)
from backend.app.modules.helpdesk.service import HelpdeskService

router = APIRouter(prefix="/helpdesk", tags=["Employee Helpdesk (Internal CRM)"])


@router.post("/tickets", status_code=status.HTTP_201_CREATED)
async def create_ticket(
    data: TicketCreate,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("helpdesk:create_ticket"))
):
    ticket = await HelpdeskService.create_ticket(db, data, user.tenant_id)
    return ticket.to_dict()


@router.get("/tickets")
async def list_tickets(
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("helpdesk:read"))
):
    return await HelpdeskService.list_tickets(db, user.tenant_id)


@router.post("/tickets/{ticket_id}/comments", status_code=status.HTTP_201_CREATED)
async def add_comment(
    ticket_id: str,
    data: TicketCommentCreate,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("helpdesk:write"))
):
    try:
        comment = await HelpdeskService.add_comment(db, ticket_id, data, user.tenant_id)
        return comment.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: str,
    data: TicketStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: UserContext = Depends(require_permission("helpdesk:manage"))
):
    try:
        ticket = await HelpdeskService.update_ticket_status(
            session=db,
            ticket_id=ticket_id,
            new_status=data.status,
            tenant_id=user.tenant_id,
            actor_id=user.user_id
        )
        return ticket.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
