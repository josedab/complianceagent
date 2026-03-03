"""Real-Time Compliance Streaming Protocol models."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class StreamEventType(str, Enum):
    SCORE_CHANGE = "score_change"
    VIOLATION_DETECTED = "violation_detected"
    VIOLATION_RESOLVED = "violation_resolved"
    SCAN_COMPLETED = "scan_completed"
    REGULATION_UPDATE = "regulation_update"
    DRIFT_DETECTED = "drift_detected"
    FIX_MERGED = "fix_merged"
    ALERT_FIRED = "alert_fired"
    ALERT_RESOLVED = "alert_resolved"
    EVIDENCE_COLLECTED = "evidence_collected"
    CERT_PROGRESS = "cert_progress"


class ConnectionState(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"


class WebhookTarget(str, Enum):
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    TEAMS = "teams"
    GENERIC = "generic"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class StreamEvent:
    id: UUID = field(default_factory=uuid4)
    event_type: StreamEventType = StreamEventType.SCORE_CHANGE
    channel: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    tenant_id: str = ""
    repo: str = ""
    timestamp: datetime | None = None


@dataclass
class StreamSubscription:
    id: UUID = field(default_factory=uuid4)
    client_id: str = ""
    channels: list[str] = field(default_factory=list)
    event_types: list[str] = field(default_factory=list)
    filters: dict[str, Any] = field(default_factory=dict)
    state: ConnectionState = ConnectionState.CONNECTED
    connected_at: datetime | None = None
    last_event_at: datetime | None = None
    events_received: int = 0


@dataclass
class StreamChannel:
    name: str = ""
    description: str = ""
    event_count: int = 0
    subscriber_count: int = 0


@dataclass
class WebhookIntegration:
    """External webhook integration for event delivery."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    target: WebhookTarget = WebhookTarget.GENERIC
    url: str = ""
    channels: list[str] = field(default_factory=list)
    event_types: list[str] = field(default_factory=list)
    min_severity: AlertSeverity = AlertSeverity.MEDIUM
    active: bool = True
    secret: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    created_at: datetime | None = None
    last_delivery_at: datetime | None = None
    delivery_count: int = 0
    failure_count: int = 0


@dataclass
class AlertPolicy:
    """Configurable threshold-based alerting policy."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    channel: str = ""
    condition_type: str = ""  # threshold, change, absence
    metric: str = ""
    operator: str = "lt"  # lt, gt, eq, lte, gte
    threshold: float = 0.0
    window_seconds: int = 300
    severity: AlertSeverity = AlertSeverity.MEDIUM
    webhook_ids: list[UUID] = field(default_factory=list)
    active: bool = True
    cooldown_seconds: int = 3600
    last_fired_at: datetime | None = None
    fire_count: int = 0


@dataclass
class AlertFiring:
    """Record of an alert being fired."""
    id: UUID = field(default_factory=uuid4)
    policy_id: UUID = field(default_factory=uuid4)
    policy_name: str = ""
    severity: AlertSeverity = AlertSeverity.MEDIUM
    message: str = ""
    current_value: float = 0.0
    threshold: float = 0.0
    fired_at: datetime | None = None
    resolved_at: datetime | None = None
    notified_webhooks: list[str] = field(default_factory=list)


@dataclass
class StreamStats:
    active_connections: int = 0
    total_events_published: int = 0
    events_per_second: float = 0.0
    channels: list[StreamChannel] = field(default_factory=list)
    by_event_type: dict[str, int] = field(default_factory=dict)
    webhook_integrations: int = 0
    active_alert_policies: int = 0
    alerts_fired_24h: int = 0
    avg_delivery_latency_ms: float = 0.0
