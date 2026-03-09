"""Compliance Agent Client SDK models."""

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class SDKRuntime(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"


class ClientMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class RateLimitTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class APIKeyStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass
class SDKConfig:
    base_url: str = "https://api.complianceagent.ai/v1"
    api_key: str = ""
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_backoff_factor: float = 0.5
    oauth2_client_id: str = ""
    oauth2_client_secret: str = ""


@dataclass
class SDKEndpoint:
    path: str = ""
    method: ClientMethod = ClientMethod.GET
    description: str = ""
    request_schema: dict[str, Any] = field(default_factory=dict)
    response_schema: dict[str, Any] = field(default_factory=dict)
    requires_auth: bool = True
    rate_limit_group: str = "default"
    category: str = "core"
    deprecated: bool = False
    version: str = "v1"


@dataclass
class SDKPackageInfo:
    runtime: SDKRuntime = SDKRuntime.PYTHON
    name: str = ""
    version: str = "0.1.0"
    install_command: str = ""
    source_url: str = ""
    docs_url: str = ""
    changelog_url: str = ""
    min_runtime_version: str = ""
    dependencies: list[str] = field(default_factory=list)
    code_sample: str = ""


@dataclass
class GeneratedClient:
    runtime: SDKRuntime = SDKRuntime.PYTHON
    code: str = ""
    filename: str = ""
    endpoints_covered: int = 0
    generated_at: datetime | None = None


@dataclass
class OAuth2Token:
    """OAuth2 token for SDK authentication."""
    access_token: str = ""
    token_type: str = "Bearer"  # noqa: S105
    expires_in: int = 3600
    refresh_token: str = ""
    scope: str = "read write"
    issued_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_expired(self) -> bool:
        elapsed = (datetime.now(UTC) - self.issued_at).total_seconds()
        return elapsed >= self.expires_in


@dataclass
class OAuth2Client:
    """OAuth2 client registration."""
    id: UUID = field(default_factory=uuid4)
    client_id: str = ""
    client_secret_hash: str = ""
    name: str = ""
    organization_id: UUID | None = None
    redirect_uris: list[str] = field(default_factory=list)
    scopes: list[str] = field(default_factory=lambda: ["read", "write"])
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class APIKey:
    """API key for SDK authentication."""
    id: UUID = field(default_factory=uuid4)
    key_prefix: str = ""  # "ca_live_" or "ca_test_"
    key_hash: str = ""
    name: str = ""
    organization_id: UUID | None = None
    status: APIKeyStatus = APIKeyStatus.ACTIVE
    tier: RateLimitTier = RateLimitTier.FREE
    scopes: list[str] = field(default_factory=lambda: ["read"])
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    usage_count: int = 0

    @staticmethod
    def generate(prefix: str = "ca_live_") -> tuple[str, str]:
        """Generate a new API key and its hash."""
        raw_key = f"{prefix}{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return raw_key, key_hash


@dataclass
class RateLimitConfig:
    """Rate limiting configuration per tier."""
    tier: RateLimitTier = RateLimitTier.FREE
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10
    concurrent_requests: int = 5


@dataclass
class RateLimitStatus:
    """Current rate limit status for a key."""
    remaining_minute: int = 60
    remaining_hour: int = 1000
    remaining_day: int = 10000
    reset_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_limited: bool = False


@dataclass
class SDKStats:
    total_endpoints: int = 0
    packages_available: int = 0
    by_method: dict[str, int] = field(default_factory=dict)
    total_downloads: dict[str, int] = field(default_factory=dict)
    active_api_keys: int = 0
    oauth2_clients: int = 0
