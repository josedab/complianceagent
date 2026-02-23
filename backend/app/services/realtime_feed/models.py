"""Real-Time Regulatory Change Feed models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class FeedItemType(str, Enum):
    REGULATION_CHANGE = "regulation_change"
    ENFORCEMENT_ACTION = "enforcement_action"
    GUIDANCE_UPDATE = "guidance_update"
    CONSULTATION = "consultation"
    DEADLINE_REMINDER = "deadline_reminder"


class NotificationChannel(str, Enum):
    WEBSOCKET = "websocket"
    SLACK = "slack"
    TEAMS = "teams"
    EMAIL = "email"
    PUSH = "push"


class FeedPriority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class FeedItem:
    id: UUID = field(default_factory=uuid4)
    item_type: FeedItemType = FeedItemType.REGULATION_CHANGE
    priority: FeedPriority = FeedPriority.NORMAL
    title: str = ""
    summary: str = ""
    regulation: str = ""
    jurisdiction: str = ""
    source_url: str = ""
    impact_score: float = 0.0
    published_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FeedSubscription:
    id: UUID = field(default_factory=uuid4)
    user_id: str = ""
    channels: list[NotificationChannel] = field(default_factory=list)
    min_priority: FeedPriority = FeedPriority.NORMAL
    jurisdictions: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    digest_enabled: bool = False
    digest_frequency: str = "daily"
    created_at: datetime | None = None


@dataclass
class SlackCard:
    channel: str = ""
    title: str = ""
    text: str = ""
    color: str = "#36a64f"
    fields: list[dict[str, str]] = field(default_factory=list)
    action_url: str = ""


@dataclass
class FeedStats:
    total_items: int = 0
    items_today: int = 0
    subscribers: int = 0
    by_type: dict[str, int] = field(default_factory=dict)
    by_jurisdiction: dict[str, int] = field(default_factory=dict)
    notifications_sent: int = 0
