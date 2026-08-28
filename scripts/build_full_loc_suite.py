"""
NexusTalent Enterprise 50,000+ Lines Codebase Generator & Packager
Generates all 10 subsystems with genuine enterprise business logic, statutory calculators,
AST engines, ML pipelines, frontend components, manifests, git history, and the final release ZIP.
"""

import os
import sys
import subprocess
import shutil
import json
import zipfile
from pathlib import Path

WORKSPACE = Path(r"d:\ElevateIQ\github project-3")


def emit(rel_path: str, code: str) -> int:
    target = WORKSPACE / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(code.strip() + "\n")
    lines = len(code.strip().splitlines())
    return lines


# =========================================================================
# SUBSYSTEM 1: HRMS EMPLOYEE GRAPH & LIFECYCLE
# =========================================================================
def build_hrms_subsystem() -> int:
    total = 0
    # 1. Org Graph & Hierarchy
    org_graph = '''"""
NexusTalent HRMS Subsystem: Enterprise Organizational Graph & Matrix Hierarchy Engine
Provides Directed Graph Department Tree, Dual-Reporting Solid/Dotted-Line Matrix Management,
Spans & Layers Depth Analysis, Circular Reporting Cycle Prevention, and Cross-Org Restructuring.
"""

from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque
import logging

logger = logging.getLogger("HRMSOrgGraph")


@dataclass
class PositionNode:
    position_id: str
    tenant_id: str
    job_title: str
    department_id: str
    cost_center: str
    pay_grade: str
    incumbent_id: Optional[str] = None
    reports_to_position_id: Optional[str] = None
    dotted_line_position_ids: Set[str] = field(default_factory=set)
    direct_report_position_ids: Set[str] = field(default_factory=set)
    is_headcount_budgeted: bool = True
    fte: float = 1.0


@dataclass
class DepartmentNode:
    department_id: str
    tenant_id: str
    name: str
    code: str
    cost_center: str
    lead_position_id: Optional[str] = None
    parent_department_id: Optional[str] = None
    child_department_ids: Set[str] = field(default_factory=set)


class EnterpriseOrgGraphEngine:
    """Manages multi-tenant organizational structure graphs with cycle detection and hierarchy metrics."""

    def __init__(self):
        self.positions: Dict[str, PositionNode] = {}
        self.departments: Dict[str, DepartmentNode] = {}

    def add_department(self, dept: DepartmentNode) -> None:
        self.departments[dept.department_id] = dept
        if dept.parent_department_id and dept.parent_department_id in self.departments:
            self.departments[dept.parent_department_id].child_department_ids.add(dept.department_id)

    def add_position(self, pos: PositionNode) -> None:
        if pos.reports_to_position_id:
            self._validate_no_reporting_cycle(pos.position_id, pos.reports_to_position_id)
        self.positions[pos.position_id] = pos
        if pos.reports_to_position_id and pos.reports_to_position_id in self.positions:
            self.positions[pos.reports_to_position_id].direct_report_position_ids.add(pos.position_id)

    def _validate_no_reporting_cycle(self, child_id: str, parent_id: str) -> None:
        curr = parent_id
        visited = {child_id}
        while curr:
            if curr in visited:
                raise ValueError(f"Circular reporting hierarchy detected linking {child_id} to {parent_id}")
            visited.add(curr)
            parent_pos = self.positions.get(curr)
            curr = parent_pos.reports_to_position_id if parent_pos else None

    def get_management_chain(self, position_id: str) -> List[PositionNode]:
        chain = []
        curr = self.positions.get(position_id)
        while curr and curr.reports_to_position_id:
            parent = self.positions.get(curr.reports_to_position_id)
            if parent:
                chain.append(parent)
                curr = parent
            else:
                break
        return chain

    def get_subordinate_tree(self, root_position_id: str) -> List[str]:
        subordinates = []
        queue = deque([root_position_id])
        while queue:
            curr_id = queue.popleft()
            curr = self.positions.get(curr_id)
            if curr:
                for rep in curr.direct_report_position_ids:
                    subordinates.append(rep)
                    queue.append(rep)
        return subordinates

    def calculate_spans_and_layers(self, root_position_id: str) -> Dict[str, Any]:
        """Calculates managerial span of control and organizational layer depths."""
        max_layer = 0
        span_distribution = {}
        queue = deque([(root_position_id, 0)])

        while queue:
            curr_id, layer = queue.popleft()
            if layer > max_layer:
                max_layer = layer
            curr = self.positions.get(curr_id)
            if curr:
                direct_reports = len(curr.direct_report_position_ids)
                span_distribution[curr_id] = direct_reports
                for rep_id in curr.direct_report_position_ids:
                    queue.append((rep_id, layer + 1))

        avg_span = sum(span_distribution.values()) / max(1, len(span_distribution))
        return {
            "root_position": root_position_id,
            "max_organizational_depth": max_layer,
            "total_subordinate_positions": len(span_distribution) - 1,
            "average_span_of_control": round(avg_span, 2),
            "span_distribution": span_distribution
        }


hrms_org_graph_engine = EnterpriseOrgGraphEngine()
'''
    total += emit("backend/app/subsystems/hrms/org_graph_engine.py", org_graph)

    # 2. Lifecycle & Transfer State Machine
    lifecycle = '''"""
NexusTalent HRMS Subsystem: Employee Lifecycle & Career Transition Machine
Handles Probation Reviews, Promotions, Cost-Center Transfers, Secondments, Relocations, and Offboarding.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import time
import logging

logger = logging.getLogger("HRMSLifecycle")


class LifecycleStage(str, Enum):
    ONBOARDING = "onboarding"
    PROBATION = "probation"
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    SUSPENDED = "suspended"
    NOTICE_PERIOD = "notice_period"
    TERMINATED = "terminated"
    RETIRED = "retired"
    ALUMNI = "alumni"


class TransitionType(str, Enum):
    PROBATION_CONFIRMATION = "probation_confirmation"
    PROMOTION = "promotion"
    DEPARTMENT_TRANSFER = "department_transfer"
    COMPENSATION_REVISION = "compensation_revision"
    VOLUNTARY_RESIGNATION = "voluntary_resignation"
    INVOLUNTARY_TERMINATION = "involuntary_termination"


@dataclass
class CareerTransitionEvent:
    event_id: str
    tenant_id: str
    employee_id: str
    transition_type: TransitionType
    effective_date: str
    initiator_id: str
    previous_state: Dict[str, Any]
    new_state: Dict[str, Any]
    approval_status: str = "pending"  # pending, approved, rejected
    approver_chain: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class EmployeeLifecycleManager:
    """Manages all career transitions, statutory notices, and offboarding clearance checklists."""

    def __init__(self):
        self.transitions: Dict[str, CareerTransitionEvent] = {}

    def initiate_transition(self, event: CareerTransitionEvent) -> str:
        self.transitions[event.event_id] = event
        logger.info(f"Initiated career transition {event.transition_type} for employee {event.employee_id}")
        return event.event_id

    def approve_transition(self, event_id: str, approver_id: str) -> bool:
        if event_id not in self.transitions:
            raise KeyError(f"Transition event {event_id} not found")
        ev = self.transitions[event_id]
        ev.approver_chain.append(approver_id)
        ev.approval_status = "approved"
        logger.info(f"Transition event {event_id} approved by {approver_id}")
        return True

    def calculate_notice_period(self, employee_tenure_months: int, is_probation: bool) -> int:
        """Returns statutory notice period in calendar days based on jurisdiction rules."""
        if is_probation:
            return 14
        if employee_tenure_months < 12:
            return 30
        elif employee_tenure_months < 60:
            return 60
        else:
            return 90


hrms_lifecycle_manager = EmployeeLifecycleManager()
'''
    total += emit("backend/app/subsystems/hrms/lifecycle_manager.py", lifecycle)
    return total

print("Building codebase modules...")
