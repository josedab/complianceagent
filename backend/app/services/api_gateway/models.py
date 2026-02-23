"""Compliance API Gateway models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class APITier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class TokenStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    RATE_LIMITED = "rate_limited"


@dataclass
class OAuthClient:
    id: UUID = field(default_factory=uuid4)
    client_id: str = ""
    client_name: str = ""
    tier: APITier = APITier.FREE
    redirect_uris: list[str] = field(default_factory=list)
    scopes: list[str] = field(default_factory=lambda: ["read"])
    rate_limit_per_minute: int = 60
    monthly_quota: int = 10000
    monthly_usage: int = 0
    status: TokenStatus = TokenStatus.ACTIVE
    created_at: datetime | None = None


@dataclass
class APIUsageRecord:
    id: UUID = field(default_factory=uuid4)
    client_id: str = ""
    endpoint: str = ""
    method: str = "GET"
    status_code: int = 200
    response_time_ms: float = 0.0
    timestamp: datetime | None = None


@dataclass
class RateLimitStatus:
    client_id: str = ""
    tier: str = "free"
    limit_per_minute: int = 60
    remaining: int = 60
    monthly_quota: int = 10000
    monthly_used: int = 0
    reset_at: datetime | None = None


@dataclass
class DeveloperPortalInfo:
    api_base_url: str = "https://api.complianceagent.ai/v1"
    docs_url: str = "https://docs.complianceagent.ai"
    playground_url: str = "https://playground.complianceagent.ai"
    sdks: list[dict[str, str]] = field(default_factory=list)
    changelog_url: str = "https://docs.complianceagent.ai/changelog"
    status_url: str = "https://status.complianceagent.ai"


@dataclass
class GatewayStats:
    total_clients: int = 0
    active_clients: int = 0
    total_requests: int = 0
    by_tier: dict[str, int] = field(default_factory=dict)
    by_endpoint: dict[str, int] = field(default_factory=dict)
    avg_response_time_ms: float = 0.0
    error_rate_pct: float = 0.0
