"""
NexusTalent Helpdesk Service Layer
Internal Service Desk CRM, Threaded Conversations, Knowledge Base & SLA Breach Monitor.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.orm import selectinload

from backend.app.modules.helpdesk.models import (
    HelpdeskTicket, TicketComment, KnowledgeBaseArticle,
    TicketStatus, TicketPriority, TicketCategory
)
from backend.app.modules.helpdesk.schemas import (
    TicketCreate, TicketCommentCreate, TicketStatusUpdate, KBArticleCreate
)
from backend.app.modules.hrms.models import Employee
from backend.app.core.event_bus import event_bus, DomainEvent, EventTypes


class HelpdeskService:

    @staticmethod
    async def create_ticket(session: AsyncSession, data: TicketCreate, tenant_id: str) -> HelpdeskTicket:
        count_res = await session.execute(select(func.count(HelpdeskTicket.id)).where(HelpdeskTicket.tenant_id == tenant_id))
        c = count_res.scalar() or 0
        ticket_number = f"TICK-{3001 + c}"

        sla_hours = 8 if data.priority == TicketPriority.URGENT else (24 if data.priority == TicketPriority.HIGH else 48)

        ticket = HelpdeskTicket(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            ticket_number=ticket_number,
            employee_id=data.employee_id,
            category=data.category,
            priority=data.priority,
            subject=data.subject,
            description=data.description,
            status=TicketStatus.OPEN,
            sla_target_hours=sla_hours
        )
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)

        await event_bus.publish(DomainEvent(
            event_type=EventTypes.TICKET_CREATED,
            tenant_id=tenant_id,
            actor_id=data.employee_id,
            payload={"id": ticket.id, "number": ticket.ticket_number, "subject": ticket.subject, "priority": ticket.priority.value}
        ))
        return ticket

    @staticmethod
    async def list_tickets(
        session: AsyncSession,
        tenant_id: str,
        status_filter: Optional[TicketStatus] = None
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(HelpdeskTicket)
            .options(
                selectinload(HelpdeskTicket.employee),
                selectinload(HelpdeskTicket.assignee),
                selectinload(HelpdeskTicket.comments)
            )
            .where(HelpdeskTicket.tenant_id == tenant_id)
        )
        if status_filter:
            stmt = stmt.where(HelpdeskTicket.status == status_filter)

        stmt = stmt.order_by(HelpdeskTicket.created_at.desc())
        res = await session.execute(stmt)
        tickets = res.scalars().all()

        output = []
        for t in tickets:
            d = t.to_dict()
            d["employee_name"] = t.employee.full_name if t.employee else "Unknown"
            d["employee_email"] = t.employee.email if t.employee else ""
            d["assignee_name"] = t.assignee.full_name if t.assignee else "Unassigned"
            d["comments_count"] = len(t.comments)
            output.append(d)
        return output

    @staticmethod
    async def add_comment(
        session: AsyncSession,
        ticket_id: str,
        data: TicketCommentCreate,
        tenant_id: str
    ) -> TicketComment:
        stmt = select(HelpdeskTicket).where(HelpdeskTicket.id == ticket_id, HelpdeskTicket.tenant_id == tenant_id)
        res = await session.execute(stmt)
        ticket = res.scalar_one_or_none()
        if not ticket:
            raise ValueError("Ticket not found.")

        comment = TicketComment(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            author_id=data.author_id,
            author_name=data.author_name,
            message=data.message,
            is_internal_note=data.is_internal_note
        )
        session.add(comment)

        # If waiting on employee, moving to in_progress
        if ticket.status in (TicketStatus.WAITING_ON_EMPLOYEE, TicketStatus.WAITING_EMPLOYEE, "waiting_on_employee", "waiting_employee") and not data.is_internal_note:
            ticket.status = TicketStatus.IN_PROGRESS

        await session.commit()
        await session.refresh(comment)
        return comment

    @staticmethod
    async def update_ticket_status(
        session: AsyncSession,
        ticket_id: str,
        new_status: TicketStatus,
        tenant_id: str,
        actor_id: str
    ) -> HelpdeskTicket:
        stmt = select(HelpdeskTicket).where(HelpdeskTicket.id == ticket_id, HelpdeskTicket.tenant_id == tenant_id)
        res = await session.execute(stmt)
        ticket = res.scalar_one_or_none()
        if not ticket:
            raise ValueError("Ticket not found.")

        ticket.status = new_status
        if new_status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
            ticket.resolved_at = datetime.now(timezone.utc)

        await session.commit()
        await session.refresh(ticket)

        if new_status == TicketStatus.RESOLVED:
            await event_bus.publish(DomainEvent(
                event_type=EventTypes.TICKET_RESOLVED,
                tenant_id=tenant_id,
                actor_id=actor_id,
                payload={"id": ticket.id, "number": ticket.ticket_number}
            ))
        return ticket
