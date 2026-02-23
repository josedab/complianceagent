"""Compliance Agents Marketplace models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class AgentCategory(str, Enum):
    CHECKER = "checker"
    FIXER = "fixer"
    REPORTER = "reporter"
    SCANNER = "scanner"
    ANALYZER = "analyzer"


class AgentStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


class InstallStatus(str, Enum):
    INSTALLED = "installed"
    UNINSTALLED = "uninstalled"
    DISABLED = "disabled"


@dataclass
class MarketplaceAgent:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    slug: str = ""
    description: str = ""
    category: AgentCategory = AgentCategory.CHECKER
    author: str = ""
    author_org: str = ""
    version: str = "1.0.0"
    mcp_tool_name: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    status: AgentStatus = AgentStatus.DRAFT
    downloads: int = 0
    rating: float = 0.0
    rating_count: int = 0
    tags: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    source_url: str = ""
    icon_url: str = ""
    revenue_share_pct: float = 70.0
    published_at: datetime | None = None
    created_at: datetime | None = None


@dataclass
class AgentInstallation:
    id: UUID = field(default_factory=uuid4)
    agent_id: UUID = field(default_factory=uuid4)
    organization_id: str = ""
    status: InstallStatus = InstallStatus.INSTALLED
    config: dict[str, Any] = field(default_factory=dict)
    installed_at: datetime | None = None
    last_executed_at: datetime | None = None
    execution_count: int = 0


@dataclass
class AgentReview:
    id: UUID = field(default_factory=uuid4)
    agent_id: UUID = field(default_factory=uuid4)
    reviewer: str = ""
    rating: int = 5
    comment: str = ""
    created_at: datetime | None = None


@dataclass
class MarketplaceStats:
    total_agents: int = 0
    published_agents: int = 0
    total_installations: int = 0
    total_executions: int = 0
    by_category: dict[str, int] = field(default_factory=dict)
    top_agents: list[dict[str, Any]] = field(default_factory=list)
