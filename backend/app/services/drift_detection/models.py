"""Compliance Drift Detection models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
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


class CICDGateDecision(str, Enum):
    """CI/CD gate pass/fail decision."""

    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


@dataclass
class CICDGateResult:
    """Result of a CI/CD compliance gate check."""

    id: UUID = field(default_factory=uuid4)
    repo: str = ""
    branch: str = "main"
    commit_sha: str = ""
    decision: CICDGateDecision = CICDGateDecision.PASS
    current_score: float = 100.0
    threshold_score: float = 80.0
    violations_found: int = 0
    critical_violations: int = 0
    blocking_findings: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_at: datetime | None = None


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


@dataclass
class DriftTrend:
    """Trend data for compliance drift over time."""

    repo: str = ""
    period: str = "7d"
    data_points: list[dict[str, Any]] = field(default_factory=list)
    trend_direction: str = "stable"  # improving, degrading, stable
    avg_score: float = 0.0
    min_score: float = 0.0
    max_score: float = 0.0
    volatility: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo": self.repo,
            "period": self.period,
            "data_points": self.data_points,
            "trend_direction": self.trend_direction,
            "avg_score": self.avg_score,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "volatility": self.volatility,
        }


@dataclass
class WebhookDelivery:
    """Record of a webhook delivery attempt."""

    id: UUID = field(default_factory=uuid4)
    channel: str = ""
    url: str = ""
    event_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, delivered, failed
    response_code: int | None = None
    error_message: str | None = None
    delivered_at: datetime | None = None
    attempts: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "channel": self.channel,
            "url": self.url,
            "event_id": self.event_id,
            "status": self.status,
            "response_code": self.response_code,
            "error_message": self.error_message,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "attempts": self.attempts,
        }


@dataclass
class TopDriftingFile:
    """A file with the most compliance drift."""

    file_path: str = ""
    drift_count: int = 0
    total_delta: float = 0.0
    last_drift_at: str = ""
    regulations_affected: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "drift_count": self.drift_count,
            "total_delta": self.total_delta,
            "last_drift_at": self.last_drift_at,
            "regulations_affected": self.regulations_affected,
        }
