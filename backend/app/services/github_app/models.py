"""GitHub App service models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class InstallationStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    UNINSTALLED = "uninstalled"


class WebhookEventType(str, Enum):
    INSTALLATION = "installation"
    PULL_REQUEST = "pull_request"
    PUSH = "push"
    CHECK_RUN = "check_run"
    CHECK_SUITE = "check_suite"


class AppPlan(str, Enum):
    FREE = "free"
    TEAM = "team"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


@dataclass
class AppInstallation:
    id: UUID = field(default_factory=uuid4)
    github_installation_id: int = 0
    account_login: str = ""
    account_type: str = "Organization"
    status: InstallationStatus = InstallationStatus.ACTIVE
    plan: AppPlan = AppPlan.FREE
    repositories: list[str] = field(default_factory=list)
    permissions: dict[str, str] = field(default_factory=dict)
    events_subscribed: list[str] = field(default_factory=list)
    installed_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class WebhookEvent:
    id: UUID = field(default_factory=uuid4)
    event_type: WebhookEventType = WebhookEventType.PUSH
    installation_id: int = 0
    payload: dict[str, Any] = field(default_factory=dict)
    processed: bool = False
    result: dict[str, Any] = field(default_factory=dict)
    received_at: datetime | None = None
    processed_at: datetime | None = None


@dataclass
class AppMarketplaceListing:
    name: str = "ComplianceAgent"
    slug: str = "complianceagent"
    description: str = "AI-powered compliance monitoring and code generation"
    plans: list[dict[str, Any]] = field(default_factory=list)
    categories: list[str] = field(default_factory=lambda: ["compliance", "security", "code-quality"])
    install_url: str = ""
    setup_url: str = ""


@dataclass
class ComplianceCheckResult:
    id: UUID = field(default_factory=uuid4)
    installation_id: int = 0
    repo: str = ""
    pr_number: int = 0
    check_run_id: int = 0
    conclusion: str = "success"
    violations_found: int = 0
    frameworks_checked: list[str] = field(default_factory=list)
    annotations: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime | None = None
