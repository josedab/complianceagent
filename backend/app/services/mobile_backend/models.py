"""Mobile Backend models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class NotificationType(str, Enum):
    """Types of mobile push notifications."""

    SCORE_CHANGE = "score_change"
    VIOLATION = "violation"
    REGULATION_UPDATE = "regulation_update"
    INCIDENT = "incident"
    APPROVAL_REQUEST = "approval_request"
    BADGE_EARNED = "badge_earned"


class DevicePlatform(str, Enum):
    """Supported mobile device platforms."""

    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


class PushPriority(str, Enum):
    """Priority levels for push notifications."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class DeviceRegistration:
    """A registered mobile device for push notifications."""

    id: UUID = field(default_factory=uuid4)
    user_id: str = ""
    platform: DevicePlatform = DevicePlatform.IOS
    device_token: str = ""
    push_enabled: bool = True
    registered_at: datetime | None = None


@dataclass
class PushNotification:
    """A push notification sent to a user."""

    id: UUID = field(default_factory=uuid4)
    user_id: str = ""
    notification_type: NotificationType = NotificationType.SCORE_CHANGE
    title: str = ""
    body: str = ""
    priority: PushPriority = PushPriority.NORMAL
    data: dict = field(default_factory=dict)
    sent: bool = False
    sent_at: datetime | None = None


@dataclass
class MobileDashboard:
    """Dashboard data for the mobile app."""

    user_id: str = ""
    overall_score: float = 0.0
    score_trend: str = ""
    active_incidents: int = 0
    pending_approvals: int = 0
    recent_badges: list[str] = field(default_factory=list)
    top_violations: list[dict] = field(default_factory=list)


@dataclass
class MobileStats:
    """Statistics for the mobile backend."""

    registered_devices: int = 0
    by_platform: dict = field(default_factory=dict)
    notifications_sent: int = 0
    push_enabled: int = 0
    active_users_24h: int = 0
