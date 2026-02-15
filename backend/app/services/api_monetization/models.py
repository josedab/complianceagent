"""Compliance API Monetization Layer models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID


class PricingTier(str, Enum):
    """API pricing tiers."""

    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class APIStatus(str, Enum):
    """Status of a published API."""

    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


@dataclass
class ComplianceAPI:
    """A monetizable compliance check API."""

    id: str
    name: str
    description: str
    endpoint: str
    regulation: str
    version: str = "1.0.0"
    status: APIStatus = APIStatus.PUBLISHED
    requests_per_month: int = 0
    avg_latency_ms: float = 150.0
    pricing_per_request: float = 0.01
    documentation_url: str = ""
    supported_languages: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class APISubscription:
    """A developer's subscription to an API."""

    id: UUID
    developer_id: UUID
    api_id: str
    tier: PricingTier
    monthly_quota: int = 100
    requests_used: int = 0
    monthly_cost: float = 0.0
    api_key: str = ""
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UsageRecord:
    """API usage tracking record."""

    api_id: str
    developer_id: UUID
    requests_count: int = 0
    tokens_consumed: int = 0
    compute_time_ms: float = 0.0
    cost: float = 0.0
    period: str = ""
    recorded_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class APIRevenueStats:
    """Revenue statistics for APIs."""

    total_apis: int = 0
    total_developers: int = 0
    total_requests_month: int = 0
    monthly_revenue: float = 0.0
    top_api: str = ""
    revenue_growth_pct: float = 0.0
    avg_revenue_per_api: float = 0.0
