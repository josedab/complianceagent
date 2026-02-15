"""GitHub/GitLab Marketplace App models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
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


@dataclass
class UsageRecord:
    """Record of API usage for billing/metering."""

    id: UUID = field(default_factory=uuid4)
    installation_id: UUID | None = None
    endpoint: str = ""
    method: str = "GET"
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    response_time_ms: float = 0.0
    status_code: int = 200
    tokens_used: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "installation_id": str(self.installation_id) if self.installation_id else None,
            "endpoint": self.endpoint,
            "method": self.method,
            "timestamp": self.timestamp.isoformat(),
            "response_time_ms": self.response_time_ms,
            "status_code": self.status_code,
            "tokens_used": self.tokens_used,
        }


@dataclass
class UsageSummary:
    """Aggregated usage summary for an installation."""

    installation_id: str = ""
    period: str = ""
    total_requests: int = 0
    total_tokens: int = 0
    avg_response_time_ms: float = 0.0
    endpoints_breakdown: dict[str, int] = field(default_factory=dict)
    quota_limit: int = 0
    quota_used: int = 0
    quota_remaining: int = 0
    overage: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "installation_id": self.installation_id,
            "period": self.period,
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "avg_response_time_ms": self.avg_response_time_ms,
            "endpoints_breakdown": self.endpoints_breakdown,
            "quota_limit": self.quota_limit,
            "quota_used": self.quota_used,
            "quota_remaining": self.quota_remaining,
            "overage": self.overage,
        }


class PlanQuota(str, Enum):
    """Plan-based quotas."""

    FREE = "free"
    TEAM = "team"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


PLAN_LIMITS: dict[str, dict[str, int]] = {
    "free": {"monthly_requests": 1000, "repos": 3, "scans_per_day": 5, "tokens": 50000},
    "team": {"monthly_requests": 10000, "repos": 25, "scans_per_day": 50, "tokens": 500000},
    "business": {"monthly_requests": 100000, "repos": 100, "scans_per_day": 500, "tokens": 5000000},
    "enterprise": {"monthly_requests": -1, "repos": -1, "scans_per_day": -1, "tokens": -1},
}
