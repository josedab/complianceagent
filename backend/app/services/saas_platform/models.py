"""Data models for SaaS Platform service."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass
class TenantConfig:
    """Configuration for provisioning a new tenant."""

    name: str
    slug: str
    plan: str = "free"
    owner_email: str = ""
    industry: str = ""
    jurisdictions: list[str] = field(default_factory=list)
    github_org: str = ""


@dataclass
class OnboardingStep:
    """A single onboarding step for a tenant."""

    id: str
    name: str
    description: str
    status: str = "pending"  # pending, completed, skipped
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class ResourceLimits:
    """Resource limits for a tenant plan."""

    max_repos: int = 5
    max_scans_per_month: int = 100
    max_api_calls_per_day: int = 1000
    max_seats: int = 5
    max_storage_mb: int = 500

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_repos": self.max_repos,
            "max_scans_per_month": self.max_scans_per_month,
            "max_api_calls_per_day": self.max_api_calls_per_day,
            "max_seats": self.max_seats,
            "max_storage_mb": self.max_storage_mb,
        }


@dataclass
class TenantProvisionResult:
    """Result of tenant provisioning."""

    tenant_id: UUID = field(default_factory=uuid4)
    status: str = "provisioned"
    api_key: str = ""
    onboarding_steps: list[OnboardingStep] = field(default_factory=list)
    dashboard_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": str(self.tenant_id),
            "status": self.status,
            "api_key": self.api_key,
            "onboarding_steps": [s.to_dict() for s in self.onboarding_steps],
            "dashboard_url": self.dashboard_url,
        }


@dataclass
class UsageSummary:
    """Usage summary for a tenant."""

    tenant_id: UUID = field(default_factory=uuid4)
    period: str = "current"
    api_calls: int = 0
    scans_run: int = 0
    regulations_tracked: int = 0
    storage_mb: float = 0.0
    seats_used: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": str(self.tenant_id),
            "period": self.period,
            "api_calls": self.api_calls,
            "scans_run": self.scans_run,
            "regulations_tracked": self.regulations_tracked,
            "storage_mb": self.storage_mb,
            "seats_used": self.seats_used,
        }
