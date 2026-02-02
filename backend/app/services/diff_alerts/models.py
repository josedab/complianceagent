"""Diff alerts data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class DiffChangeType(str, Enum):
    """Type of text change."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class AlertStatus(str, Enum):
    """Status of a regulatory alert."""
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class AlertSeverity(str, Enum):
    """Severity of a regulatory change alert."""
    CRITICAL = "critical"  # Major compliance impact
    HIGH = "high"          # Significant changes
    MEDIUM = "medium"      # Moderate changes
    LOW = "low"            # Minor updates


@dataclass
class DiffChange:
    """A single change in the diff."""
    change_type: DiffChangeType
    line_number_old: int | None
    line_number_new: int | None
    old_text: str | None
    new_text: str | None
    context_before: list[str] = field(default_factory=list)
    context_after: list[str] = field(default_factory=list)


@dataclass
class TextDiff:
    """Complete diff between two versions of regulatory text."""
    old_version: str
    new_version: str
    old_version_date: datetime | None
    new_version_date: datetime | None
    changes: list[DiffChange]
    additions_count: int = 0
    deletions_count: int = 0
    modifications_count: int = 0
    similarity_ratio: float = 1.0
    
    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0


@dataclass
class ImpactAnalysis:
    """AI-generated analysis of regulatory change impact."""
    summary: str
    key_changes: list[str]
    affected_areas: list[str]
    compliance_impact: str
    recommended_actions: list[str]
    urgency_level: AlertSeverity
    affected_frameworks: list[str] = field(default_factory=list)
    affected_requirements: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class RegulatoryAlert:
    """A regulatory change alert."""
    id: UUID = field(default_factory=uuid4)
    regulation_id: UUID | None = None
    regulation_name: str = ""
    jurisdiction: str = ""
    framework: str = ""
    
    # Diff information
    diff: TextDiff | None = None
    old_version_id: str | None = None
    new_version_id: str | None = None
    
    # Analysis
    impact_analysis: ImpactAnalysis | None = None
    severity: AlertSeverity = AlertSeverity.MEDIUM
    
    # Status tracking
    status: AlertStatus = AlertStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: datetime | None = None
    acknowledged_by: UUID | None = None
    resolved_at: datetime | None = None
    
    # Notification tracking
    notification_sent: bool = False
    notification_channels: list[str] = field(default_factory=list)
    
    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertAcknowledgment:
    """Acknowledgment of an alert."""
    alert_id: UUID
    user_id: UUID
    organization_id: UUID
    acknowledged_at: datetime = field(default_factory=datetime.utcnow)
    notes: str | None = None
    action_taken: str | None = None


@dataclass
class NotificationConfig:
    """Configuration for alert notifications."""
    slack_webhook_url: str | None = None
    slack_channel: str | None = None
    teams_webhook_url: str | None = None
    email_recipients: list[str] = field(default_factory=list)
    min_severity: AlertSeverity = AlertSeverity.LOW
    enabled: bool = True
