"""Digital Compliance Marketplace models."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class AssetType(str, Enum):
    POLICY = "policy"
    EVIDENCE_TEMPLATE = "evidence_template"
    ARCHITECTURE_PATTERN = "architecture_pattern"
    TRAINING_MODULE = "training_module"
    COMPLIANCE_PLAYBOOK = "compliance_playbook"


class AssetStatus(str, Enum):
    DRAFT = "draft"
    LISTED = "listed"
    SOLD = "sold"
    ARCHIVED = "archived"


class PricingModel(str, Enum):
    FREE = "free"
    ONE_TIME = "one_time"
    SUBSCRIPTION = "subscription"
    PAY_PER_USE = "pay_per_use"


@dataclass
class MarketplaceAsset:
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    asset_type: AssetType = AssetType.POLICY
    author: str = ""
    pricing: PricingModel = PricingModel.FREE
    price_usd: float = 0.0
    status: AssetStatus = AssetStatus.DRAFT
    downloads: int = 0
    rating: float = 0.0
    rating_count: int = 0
    frameworks: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    content: dict[str, Any] = field(default_factory=dict)
    listed_at: datetime | None = None


@dataclass
class AssetPurchase:
    id: UUID = field(default_factory=uuid4)
    asset_id: UUID = field(default_factory=uuid4)
    buyer_org: str = ""
    price_paid: float = 0.0
    purchased_at: datetime | None = None


@dataclass
class MarketplaceRevenueReport:
    period: str = ""
    total_sales: int = 0
    total_revenue: float = 0.0
    by_asset_type: dict[str, Any] = field(default_factory=dict)
    top_sellers: list[dict[str, Any]] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass
class DigitalMarketplaceStats:
    total_assets: int = 0
    listed_assets: int = 0
    total_purchases: int = 0
    total_revenue: float = 0.0
    by_asset_type: dict[str, int] = field(default_factory=dict)
    avg_rating: float = 0.0
