"""
NexusTalent Helpdesk Models
Internal HR Service Delivery, Ticket Queues, SLA Escalations & Knowledge Base
"""

from datetime import datetime, date, timezone
from typing import Optional, List
from sqlalchemy import String, Date, DateTime, Float, ForeignKey, Integer, Text, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
import enum


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketCategory(str, enum.Enum):
    PAYROLL = "payroll"
    BENEFITS_INSURANCE = "benefits_insurance"
    LEAVE_ATTENDANCE = "leave_attendance"
    IT_ASSETS = "it_assets"
    WORKPLACE_RELATIONS = "workplace_relations"
    POLICY_INQUIRY = "policy_inquiry"
    GENERAL = "general"


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_EMPLOYEE = "waiting_employee"
    RESOLVED = "resolved"
    CLOSED = "closed"


class HelpdeskTicket(Base):
    """Employee support request and internal service ticket."""
    __tablename__ = "helpdesk_tickets"

    ticket_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("hrms_employees.id"), index=True)
    category: Mapped[TicketCategory] = mapped_column(String(40), default=TicketCategory.POLICY_INQUIRY)
    priority: Mapped[TicketPriority] = mapped_column(String(20), default=TicketPriority.MEDIUM)
    subject: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[TicketStatus] = mapped_column(String(30), default=TicketStatus.OPEN, index=True)
    
    # SLA & Assignee
    assigned_to_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("hrms_employees.id"), nullable=True)
    sla_target_hours: Mapped[int] = mapped_column(Integer, default=24)
    is_sla_breached: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    employee: Mapped["backend.app.modules.hrms.models.Employee"] = relationship("Employee", foreign_keys=[employee_id])
    assignee: Mapped[Optional["backend.app.modules.hrms.models.Employee"]] = relationship("Employee", foreign_keys=[assigned_to_id])
    comments: Mapped[List["TicketComment"]] = relationship("TicketComment", back_populates="ticket")


class TicketComment(Base):
    """Threaded conversation message on a ticket."""
    __tablename__ = "helpdesk_ticket_comments"

    ticket_id: Mapped[str] = mapped_column(String(36), ForeignKey("helpdesk_tickets.id"), index=True)
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("hrms_employees.id"))
    author_name: Mapped[str] = mapped_column(String(100))
    is_internal_note: Mapped[bool] = mapped_column(Boolean, default=False)
    message: Mapped[str] = mapped_column(Text)

    ticket: Mapped[HelpdeskTicket] = relationship("HelpdeskTicket", back_populates="comments")


class KnowledgeBaseArticle(Base):
    """Self-service HR Policy & FAQ Article."""
    __tablename__ = "helpdesk_kb_articles"

    title: Mapped[str] = mapped_column(String(200), index=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    content: Mapped[str] = mapped_column(Text)
    views_count: Mapped[int] = mapped_column(Integer, default=0)
