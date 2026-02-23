"""Compliance Incident War Room models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class IncidentSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentPhase(str, Enum):
    DETECTED = "detected"
    TRIAGING = "triaging"
    RESPONDING = "responding"
    NOTIFYING = "notifying"
    POST_MORTEM = "post_mortem"
    CLOSED = "closed"


@dataclass
class TimelineEntry:
    timestamp: datetime | None = None
    actor: str = ""
    action: str = ""
    details: str = ""


@dataclass
class WarRoomIncident:
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    phase: IncidentPhase = IncidentPhase.DETECTED
    description: str = ""
    regulation: str = ""
    breach_detected_at: datetime | None = None
    notification_deadline: datetime | None = None
    timeline_events: list[TimelineEntry] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    stakeholders: list[str] = field(default_factory=list)
    communication_log: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    closed_at: datetime | None = None


@dataclass
class PostMortem:
    id: UUID = field(default_factory=uuid4)
    incident_id: UUID | None = None
    root_cause: str = ""
    impact_summary: str = ""
    lessons_learned: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass
class WarRoomStats:
    total_incidents: int = 0
    by_severity: dict[str, int] = field(default_factory=dict)
    by_phase: dict[str, int] = field(default_factory=dict)
    avg_resolution_hours: float = 0.0
    post_mortems_generated: int = 0
