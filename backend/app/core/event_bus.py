"""
NexusTalent Asynchronous Event Bus
Decouples Core HRMS, Recruitment, Payroll, Attendance & Helpdesk Subsystems.
"""

from typing import Dict, List, Callable, Awaitable, Any, Optional
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger("EventBus")


@dataclass
class DomainEvent:
    event_type: str
    tenant_id: str
    actor_id: str
    payload: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_id: Optional[str] = None


EventHandler = Callable[[DomainEvent], Awaitable[None]]


class AsyncEventBus:
    """In-memory event bus with Kafka-compatible event contract."""

    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed handler to event: {event_type}")

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._subscribers.get(event.event_type, [])
        wildcard_handlers = self._subscribers.get("*", [])
        all_handlers = handlers + wildcard_handlers

        if not all_handlers:
            return

        # Execute handlers concurrently
        tasks = [asyncio.create_task(self._safe_execute(h, event)) for h in all_handlers]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_execute(self, handler: EventHandler, event: DomainEvent) -> None:
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Error handling event {event.event_type}: {e}", exc_info=True)


# Global Singleton Event Bus
event_bus = AsyncEventBus()


# Predefined Event Types
class EventTypes:
    # Recruitment
    CANDIDATE_APPLIED = "recruitment.candidate.applied"
    STAGE_TRANSITIONED = "recruitment.stage.transitioned"
    OFFER_RELEASED = "recruitment.offer.released"
    CANDIDATE_HIRED = "recruitment.candidate.hired"

    # HRMS
    EMPLOYEE_CREATED = "hrms.employee.created"
    EMPLOYEE_PROMOTED = "hrms.employee.promoted"
    EMPLOYEE_TERMINATED = "hrms.employee.terminated"

    # Attendance & Leaves
    ATTENDANCE_CLOCKED = "attendance.clocked"
    LEAVE_REQUESTED = "attendance.leave.requested"
    LEAVE_APPROVED = "attendance.leave.approved"
    LEAVE_REJECTED = "attendance.leave.rejected"

    # Payroll
    PAYROLL_CALCULATED = "payroll.calculated"
    PAYSLIP_GENERATED = "payroll.payslip.generated"
    PAYROLL_DISBURSED = "payroll.disbursed"

    # Performance
    REVIEW_CYCLE_LAUNCHED = "performance.cycle.launched"
    FEEDBACK_SUBMITTED = "performance.feedback.submitted"

    # Helpdesk
    TICKET_CREATED = "helpdesk.ticket.created"
    TICKET_RESOLVED = "helpdesk.ticket.resolved"
    SLA_BREACHED = "helpdesk.sla.breached"
