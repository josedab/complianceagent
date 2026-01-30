"""Data models for Regulatory Intelligence Feed."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class UpdateSeverity(str, Enum):
    """Severity/urgency of a regulatory update."""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Action within 30 days
    MEDIUM = "medium"  # Action within 90 days
    LOW = "low"  # Informational
    INFO = "info"  # General news


class UpdateType(str, Enum):
    """Type of regulatory update."""
    NEW_REGULATION = "new_regulation"
    AMENDMENT = "amendment"
    GUIDANCE = "guidance"
    ENFORCEMENT = "enforcement"
    DEADLINE = "deadline"
    DRAFT = "draft"
    CONSULTATION = "consultation"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class NotificationFrequency(str, Enum):
    """Notification delivery frequency."""
    IMMEDIATE = "immediate"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class RegulatorySource:
    """A regulatory source being monitored."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    url: str = ""
    jurisdiction: str = ""
    framework: str = ""
    category: str = ""
    check_frequency_hours: int = 24
    last_checked: datetime | None = None
    last_updated: datetime | None = None
    is_active: bool = True


@dataclass
class RegulatoryUpdate:
    """A detected regulatory update/change."""
    id: UUID = field(default_factory=uuid4)
    source_id: UUID | None = None
    source_name: str = ""
    title: str = ""
    summary: str = ""
    content: str = ""
    url: str = ""
    jurisdiction: str = ""
    framework: str = ""
    update_type: UpdateType = UpdateType.NEW_REGULATION
    severity: UpdateSeverity = UpdateSeverity.MEDIUM
    effective_date: datetime | None = None
    published_date: datetime | None = None
    detected_at: datetime = field(default_factory=datetime.utcnow)
    affected_regulations: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    raw_content: str = ""
    content_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RelevanceScore:
    """Relevance scoring for an update."""
    update_id: UUID | None = None
    organization_id: UUID | None = None
    overall_score: float = 0.0
    jurisdiction_match: float = 0.0
    industry_match: float = 0.0
    regulation_match: float = 0.0
    keyword_match: float = 0.0
    historical_interest: float = 0.0
    urgency_factor: float = 0.0
    confidence: float = 0.0
    explanation: str = ""
    matched_criteria: list[str] = field(default_factory=list)
    scored_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class NotificationPreference:
    """User/org notification preferences."""
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    user_id: UUID | None = None
    channel: NotificationChannel = NotificationChannel.EMAIL
    frequency: NotificationFrequency = NotificationFrequency.DAILY
    min_severity: UpdateSeverity = UpdateSeverity.MEDIUM
    min_relevance: float = 0.5
    jurisdictions: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    muted_sources: list[str] = field(default_factory=list)
    is_active: bool = True
    webhook_url: str | None = None
    slack_channel: str | None = None
    teams_channel: str | None = None


@dataclass
class IntelligenceAlert:
    """An alert generated for a regulatory update."""
    id: UUID = field(default_factory=uuid4)
    update: RegulatoryUpdate | None = None
    relevance: RelevanceScore | None = None
    organization_id: UUID | None = None
    user_ids: list[UUID] = field(default_factory=list)
    title: str = ""
    body: str = ""
    action_required: str = ""
    deadline: datetime | None = None
    channels_sent: list[NotificationChannel] = field(default_factory=list)
    sent_at: datetime | None = None
    read_at: datetime | None = None
    acknowledged_at: datetime | None = None
    acknowledged_by: UUID | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass 
class IntelligenceDigest:
    """A digest of multiple regulatory updates."""
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    total_updates: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    updates: list[RegulatoryUpdate] = field(default_factory=list)
    alerts: list[IntelligenceAlert] = field(default_factory=list)
    summary: str = ""
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CustomerProfile:
    """Customer profile for relevance scoring."""
    organization_id: UUID | None = None
    industries: list[str] = field(default_factory=list)
    jurisdictions: list[str] = field(default_factory=list)
    applicable_regulations: list[str] = field(default_factory=list)
    data_types_processed: list[str] = field(default_factory=list)
    risk_tolerance: str = "medium"  # low, medium, high
    company_size: str = "medium"  # startup, small, medium, enterprise
    keywords_of_interest: list[str] = field(default_factory=list)
