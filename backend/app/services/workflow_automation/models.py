"""Compliance Workflow Automation models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class TriggerType(str, Enum):
    SCORE_DROP = "score_drop"
    VIOLATION_DETECTED = "violation_detected"
    REGULATION_CHANGE = "regulation_change"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    DRIFT_DETECTED = "drift_detected"


class ActionType(str, Enum):
    NOTIFY_SLACK = "notify_slack"
    NOTIFY_EMAIL = "notify_email"
    CREATE_TICKET = "create_ticket"
    TRIGGER_SCAN = "trigger_scan"
    CREATE_PR = "create_pr"
    ESCALATE = "escalate"
    RUN_PIPELINE = "run_pipeline"


class WorkflowStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ERROR = "error"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowTrigger:
    trigger_type: TriggerType = TriggerType.MANUAL
    conditions: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowAction:
    action_type: ActionType = ActionType.NOTIFY_SLACK
    config: dict[str, Any] = field(default_factory=dict)
    order: int = 0


@dataclass
class WorkflowDefinition:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    trigger: WorkflowTrigger = field(default_factory=WorkflowTrigger)
    actions: list[WorkflowAction] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.ACTIVE
    execution_count: int = 0
    last_executed_at: datetime | None = None
    created_at: datetime | None = None


@dataclass
class WorkflowExecution:
    id: UUID = field(default_factory=uuid4)
    workflow_id: UUID = field(default_factory=uuid4)
    status: ExecutionStatus = ExecutionStatus.PENDING
    trigger_data: dict[str, Any] = field(default_factory=dict)
    actions_completed: list[str] = field(default_factory=list)
    error_message: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class WorkflowTemplate:
    id: str = ""
    name: str = ""
    description: str = ""
    trigger_type: str = ""
    actions: list[dict[str, Any]] = field(default_factory=list)
    category: str = ""


@dataclass
class WorkflowStats:
    total_workflows: int = 0
    active_workflows: int = 0
    total_executions: int = 0
    successful_executions: int = 0
    by_trigger_type: dict[str, int] = field(default_factory=dict)
    by_action_type: dict[str, int] = field(default_factory=dict)
