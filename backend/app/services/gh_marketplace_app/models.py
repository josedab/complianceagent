"""Compliance Copilot GitHub Marketplace App models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class MarketplacePlan(str, Enum):
    FREE = "free"
    TEAM = "team"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class AppFeature(str, Enum):
    PR_BOT = "pr_bot"
    CHECKS = "checks"
    BADGE = "badge"
    IDE_LINT = "ide_lint"
    AI_CODEGEN = "ai_codegen"
    DASHBOARD = "dashboard"


class InstallState(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    UNINSTALLED = "uninstalled"


@dataclass
class MarketplaceApp:
    id: UUID = field(default_factory=uuid4)
    name: str = "ComplianceAgent"
    slug: str = "complianceagent"
    tagline: str = "AI-powered compliance monitoring and code generation"
    description: str = "Automatically monitor regulations, detect violations, and generate compliant code."
    pricing_url: str = "https://complianceagent.ai/pricing"
    install_url: str = "https://github.com/apps/complianceagent/installations/new"
    plans: list[dict[str, Any]] = field(default_factory=list)
    total_installs: int = 0
    rating: float = 0.0
    categories: list[str] = field(default_factory=lambda: ["compliance", "security", "code-quality"])


@dataclass
class AppInstall:
    id: UUID = field(default_factory=uuid4)
    github_id: int = 0
    account: str = ""
    account_type: str = "Organization"
    plan: MarketplacePlan = MarketplacePlan.FREE
    state: InstallState = InstallState.ACTIVE
    features_enabled: list[str] = field(default_factory=list)
    repos: list[str] = field(default_factory=list)
    repo_limit: int = 3
    checks_run: int = 0
    violations_found: int = 0
    prs_analyzed: int = 0
    installed_at: datetime | None = None
    last_active_at: datetime | None = None


@dataclass
class CheckRun:
    id: UUID = field(default_factory=uuid4)
    install_id: UUID = field(default_factory=uuid4)
    repo: str = ""
    pr_number: int = 0
    sha: str = ""
    conclusion: str = "success"
    violations: int = 0
    frameworks: list[str] = field(default_factory=list)
    annotations: list[dict[str, Any]] = field(default_factory=list)
    badge_grade: str = "B+"
    duration_ms: float = 0.0
    created_at: datetime | None = None


@dataclass
class MarketplaceStats:
    total_installs: int = 0
    active_installs: int = 0
    by_plan: dict[str, int] = field(default_factory=dict)
    total_checks: int = 0
    total_violations_found: int = 0
    total_prs_analyzed: int = 0
    avg_check_duration_ms: float = 0.0
