"""Incident Response Compliance Playbook models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class IncidentType(str, Enum):
    DATA_BREACH = "data_breach"
    API_OUTAGE = "api_outage"
    INSIDER_THREAT = "insider_threat"
    RANSOMWARE = "ransomware"
    VENDOR_COMPROMISE = "vendor_compromise"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class IncidentSeverity(str, Enum):
    P1_CRITICAL = "p1_critical"
    P2_HIGH = "p2_high"
    P3_MEDIUM = "p3_medium"
    P4_LOW = "p4_low"


class PlaybookStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class IncidentStatus(str, Enum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONTAINING = "containing"
    ERADICATING = "eradicating"
    RECOVERING = "recovering"
    CLOSED = "closed"


@dataclass
class Playbook:
    """An incident response playbook."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    incident_type: IncidentType = IncidentType.DATA_BREACH
    description: str = ""
    steps: list[dict] = field(default_factory=list)
    notification_requirements: list[dict] = field(default_factory=list)
    evidence_checklist: list[str] = field(default_factory=list)
    status: PlaybookStatus = PlaybookStatus.ACTIVE
    jurisdictions: list[str] = field(default_factory=list)
    created_at: datetime | None = None


@dataclass
class Incident:
    """An active incident being managed."""

    id: UUID = field(default_factory=uuid4)
    playbook_id: UUID = field(default_factory=uuid4)
    incident_type: IncidentType = IncidentType.DATA_BREACH
    severity: IncidentSeverity = IncidentSeverity.P3_MEDIUM
    title: str = ""
    description: str = ""
    status: IncidentStatus = IncidentStatus.DETECTED
    affected_data_subjects: int = 0
    jurisdictions_affected: list[str] = field(default_factory=list)
    timeline: list[dict] = field(default_factory=list)
    evidence_collected: list[str] = field(default_factory=list)
    notifications_sent: list[dict] = field(default_factory=list)
    started_at: datetime | None = None
    resolved_at: datetime | None = None


@dataclass
class NotificationRequirement:
    """A notification requirement for an incident."""

    jurisdiction: str = ""
    authority: str = ""
    deadline_hours: int = 72
    template: str = ""
    data_required: list[str] = field(default_factory=list)


@dataclass
class IncidentReport:
    """A post-incident compliance report."""

    id: UUID = field(default_factory=uuid4)
    incident_id: UUID = field(default_factory=uuid4)
    incident_type: str = ""
    severity: str = ""
    total_duration_hours: float = 0.0
    notifications_compliant: bool = False
    evidence_complete: bool = False
    timeline: list[dict] = field(default_factory=list)
    lessons_learned: list[str] = field(default_factory=list)
    generated_at: datetime | None = None
