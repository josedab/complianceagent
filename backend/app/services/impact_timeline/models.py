"""Regulatory Change Impact Timeline models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class TimelineEventType(str, Enum):
    REGULATION_EFFECTIVE = "regulation_effective"
    ENFORCEMENT_START = "enforcement_start"
    COMPLIANCE_DEADLINE = "compliance_deadline"
    AMENDMENT = "amendment"
    PREDICTED = "predicted"


class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


@dataclass
class TimelineEvent:
    """A regulatory event on the timeline."""
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    event_type: TimelineEventType = TimelineEventType.REGULATION_EFFECTIVE
    framework: str = ""
    jurisdiction: str = ""
    effective_date: datetime | None = None
    days_remaining: int = 0
    impact_score: float = 0.0
    affected_repos: list[str] = field(default_factory=list)
    estimated_effort_hours: float = 0.0
    is_predicted: bool = False
    confidence: float = 1.0


@dataclass
class RemediationTask:
    """Auto-generated task from a timeline event."""
    id: UUID = field(default_factory=uuid4)
    timeline_event_id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: str | None = None
    estimated_hours: float = 0.0
    due_date: datetime | None = None
    created_at: datetime | None = None


@dataclass
class TimelineView:
    """A complete timeline view."""
    events: list[TimelineEvent] = field(default_factory=list)
    tasks: list[RemediationTask] = field(default_factory=list)
    total_events: int = 0
    upcoming_deadlines: int = 0
    overdue_count: int = 0
    total_effort_hours: float = 0.0
