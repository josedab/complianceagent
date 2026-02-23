"""Compliance SDK models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class SDKLanguage(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    GO = "go"


class APIKeyTier(str, Enum):
    FREE = "free"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class APIKeyStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass
class SDKPackage:
    language: SDKLanguage = SDKLanguage.PYTHON
    name: str = ""
    version: str = "0.1.0"
    install_command: str = ""
    registry_url: str = ""
    description: str = ""
    downloads: int = 0


@dataclass
class APIKey:
    id: UUID = field(default_factory=uuid4)
    key_prefix: str = ""
    key_hash: str = ""
    name: str = ""
    tier: APIKeyTier = APIKeyTier.FREE
    status: APIKeyStatus = APIKeyStatus.ACTIVE
    organization_id: str = ""
    rate_limit_per_minute: int = 60
    scopes: list[str] = field(default_factory=lambda: ["read"])
    created_at: datetime | None = None
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    total_requests: int = 0


@dataclass
class APIUsageRecord:
    id: UUID = field(default_factory=uuid4)
    api_key_id: UUID = field(default_factory=uuid4)
    endpoint: str = ""
    method: str = "GET"
    status_code: int = 200
    response_time_ms: float = 0.0
    timestamp: datetime | None = None


@dataclass
class SDKUsageSummary:
    total_keys: int = 0
    active_keys: int = 0
    total_requests: int = 0
    requests_by_tier: dict[str, int] = field(default_factory=dict)
    requests_by_endpoint: dict[str, int] = field(default_factory=dict)
    avg_response_time_ms: float = 0.0
    sdk_downloads: dict[str, int] = field(default_factory=dict)


@dataclass
class RateLimitInfo:
    tier: str = "free"
    limit_per_minute: int = 60
    remaining: int = 60
    reset_at: datetime | None = None
