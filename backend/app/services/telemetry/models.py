"""Real-time compliance telemetry models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class MetricType(str, Enum):
    """Types of telemetry metrics."""

    COMPLIANCE_SCORE = "compliance_score"
    VIOLATION_COUNT = "violation_count"
    REQUIREMENT_COVERAGE = "requirement_coverage"
    DRIFT_SCORE = "drift_score"
    SCAN_DURATION = "scan_duration"
    REMEDIATION_RATE = "remediation_rate"
    RISK_SCORE = "risk_score"
    AUDIT_READINESS = "audit_readiness"


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    """Alert delivery channels."""

    WEBSOCKET = "websocket"
    SLACK = "slack"
    EMAIL = "email"
    PAGERDUTY = "pagerduty"
    TEAMS = "teams"


class TelemetryEventType(str, Enum):
    """Types of real-time telemetry events."""

    SCORE_CHANGE = "score_change"
    VIOLATION_DETECTED = "violation_detected"
    SCAN_COMPLETED = "scan_completed"
    DRIFT_DETECTED = "drift_detected"
    REMEDIATION_APPLIED = "remediation_applied"
    REGULATION_UPDATE = "regulation_update"
    THRESHOLD_BREACH = "threshold_breach"


@dataclass
class TelemetryMetric:
    """A single telemetry metric data point."""

    id: UUID = field(default_factory=uuid4)
    metric_type: MetricType = MetricType.COMPLIANCE_SCORE
    value: float = 0.0
    previous_value: float | None = None
    unit: str = ""
    framework: str | None = None
    repository: str | None = None
    timestamp: datetime | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class TelemetryEvent:
    """A real-time telemetry event."""

    id: UUID = field(default_factory=uuid4)
    event_type: TelemetryEventType = TelemetryEventType.SCORE_CHANGE
    severity: AlertSeverity = AlertSeverity.INFO
    title: str = ""
    description: str = ""
    source: str = ""
    framework: str | None = None
    repository: str | None = None
    metric_value: float | None = None
    timestamp: datetime | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class AlertThreshold:
    """Configurable alert threshold."""

    id: UUID = field(default_factory=uuid4)
    metric_type: MetricType = MetricType.COMPLIANCE_SCORE
    operator: str = "lt"  # lt, gt, eq, lte, gte
    value: float = 0.0
    severity: AlertSeverity = AlertSeverity.WARNING
    channels: list[AlertChannel] = field(default_factory=lambda: [AlertChannel.WEBSOCKET])
    enabled: bool = True
    cooldown_minutes: int = 60
    last_triggered: datetime | None = None
    created_at: datetime | None = None


@dataclass
class TelemetrySnapshot:
    """Current telemetry snapshot with all key metrics."""

    id: UUID = field(default_factory=uuid4)
    overall_score: float = 0.0
    violation_count: int = 0
    requirement_coverage: float = 0.0
    drift_score: float = 0.0
    risk_score: float = 0.0
    audit_readiness: float = 0.0
    frameworks: dict[str, float] = field(default_factory=dict)
    repositories: dict[str, float] = field(default_factory=dict)
    timestamp: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "overall_score": round(self.overall_score, 2),
            "violation_count": self.violation_count,
            "requirement_coverage": round(self.requirement_coverage, 2),
            "drift_score": round(self.drift_score, 2),
            "risk_score": round(self.risk_score, 2),
            "audit_readiness": round(self.audit_readiness, 2),
            "frameworks": {k: round(v, 2) for k, v in self.frameworks.items()},
            "repositories": {k: round(v, 2) for k, v in self.repositories.items()},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class MetricTimeSeries:
    """Time series data for a metric."""

    metric_type: MetricType = MetricType.COMPLIANCE_SCORE
    data_points: list[TelemetryMetric] = field(default_factory=list)
    framework: str | None = None
    period: str = "24h"  # 1h, 24h, 7d, 30d

    @property
    def latest_value(self) -> float | None:
        return self.data_points[-1].value if self.data_points else None

    @property
    def trend(self) -> float | None:
        if len(self.data_points) < 2:
            return None
        return self.data_points[-1].value - self.data_points[0].value
