"""Public API & SDK management models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class APIKeyStatus(str, Enum):
    """API key status."""

    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    RATE_LIMITED = "rate_limited"


class APIKeyScope(str, Enum):
    """API key access scopes."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    SCAN = "scan"
    REPORTS = "reports"


class RateLimitTier(str, Enum):
    """Rate limit tiers."""

    FREE = "free"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class APIKey:
    """A public API key."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    key_prefix: str = ""
    key_hash: str = ""
    scopes: list[APIKeyScope] = field(default_factory=lambda: [APIKeyScope.READ])
    status: APIKeyStatus = APIKeyStatus.ACTIVE
    rate_limit_tier: RateLimitTier = RateLimitTier.FREE
    tenant_id: UUID | None = None
    created_by: str = ""
    expires_at: datetime | None = None
    created_at: datetime | None = None
    last_used_at: datetime | None = None
    total_requests: int = 0


@dataclass
class APIUsageRecord:
    """API usage tracking record."""

    key_id: UUID = field(default_factory=uuid4)
    endpoint: str = ""
    method: str = "GET"
    status_code: int = 200
    latency_ms: float = 0.0
    timestamp: datetime | None = None


@dataclass
class RateLimitConfig:
    """Rate limit configuration per tier."""

    tier: RateLimitTier = RateLimitTier.FREE
    requests_per_minute: int = 10
    requests_per_hour: int = 100
    requests_per_day: int = 1000
    burst_size: int = 20


@dataclass
class APIUsageSummary:
    """API usage summary for a key."""

    key_id: UUID = field(default_factory=uuid4)
    period: str = "day"
    total_requests: int = 0
    successful_requests: int = 0
    error_requests: int = 0
    avg_latency_ms: float = 0.0
    top_endpoints: list[dict] = field(default_factory=list)
    requests_by_hour: list[dict] = field(default_factory=list)


@dataclass
class SDKInfo:
    """SDK package information."""

    language: str = ""
    package_name: str = ""
    version: str = ""
    install_command: str = ""
    documentation_url: str = ""
    source_url: str = ""


# Default rate limits per tier
RATE_LIMITS: dict[RateLimitTier, RateLimitConfig] = {
    RateLimitTier.FREE: RateLimitConfig(tier=RateLimitTier.FREE, requests_per_minute=10, requests_per_hour=100, requests_per_day=1000),
    RateLimitTier.STANDARD: RateLimitConfig(tier=RateLimitTier.STANDARD, requests_per_minute=60, requests_per_hour=1000, requests_per_day=10000),
    RateLimitTier.PROFESSIONAL: RateLimitConfig(tier=RateLimitTier.PROFESSIONAL, requests_per_minute=120, requests_per_hour=5000, requests_per_day=50000),
    RateLimitTier.ENTERPRISE: RateLimitConfig(tier=RateLimitTier.ENTERPRISE, requests_per_minute=600, requests_per_hour=30000, requests_per_day=500000),
}
