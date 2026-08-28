"""
NexusTalent Helpdesk Schemas
Pydantic v2 DTOs for Internal HR CRM Tickets, Comments & Knowledge Base.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from backend.app.modules.helpdesk.models import TicketPriority, TicketCategory, TicketStatus


class TicketCreate(BaseModel):
    employee_id: str
    category: TicketCategory = TicketCategory.POLICY_INQUIRY
    priority: TicketPriority = TicketPriority.MEDIUM
    subject: str
    description: str


class TicketCommentCreate(BaseModel):
    author_id: str
    author_name: str
    message: str
    is_internal_note: bool = False


class TicketStatusUpdate(BaseModel):
    status: TicketStatus
    comment: Optional[str] = None


class KBArticleCreate(BaseModel):
    title: str
    category: str
    slug: str
    content: str
