"""Marketplace Revenue models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class RevenueModel(str, Enum):
    """Revenue models for marketplace agent listings."""

    FREE = "free"
    PAID_LISTING = "paid_listing"
    SUBSCRIPTION = "subscription"
    USAGE_BASED = "usage_based"


class PayoutStatus(str, Enum):
    """Status of an author payout."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentListing:
    """A marketplace agent listing with revenue tracking."""

    id: UUID = field(default_factory=uuid4)
    agent_slug: str = ""
    author: str = ""
    revenue_model: RevenueModel = RevenueModel.FREE
    listing_fee_usd: float = 0.0
    price_usd: float = 0.0
    revenue_share_pct: float = 70.0
    monthly_revenue: float = 0.0
    total_revenue: float = 0.0
    subscribers: int = 0
    featured: bool = False
    listed_at: datetime | None = None


@dataclass
class Payout:
    """A payout to an agent author."""

    id: UUID = field(default_factory=uuid4)
    author: str = ""
    amount_usd: float = 0.0
    period: str = ""
    status: PayoutStatus = PayoutStatus.PENDING
    agents: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    paid_at: datetime | None = None


@dataclass
class RevenueReport:
    """A revenue report for a given period."""

    period: str = ""
    total_revenue: float = 0.0
    platform_share: float = 0.0
    author_payouts: float = 0.0
    by_model: dict = field(default_factory=dict)
    top_agents: list[dict] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass
class RevenueStats:
    """Aggregate marketplace revenue statistics."""

    total_listings: int = 0
    paid_listings: int = 0
    total_revenue: float = 0.0
    platform_revenue: float = 0.0
    author_payouts: float = 0.0
    avg_revenue_per_agent: float = 0.0
    by_revenue_model: dict = field(default_factory=dict)
