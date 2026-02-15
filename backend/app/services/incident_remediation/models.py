"""Incident-to-Compliance Auto-Remediation models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID


class IncidentSeverity(str, Enum):
    """Incident severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IncidentSource(str, Enum):
    """Source of the incident."""

    SPLUNK = "splunk"
    DATADOG = "datadog"
    ELASTIC = "elastic"
    PAGERDUTY = "pagerduty"
    SENTRY = "sentry"
    MANUAL = "manual"


class RemediationStatus(str, Enum):
    """Remediation workflow status."""

    DETECTED = "detected"
    ANALYZING = "analyzing"
    REMEDIATING = "remediating"
    PR_CREATED = "pr_created"
    AWAITING_APPROVAL = "awaiting_approval"
    MERGED = "merged"
    VERIFIED = "verified"
    CLOSED = "closed"


@dataclass
class ComplianceIncident:
    """A security incident mapped to compliance violations."""

    id: UUID
    title: str
    description: str
    source: IncidentSource
    severity: IncidentSeverity
    status: RemediationStatus = RemediationStatus.DETECTED
    affected_frameworks: list[str] = field(default_factory=list)
    affected_controls: list[str] = field(default_factory=list)
    affected_files: list[str] = field(default_factory=list)
    cvss_score: float = 0.0
    compliance_impact_score: float = 0.0
    remediation_pr_url: str = ""
    evidence_collected: bool = False
    breach_notification_required: bool = False
    notification_deadline_hours: int = 72
    detected_at: datetime = field(default_factory=datetime.utcnow)
    remediated_at: datetime | None = None


@dataclass
class RemediationAction:
    """An auto-generated remediation action."""

    id: UUID
    incident_id: UUID
    action_type: str
    description: str
    file_path: str = ""
    code_patch: str = ""
    priority: int = 1
    estimated_effort_minutes: int = 30
    automated: bool = True
    applied: bool = False


@dataclass
class BreachNotification:
    """Auto-generated breach notification draft."""

    id: UUID
    incident_id: UUID
    regulation: str
    authority: str
    deadline: datetime
    draft_text: str = ""
    affected_individuals_count: int = 0
    data_categories: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    sent: bool = False
