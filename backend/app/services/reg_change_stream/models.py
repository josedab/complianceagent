"""Regulatory Change Stream models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class ChangeSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class SubscriptionChannel(str, Enum):
    SSE = "sse"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    PAGERDUTY = "pagerduty"
    EMAIL = "email"


class ChangeStatus(str, Enum):
    DETECTED = "detected"
    CLASSIFIED = "classified"
    NOTIFIED = "notified"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class RegulatoryChange:
    id: UUID = field(default_factory=uuid4)
    regulation: str = ""
    jurisdiction: str = ""
    title: str = ""
    summary: str = ""
    severity: ChangeSeverity = ChangeSeverity.MEDIUM
    status: ChangeStatus = ChangeStatus.DETECTED
    source_url: str = ""
    affected_articles: list[str] = field(default_factory=list)
    affected_frameworks: list[str] = field(default_factory=list)
    change_type: str = "amendment"
    effective_date: str = ""
    detected_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamSubscription:
    id: UUID = field(default_factory=uuid4)
    subscriber_id: str = ""
    channel: SubscriptionChannel = SubscriptionChannel.WEBHOOK
    endpoint_url: str = ""
    filters: dict[str, Any] = field(default_factory=dict)
    severity_threshold: ChangeSeverity = ChangeSeverity.MEDIUM
    jurisdictions: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime | None = None
    last_notified_at: datetime | None = None


@dataclass
class StreamNotification:
    id: UUID = field(default_factory=uuid4)
    subscription_id: UUID = field(default_factory=uuid4)
    change_id: UUID = field(default_factory=uuid4)
    channel: SubscriptionChannel = SubscriptionChannel.WEBHOOK
    status: str = "pending"
    attempts: int = 0
    sent_at: datetime | None = None
    error_message: str = ""


@dataclass
class StreamStats:
    total_changes: int = 0
    changes_by_severity: dict[str, int] = field(default_factory=dict)
    changes_by_jurisdiction: dict[str, int] = field(default_factory=dict)
    active_subscriptions: int = 0
    notifications_sent: int = 0
    avg_detection_latency_min: float = 0.0
