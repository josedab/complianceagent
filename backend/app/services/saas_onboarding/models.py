"""Zero-Config Compliance SaaS models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class OnboardingStep(str, Enum):
    SIGNUP = "signup"
    CONNECT_SCM = "connect_scm"
    SELECT_REPOS = "select_repos"
    FIRST_SCAN = "first_scan"
    DASHBOARD = "dashboard"
    COMPLETED = "completed"


class SaaSPlan(str, Enum):
    FREE = "free"
    TEAM = "team"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


@dataclass
class SaaSTenant:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    slug: str = ""
    owner_email: str = ""
    plan: SaaSPlan = SaaSPlan.FREE
    status: TenantStatus = TenantStatus.PROVISIONING
    repo_limit: int = 3
    repos_connected: int = 0
    scm_provider: str = ""
    scm_org: str = ""
    onboarding_step: OnboardingStep = OnboardingStep.SIGNUP
    onboarding_completed: bool = False
    first_scan_score: float | None = None
    region: str = "us-east-1"
    settings: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    activated_at: datetime | None = None


@dataclass
class OnboardingProgress:
    tenant_id: UUID = field(default_factory=uuid4)
    current_step: OnboardingStep = OnboardingStep.SIGNUP
    steps_completed: list[str] = field(default_factory=list)
    time_to_first_scan_seconds: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class UsageLimits:
    plan: SaaSPlan = SaaSPlan.FREE
    max_repos: int = 3
    max_scans_per_day: int = 10
    max_api_calls_per_minute: int = 60
    ai_features_enabled: bool = False
    sso_enabled: bool = False
    custom_policies_enabled: bool = False
    support_tier: str = "community"


@dataclass
class SaaSMetrics:
    total_tenants: int = 0
    active_tenants: int = 0
    by_plan: dict[str, int] = field(default_factory=dict)
    avg_time_to_first_scan_min: float = 0.0
    onboarding_completion_rate: float = 0.0
    total_repos_connected: int = 0
