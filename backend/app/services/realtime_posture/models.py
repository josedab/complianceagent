"""Real-Time Compliance Posture API models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4


class PostureEvent(str, Enum):
    """Types of posture events."""

    SCORE_CHANGE = "score_change"
    VIOLATION_ADDED = "violation_added"
    VIOLATION_RESOLVED = "violation_resolved"
    EVIDENCE_EXPIRED = "evidence_expired"
    SCAN_COMPLETE = "scan_complete"


class AlertChannel(str, Enum):
    """Alert delivery channels."""

    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    EMAIL = "email"
    WEBHOOK = "webhook"


@dataclass
class AlertRule:
    """A rule that triggers alerts based on posture metrics."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    metric: str = ""
    threshold: float = 0.0
    channel: AlertChannel = AlertChannel.EMAIL
    enabled: bool = True


@dataclass
class PostureSnapshot:
    """A point-in-time snapshot of compliance posture."""

    organization_id: str = ""
    score: float = 0.0
    grade: str = "C"
    violations: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class PostureStreamConfig:
    """Configuration for posture streaming."""

    poll_interval_seconds: int = 30
    alert_rules: list[AlertRule] = field(default_factory=list)
    channels: list[AlertChannel] = field(default_factory=list)
