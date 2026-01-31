"""Data models for Regulatory API Marketplace."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class PlanTier(str, Enum):
    """API subscription tiers."""
    
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    WHITE_LABEL = "white_label"


class APICategory(str, Enum):
    """Categories of compliance APIs."""
    
    ANALYSIS = "analysis"
    MONITORING = "monitoring"
    REPORTING = "reporting"
    VALIDATION = "validation"
    INTELLIGENCE = "intelligence"
    EVIDENCE = "evidence"


class UsageType(str, Enum):
    """Types of API usage."""
    
    REQUEST = "request"
    ANALYSIS = "analysis"
    REPORT = "report"
    SCAN = "scan"
    WEBHOOK = "webhook"


@dataclass
class APIProduct:
    """A compliance API product available in the marketplace."""
    
    id: UUID = field(default_factory=uuid4)
    slug: str = ""
    name: str = ""
    description: str = ""
    category: APICategory = APICategory.ANALYSIS
    version: str = "1.0.0"
    
    # Endpoints
    base_path: str = ""
    endpoints: list[dict[str, Any]] = field(default_factory=list)
    
    # Documentation
    documentation_url: str = ""
    openapi_spec: str = ""
    
    # Pricing
    free_tier_limit: int = 100  # Monthly requests
    price_per_request: float = 0.01
    enterprise_pricing: bool = False
    
    # Features
    features: list[str] = field(default_factory=list)
    supported_frameworks: list[str] = field(default_factory=list)
    
    # Status
    is_active: bool = True
    is_beta: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class APIKey:
    """An API key for marketplace access."""
    
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    key_prefix: str = ""  # First 8 chars for identification
    key_hash: str = ""  # Hashed full key
    name: str = ""
    
    # Permissions
    plan_tier: PlanTier = PlanTier.FREE
    allowed_products: list[UUID] = field(default_factory=list)  # Empty = all
    scopes: list[str] = field(default_factory=list)
    
    # Limits
    rate_limit: int = 100  # Requests per minute
    monthly_limit: int = 1000
    
    # Status
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    
    # White-label
    white_label_enabled: bool = False
    white_label_config: dict[str, Any] = field(default_factory=dict)


@dataclass
class UsageRecord:
    """Record of API usage."""
    
    id: UUID = field(default_factory=uuid4)
    api_key_id: UUID | None = None
    organization_id: UUID | None = None
    product_id: UUID | None = None
    
    # Request details
    endpoint: str = ""
    method: str = "GET"
    usage_type: UsageType = UsageType.REQUEST
    
    # Response
    status_code: int = 200
    response_time_ms: float = 0.0
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: str = ""
    user_agent: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Subscription:
    """API subscription for an organization."""
    
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    
    # Plan
    plan_tier: PlanTier = PlanTier.FREE
    subscribed_products: list[UUID] = field(default_factory=list)
    
    # Usage
    current_period_start: datetime = field(default_factory=datetime.utcnow)
    current_period_end: datetime | None = None
    usage_this_period: int = 0
    
    # Billing
    monthly_price: float = 0.0
    overage_rate: float = 0.01
    
    # Status
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    cancelled_at: datetime | None = None


@dataclass
class WhiteLabelConfig:
    """White-label configuration for resellers."""
    
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    
    # Branding
    brand_name: str = ""
    logo_url: str = ""
    primary_color: str = "#0066cc"
    secondary_color: str = "#ffffff"
    
    # Custom domain
    custom_domain: str = ""
    ssl_enabled: bool = True
    
    # Features
    enabled_products: list[UUID] = field(default_factory=list)
    custom_pricing: dict[str, float] = field(default_factory=dict)
    
    # Status
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UsageSummary:
    """Summary of API usage for billing."""
    
    organization_id: UUID
    period_start: datetime
    period_end: datetime
    
    # Totals
    total_requests: int = 0
    total_analyses: int = 0
    total_reports: int = 0
    
    # By product
    by_product: dict[str, int] = field(default_factory=dict)
    
    # Costs
    included_requests: int = 0
    overage_requests: int = 0
    estimated_cost: float = 0.0


# Plan configuration
PLAN_CONFIGS: dict[PlanTier, dict[str, Any]] = {
    PlanTier.FREE: {
        "monthly_requests": 100,
        "rate_limit_per_minute": 10,
        "features": ["basic_analysis", "limited_reports"],
        "price": 0,
    },
    PlanTier.STARTER: {
        "monthly_requests": 1000,
        "rate_limit_per_minute": 30,
        "features": ["analysis", "reports", "monitoring"],
        "price": 49,
    },
    PlanTier.PROFESSIONAL: {
        "monthly_requests": 10000,
        "rate_limit_per_minute": 100,
        "features": ["analysis", "reports", "monitoring", "intelligence", "evidence"],
        "price": 199,
    },
    PlanTier.ENTERPRISE: {
        "monthly_requests": -1,  # Unlimited
        "rate_limit_per_minute": 500,
        "features": ["all"],
        "price": -1,  # Custom
    },
    PlanTier.WHITE_LABEL: {
        "monthly_requests": -1,
        "rate_limit_per_minute": 1000,
        "features": ["all", "white_label", "custom_branding"],
        "price": -1,
    },
}
