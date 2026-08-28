"""
NexusTalent Universal Workflow & State Machine Engine
Reusable Finite State Machine & Multi-tier Approval Engine
Powering Leaves, Requisitions, Hiring Stages, Expense Claims & Payroll Approval
"""

from typing import Dict, List, Any, Optional, Callable, Awaitable, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
import enum
import logging

logger = logging.getLogger("WorkflowEngine")


class TransitionError(Exception):
    """Raised when an illegal or unauthorized state transition is attempted."""
    pass


@dataclass
class TransitionRecord:
    from_state: str
    to_state: str
    actor_id: str
    actor_role: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    comment: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransitionRule:
    from_state: str
    to_state: str
    allowed_roles: Set[str] = field(default_factory=lambda: {"*"})
    guard: Optional[Callable[[Dict[str, Any]], bool]] = None
    on_success: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
    description: str = ""


class WorkflowDefinition:
    """Configurable workflow structure for a given domain entity."""
    
    def __init__(
        self,
        name: str,
        initial_state: str,
        terminal_states: Set[str],
        transitions: List[TransitionRule]
    ):
        self.name = name
        self.initial_state = initial_state
        self.terminal_states = terminal_states
        self.transitions: Dict[str, List[TransitionRule]] = {}
        
        for rule in transitions:
            if rule.from_state not in self.transitions:
                self.transitions[rule.from_state] = []
            self.transitions[rule.from_state].append(rule)

    def can_transition(
        self,
        current_state: str,
        target_state: str,
        actor_roles: Set[str],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        rules = self.transitions.get(current_state, [])
        for rule in rules:
            if rule.to_state == target_state:
                # Role check
                if "*" not in rule.allowed_roles and not (actor_roles & rule.allowed_roles):
                    continue
                # Guard check
                if rule.guard and not rule.guard(context or {}):
                    continue
                return True
        return False

    async def execute_transition(
        self,
        current_state: str,
        target_state: str,
        actor_id: str,
        actor_roles: Set[str],
        context: Optional[Dict[str, Any]] = None,
        comment: Optional[str] = None
    ) -> TransitionRecord:
        rules = self.transitions.get(current_state, [])
        matched_rule: Optional[TransitionRule] = None

        for rule in rules:
            if rule.to_state == target_state:
                if "*" in rule.allowed_roles or (actor_roles & rule.allowed_roles):
                    if not rule.guard or rule.guard(context or {}):
                        matched_rule = rule
                        break

        if not matched_rule:
            raise TransitionError(
                f"Transition '{current_state}' -> '{target_state}' is not permitted for roles {actor_roles} in workflow '{self.name}'."
            )

        # Execute callback hook if present
        if matched_rule.on_success:
            await matched_rule.on_success(context or {})

        record = TransitionRecord(
            from_state=current_state,
            to_state=target_state,
            actor_id=actor_id,
            actor_role=list(actor_roles)[0] if actor_roles else "system",
            comment=comment,
            metadata=context or {}
        )
        return record


# Predefined Universal Workflows

LEAVE_REQUEST_WORKFLOW = WorkflowDefinition(
    name="leave_request",
    initial_state="draft",
    terminal_states={"approved", "rejected", "cancelled"},
    transitions=[
        TransitionRule(from_state="draft", to_state="submitted", allowed_roles={"employee", "hr_admin"}),
        TransitionRule(from_state="submitted", to_state="manager_approved", allowed_roles={"hiring_manager", "hr_admin", "superadmin"}),
        TransitionRule(from_state="submitted", to_state="rejected", allowed_roles={"hiring_manager", "hr_admin", "superadmin"}),
        TransitionRule(from_state="submitted", to_state="cancelled", allowed_roles={"employee", "hr_admin"}),
        TransitionRule(from_state="manager_approved", to_state="approved", allowed_roles={"hr_admin", "superadmin"}),
        TransitionRule(from_state="manager_approved", to_state="rejected", allowed_roles={"hr_admin", "superadmin"}),
    ]
)

RECRUITMENT_PIPELINE_WORKFLOW = WorkflowDefinition(
    name="recruitment_candidate_pipeline",
    initial_state="sourced",
    terminal_states={"hired", "rejected", "withdrawn"},
    transitions=[
        TransitionRule(from_state="sourced", to_state="applied", allowed_roles={"recruiter", "hr_admin", "superadmin"}),
        TransitionRule(from_state="applied", to_state="screening", allowed_roles={"recruiter", "hr_admin", "superadmin"}),
        TransitionRule(from_state="screening", to_state="interviewing", allowed_roles={"recruiter", "hiring_manager", "hr_admin", "superadmin"}),
        TransitionRule(from_state="interviewing", to_state="tech_assessment", allowed_roles={"recruiter", "hiring_manager", "hr_admin", "superadmin"}),
        TransitionRule(from_state="tech_assessment", to_state="offer_extended", allowed_roles={"hr_admin", "hiring_manager", "superadmin"}),
        TransitionRule(from_state="offer_extended", to_state="offer_accepted", allowed_roles={"recruiter", "hr_admin", "superadmin"}),
        TransitionRule(from_state="offer_accepted", to_state="hired", allowed_roles={"hr_admin", "superadmin"}),
        
        # Universal drop-offs
        TransitionRule(from_state="sourced", to_state="rejected", allowed_roles={"recruiter", "hr_admin", "superadmin"}),
        TransitionRule(from_state="applied", to_state="rejected", allowed_roles={"recruiter", "hr_admin", "superadmin"}),
        TransitionRule(from_state="screening", to_state="rejected", allowed_roles={"recruiter", "hr_admin", "superadmin"}),
        TransitionRule(from_state="interviewing", to_state="rejected", allowed_roles={"recruiter", "hiring_manager", "hr_admin", "superadmin"}),
        TransitionRule(from_state="tech_assessment", to_state="rejected", allowed_roles={"recruiter", "hiring_manager", "hr_admin", "superadmin"}),
        TransitionRule(from_state="offer_extended", to_state="withdrawn", allowed_roles={"recruiter", "hr_admin", "superadmin"}),
        TransitionRule(from_state="offer_extended", to_state="rejected", allowed_roles={"hr_admin", "superadmin"}),
    ]
)

PAYROLL_CYCLE_WORKFLOW = WorkflowDefinition(
    name="payroll_cycle",
    initial_state="draft",
    terminal_states={"disbursed", "cancelled"},
    transitions=[
        TransitionRule(from_state="draft", to_state="calculated", allowed_roles={"payroll_specialist", "hr_admin", "superadmin"}),
        TransitionRule(from_state="calculated", to_state="under_audit", allowed_roles={"payroll_specialist", "hr_admin", "superadmin"}),
        TransitionRule(from_state="under_audit", to_state="approved", allowed_roles={"hr_admin", "superadmin"}),
        TransitionRule(from_state="under_audit", to_state="rejected", allowed_roles={"hr_admin", "superadmin"}),
        TransitionRule(from_state="approved", to_state="disbursed", allowed_roles={"hr_admin", "superadmin"}),
        TransitionRule(from_state="draft", to_state="cancelled", allowed_roles={"hr_admin", "superadmin"}),
    ]
)

HELPDESK_TICKET_WORKFLOW = WorkflowDefinition(
    name="helpdesk_ticket",
    initial_state="open",
    terminal_states={"resolved", "closed", "cancelled"},
    transitions=[
        TransitionRule(from_state="open", to_state="in_progress", allowed_roles={"hr_admin", "superadmin", "hiring_manager"}),
        TransitionRule(from_state="in_progress", to_state="waiting_on_employee", allowed_roles={"hr_admin", "superadmin"}),
        TransitionRule(from_state="waiting_on_employee", to_state="in_progress", allowed_roles={"employee", "hr_admin", "superadmin"}),
        TransitionRule(from_state="in_progress", to_state="resolved", allowed_roles={"hr_admin", "superadmin"}),
        TransitionRule(from_state="resolved", to_state="closed", allowed_roles={"employee", "hr_admin", "superadmin"}),
        TransitionRule(from_state="open", to_state="cancelled", allowed_roles={"employee", "hr_admin", "superadmin"}),
    ]
)

WORKFLOW_REGISTRY: Dict[str, WorkflowDefinition] = {
    "leave_request": LEAVE_REQUEST_WORKFLOW,
    "recruitment_pipeline": RECRUITMENT_PIPELINE_WORKFLOW,
    "payroll_cycle": PAYROLL_CYCLE_WORKFLOW,
    "helpdesk_ticket": HELPDESK_TICKET_WORKFLOW
}
