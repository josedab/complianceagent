"""Public API & SDK Management Service."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.public_api.models import (
    APIKey,
    APIKeyScope,
    APIKeyStatus,
    APIUsageRecord,
    APIUsageSummary,
    RATE_LIMITS,
    RateLimitConfig,
    RateLimitTier,
    SDKInfo,
)

logger = structlog.get_logger()

# Available SDKs
_SDKS: list[SDKInfo] = [
    SDKInfo(
        language="python",
        package_name="complianceagent-sdk",
        version="0.1.0",
        install_command="pip install complianceagent-sdk",
        documentation_url="https://docs.complianceagent.ai/sdk/python",
        source_url="https://github.com/josedab/complianceagent/tree/main/shared/compliance-sdk-python",
    ),
    SDKInfo(
        language="typescript",
        package_name="@complianceagent/sdk",
        version="0.1.0",
        install_command="npm install @complianceagent/sdk",
        documentation_url="https://docs.complianceagent.ai/sdk/typescript",
        source_url="https://github.com/josedab/complianceagent/tree/main/shared/compliance-sdk-typescript",
    ),
    SDKInfo(
        language="go",
        package_name="github.com/josedab/complianceagent-go",
        version="0.1.0",
        install_command="go get github.com/josedab/complianceagent-go",
        documentation_url="https://docs.complianceagent.ai/sdk/go",
        source_url="https://github.com/josedab/complianceagent-go",
    ),
]


class PublicAPIService:
    """Service for managing public API keys, rate limiting, and SDK information."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._keys: dict[UUID, APIKey] = {}
        self._usage: list[APIUsageRecord] = []

    async def create_api_key(
        self,
        name: str,
        scopes: list[APIKeyScope] | None = None,
        tier: RateLimitTier = RateLimitTier.FREE,
        tenant_id: UUID | None = None,
        created_by: str = "",
        expires_days: int | None = None,
    ) -> tuple[APIKey, str]:
        """Create a new API key. Returns (key_metadata, raw_key)."""
        raw_key = f"ca_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:10]

        api_key = APIKey(
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            scopes=scopes or [APIKeyScope.READ],
            rate_limit_tier=tier,
            tenant_id=tenant_id,
            created_by=created_by,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=expires_days) if expires_days else None,
        )

        self._keys[api_key.id] = api_key
        logger.info("API key created", name=name, prefix=key_prefix, tier=tier.value)
        return api_key, raw_key

    async def validate_key(self, raw_key: str) -> APIKey | None:
        """Validate an API key and return its metadata."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        for key in self._keys.values():
            if key.key_hash == key_hash:
                if key.status != APIKeyStatus.ACTIVE:
                    return None
                if key.expires_at and key.expires_at < datetime.now(UTC):
                    key.status = APIKeyStatus.EXPIRED
                    return None
                key.last_used_at = datetime.now(UTC)
                key.total_requests += 1
                return key
        return None

    async def revoke_key(self, key_id: UUID) -> bool:
        """Revoke an API key."""
        key = self._keys.get(key_id)
        if key:
            key.status = APIKeyStatus.REVOKED
            logger.info("API key revoked", key_id=str(key_id))
            return True
        return False

    async def list_keys(self, tenant_id: UUID | None = None) -> list[APIKey]:
        """List API keys for a tenant."""
        keys = list(self._keys.values())
        if tenant_id:
            keys = [k for k in keys if k.tenant_id == tenant_id]
        return keys

    async def get_key(self, key_id: UUID) -> APIKey | None:
        """Get an API key by ID."""
        return self._keys.get(key_id)

    async def record_usage(
        self,
        key_id: UUID,
        endpoint: str,
        method: str = "GET",
        status_code: int = 200,
        latency_ms: float = 0.0,
    ) -> APIUsageRecord:
        """Record an API usage event."""
        record = APIUsageRecord(
            key_id=key_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            latency_ms=latency_ms,
            timestamp=datetime.now(UTC),
        )
        self._usage.append(record)
        return record

    async def check_rate_limit(self, key_id: UUID) -> tuple[bool, RateLimitConfig]:
        """Check if a key is within its rate limits."""
        key = self._keys.get(key_id)
        if not key:
            return False, RATE_LIMITS[RateLimitTier.FREE]

        config = RATE_LIMITS.get(key.rate_limit_tier, RATE_LIMITS[RateLimitTier.FREE])

        now = datetime.now(UTC)
        minute_ago = now - timedelta(minutes=1)
        recent = [
            r for r in self._usage
            if r.key_id == key_id and r.timestamp and r.timestamp > minute_ago
        ]

        within_limit = len(recent) < config.requests_per_minute
        return within_limit, config

    async def get_usage_summary(
        self,
        key_id: UUID,
        period: str = "day",
    ) -> APIUsageSummary:
        """Get usage summary for an API key."""
        now = datetime.now(UTC)
        if period == "hour":
            cutoff = now - timedelta(hours=1)
        elif period == "day":
            cutoff = now - timedelta(days=1)
        else:
            cutoff = now - timedelta(days=30)

        records = [
            r for r in self._usage
            if r.key_id == key_id and r.timestamp and r.timestamp > cutoff
        ]

        total = len(records)
        successful = sum(1 for r in records if r.status_code < 400)
        avg_latency = sum(r.latency_ms for r in records) / total if total else 0

        endpoint_counts: dict[str, int] = {}
        for r in records:
            endpoint_counts[r.endpoint] = endpoint_counts.get(r.endpoint, 0) + 1

        top_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return APIUsageSummary(
            key_id=key_id,
            period=period,
            total_requests=total,
            successful_requests=successful,
            error_requests=total - successful,
            avg_latency_ms=round(avg_latency, 2),
            top_endpoints=[{"endpoint": e, "count": c} for e, c in top_endpoints],
        )

    async def list_sdks(self) -> list[SDKInfo]:
        """List available SDKs."""
        return _SDKS

    async def get_rate_limits(self) -> dict[str, RateLimitConfig]:
        """Get all rate limit configurations."""
        return {tier.value: config for tier, config in RATE_LIMITS.items()}
