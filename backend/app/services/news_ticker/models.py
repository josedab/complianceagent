"""Regulatory News Ticker models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class NewsSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class NotificationChannel(str, Enum):
    SLACK = "slack"
    TEAMS = "teams"
    EMAIL = "email"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NewsCategory(str, Enum):
    NEW_REGULATION = "new_regulation"
    AMENDMENT = "amendment"
    ENFORCEMENT_ACTION = "enforcement_action"
    GUIDANCE = "guidance"
    DEADLINE = "deadline"
    COURT_RULING = "court_ruling"


@dataclass
class RegulatoryNewsItem:
    """A single regulatory news item."""
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    summary: str = ""
    category: NewsCategory = NewsCategory.NEW_REGULATION
    severity: NewsSeverity = NewsSeverity.MEDIUM
    source_url: str = ""
    source_name: str = ""
    jurisdictions: list[str] = field(default_factory=list)
    affected_regulations: list[str] = field(default_factory=list)
    affected_industries: list[str] = field(default_factory=list)
    published_at: datetime | None = None
    relevance_score: float = 0.0
    impact_summary: str = ""
    action_required: bool = False
    tags: list[str] = field(default_factory=list)


@dataclass
class NotificationPreference:
    """User notification preferences for regulatory news."""
    id: UUID = field(default_factory=uuid4)
    org_id: UUID | None = None
    user_id: UUID | None = None
    channel: NotificationChannel = NotificationChannel.IN_APP
    enabled: bool = True
    min_severity: NewsSeverity = NewsSeverity.MEDIUM
    jurisdictions: list[str] = field(default_factory=list)
    regulations: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    max_per_day: int = 20
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None


@dataclass
class NotificationDelivery:
    """Record of a notification delivery."""
    id: UUID = field(default_factory=uuid4)
    news_item_id: UUID | None = None
    user_id: UUID | None = None
    channel: NotificationChannel = NotificationChannel.IN_APP
    delivered_at: datetime | None = None
    read_at: datetime | None = None
    dismissed: bool = False
    feedback: str | None = None


@dataclass
class NewsFeed:
    """Paginated news feed response."""
    items: list[RegulatoryNewsItem] = field(default_factory=list)
    total: int = 0
    unread_count: int = 0
    filters_applied: dict = field(default_factory=dict)


@dataclass
class SlackWebhookConfig:
    """Slack webhook configuration."""
    webhook_url: str = ""
    channel: str = ""
    bot_name: str = "ComplianceAgent"
    icon_emoji: str = ":shield:"


@dataclass
class TeamsWebhookConfig:
    """Microsoft Teams webhook configuration."""
    webhook_url: str = ""
    channel_name: str = ""


@dataclass
class NewsDigest:
    """A periodic digest of regulatory news."""
    id: UUID = field(default_factory=uuid4)
    period: str = "daily"
    items: list[RegulatoryNewsItem] = field(default_factory=list)
    summary: str = ""
    generated_at: datetime | None = None
