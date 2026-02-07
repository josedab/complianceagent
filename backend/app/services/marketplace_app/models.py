"""GitHub/GitLab Marketplace App models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class InstallationStatus(str, Enum):
    """App installation status."""

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    UNINSTALLED = "uninstalled"


class MarketplacePlan(str, Enum):
    """Marketplace pricing plan."""

    FREE = "free"
    TEAM = "team"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class AppPlatform(str, Enum):
    """Source platform."""

    GITHUB = "github"
    GITLAB = "gitlab"


@dataclass
class AppInstallation:
    """A marketplace app installation."""

    id: UUID = field(default_factory=uuid4)
    platform: AppPlatform = AppPlatform.GITHUB
    external_id: int = 0
    account_login: str = ""
    account_type: str = "Organization"
    plan: MarketplacePlan = MarketplacePlan.FREE
    status: InstallationStatus = InstallationStatus.PENDING
    repositories: list[str] = field(default_factory=list)
    permissions: dict = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    tenant_id: UUID | None = None
    installed_at: datetime | None = None
    settings: dict = field(default_factory=dict)


@dataclass
class WebhookEvent:
    """Incoming webhook event from GitHub/GitLab."""

    id: UUID = field(default_factory=uuid4)
    platform: AppPlatform = AppPlatform.GITHUB
    event_type: str = ""
    action: str = ""
    installation_id: int = 0
    payload: dict = field(default_factory=dict)
    received_at: datetime | None = None
    processed: bool = False


@dataclass
class InstallationSyncResult:
    """Result of syncing installation repositories."""

    installation_id: UUID = field(default_factory=uuid4)
    repos_added: list[str] = field(default_factory=list)
    repos_removed: list[str] = field(default_factory=list)
    scans_triggered: int = 0


@dataclass
class MarketplaceListingInfo:
    """Marketplace listing metadata."""

    app_name: str = "ComplianceAgent"
    description: str = "Autonomous regulatory compliance for your codebase"
    plans: list[dict] = field(default_factory=list)
    categories: list[str] = field(default_factory=lambda: ["compliance", "security", "code-quality"])
    install_url: str = ""
    webhook_url: str = ""
