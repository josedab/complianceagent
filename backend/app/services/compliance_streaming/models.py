"""Real-Time Compliance Streaming Protocol models."""

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


class ConnectionState(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"


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
class StreamStats:
    active_connections: int = 0
    total_events_published: int = 0
    events_per_second: float = 0.0
    channels: list[StreamChannel] = field(default_factory=list)
    by_event_type: dict[str, int] = field(default_factory=dict)
