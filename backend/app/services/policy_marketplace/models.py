"""Data models for the Compliance-as-Code Policy Marketplace."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class PolicyPackStatus(str, Enum):
    """Lifecycle status of a policy pack."""

    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"


class PricingModel(str, Enum):
    """Pricing models for policy packs."""

    FREE = "free"
    ONE_TIME = "one_time"
    SUBSCRIPTION = "subscription"
    USAGE_BASED = "usage_based"


class PolicyLanguage(str, Enum):
    """Supported policy languages."""

    REGO = "rego"
    PYTHON = "python"
    YAML = "yaml"
    TYPESCRIPT = "typescript"
    JSON = "json"


@dataclass
class PolicyFile:
    """A single policy file within a pack."""

    path: str = ""
    language: PolicyLanguage = PolicyLanguage.REGO
    content: str = ""
    description: str = ""


@dataclass
class PolicyPack:
    """A compliance policy pack published to the marketplace."""

    id: UUID = field(default_factory=uuid4)
    creator_id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    version: str = "1.0.0"
    regulations: list[str] = field(default_factory=list)
    languages: list[PolicyLanguage] = field(default_factory=list)
    pricing_model: PricingModel = PricingModel.FREE
    price_usd: float = 0.0
    revenue_share_pct: float = 70.0
    status: PolicyPackStatus = PolicyPackStatus.DRAFT
    downloads: int = 0
    rating: float = 0.0
    review_count: int = 0
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PolicyPackVersion:
    """A specific version of a policy pack."""

    id: UUID = field(default_factory=uuid4)
    pack_id: UUID = field(default_factory=uuid4)
    version: str = "1.0.0"
    changelog: str = ""
    files: list[PolicyFile] = field(default_factory=list)
    published_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PolicyReview:
    """A user review of a policy pack."""

    id: UUID = field(default_factory=uuid4)
    pack_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    rating: float = 5.0
    comment: str = ""
    verified_purchase: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CreatorProfile:
    """A marketplace creator profile."""

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    display_name: str = ""
    bio: str = ""
    expertise: list[str] = field(default_factory=list)
    published_packs: int = 0
    total_downloads: int = 0
    total_earnings_usd: float = 0.0
    verified: bool = False
    joined_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Purchase:
    """A policy pack purchase record."""

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    pack_id: UUID = field(default_factory=uuid4)
    price_usd: float = 0.0
    creator_payout_usd: float = 0.0
    platform_fee_usd: float = 0.0
    purchased_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MarketplaceStats:
    """Aggregate marketplace statistics."""

    total_packs: int = 0
    total_creators: int = 0
    total_downloads: int = 0
    total_gmv_usd: float = 0.0
    top_categories: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PolicyBundle:
    """A bundle of policy packs offered at a discount."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    packs: list[str] = field(default_factory=list)
    bundle_price_usd: float = 0.0
    savings_pct: float = 0.0
