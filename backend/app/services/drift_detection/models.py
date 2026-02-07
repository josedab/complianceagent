"""Compliance Drift Detection models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class DriftSeverity(str, Enum):
    """Drift event severity."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DriftType(str, Enum):
    """Type of compliance drift."""

    REGRESSION = "regression"
    NEW_VIOLATION = "new_violation"
    CONFIGURATION_CHANGE = "configuration_change"
    DEPENDENCY_UPDATE = "dependency_update"
    POLICY_CHANGE = "policy_change"


class AlertChannel(str, Enum):
    """Notification channel."""

    SLACK = "slack"
    TEAMS = "teams"
    PAGERDUTY = "pagerduty"
    EMAIL = "email"
    WEBHOOK = "webhook"


class AlertStatus(str, Enum):
    """Alert status."""

    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class ComplianceBaseline:
    """Snapshot of compliance state at a point in time."""

    id: UUID = field(default_factory=uuid4)
    repo: str = ""
    branch: str = "main"
    commit_sha: str = ""
    score: float = 100.0
    findings_count: int = 0
    findings_by_severity: dict[str, int] = field(default_factory=dict)
    findings_by_regulation: dict[str, int] = field(default_factory=dict)
    captured_at: datetime | None = None


@dataclass
class DriftEvent:
    """A detected compliance drift event."""

    id: UUID = field(default_factory=uuid4)
    repo: str = ""
    branch: str = "main"
    drift_type: DriftType = DriftType.REGRESSION
    severity: DriftSeverity = DriftSeverity.MEDIUM
    regulation: str = ""
    article_ref: str = ""
    description: str = ""
    file_path: str = ""
    commit_sha: str = ""
    previous_score: float = 100.0
    current_score: float = 100.0
    blast_radius: list[str] = field(default_factory=list)
    detected_at: datetime | None = None
    resolved_at: datetime | None = None


@dataclass
class DriftAlert:
    """An alert generated from a drift event."""

    id: UUID = field(default_factory=uuid4)
    drift_event_id: UUID = field(default_factory=uuid4)
    channel: AlertChannel = AlertChannel.EMAIL
    status: AlertStatus = AlertStatus.PENDING
    recipients: list[str] = field(default_factory=list)
    message: str = ""
    sent_at: datetime | None = None


@dataclass
class AlertConfig:
    """Configuration for drift alerting."""

    channels: list[AlertChannel] = field(default_factory=lambda: [AlertChannel.EMAIL])
    severity_threshold: DriftSeverity = DriftSeverity.MEDIUM
    recipients: dict[str, list[str]] = field(default_factory=dict)
    batch_interval_seconds: int = 300
    slack_webhook_url: str = ""
    teams_webhook_url: str = ""
    pagerduty_routing_key: str = ""


@dataclass
class DriftReport:
    """Summary report of drift over a time period."""

    repo: str = ""
    period_start: datetime | None = None
    period_end: datetime | None = None
    total_events: int = 0
    events_by_severity: dict[str, int] = field(default_factory=dict)
    events_by_type: dict[str, int] = field(default_factory=dict)
    score_trend: list[dict] = field(default_factory=list)
    top_drifting_files: list[dict] = field(default_factory=list)
