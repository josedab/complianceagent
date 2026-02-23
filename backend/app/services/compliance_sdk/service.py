"""Compliance SDK Service."""

import hashlib
import secrets
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.compliance_sdk.models import (
    APIKey,
    APIKeyStatus,
    APIKeyTier,
    APIUsageRecord,
    RateLimitInfo,
    SDKLanguage,
    SDKPackage,
    SDKUsageSummary,
)


logger = structlog.get_logger()


TIER_RATE_LIMITS = {
    APIKeyTier.FREE: 60,
    APIKeyTier.STANDARD: 300,
    APIKeyTier.PROFESSIONAL: 1000,
    APIKeyTier.ENTERPRISE: 5000,
}

SDK_PACKAGES: list[SDKPackage] = [
    SDKPackage(
        language=SDKLanguage.PYTHON,
        name="complianceagent",
        version="0.1.0",
        install_command="pip install complianceagent",
        registry_url="https://pypi.org/project/complianceagent/",
        description="Python SDK for ComplianceAgent API",
    ),
    SDKPackage(
        language=SDKLanguage.TYPESCRIPT,
        name="@complianceagent/sdk",
        version="0.1.0",
        install_command="npm install @complianceagent/sdk",
        registry_url="https://www.npmjs.com/package/@complianceagent/sdk",
        description="TypeScript/JavaScript SDK for ComplianceAgent API",
    ),
    SDKPackage(
        language=SDKLanguage.GO,
        name="github.com/josedab/complianceagent-go",
        version="0.1.0",
        install_command="go get github.com/josedab/complianceagent-go",
        registry_url="https://pkg.go.dev/github.com/josedab/complianceagent-go",
        description="Go SDK for ComplianceAgent API",
    ),
]


class ComplianceSDKService:
    """Service for managing SDK packages, API keys, and usage tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._api_keys: dict[str, APIKey] = {}
        self._usage_records: list[APIUsageRecord] = []

    def list_sdk_packages(self, language: SDKLanguage | None = None) -> list[SDKPackage]:
        pkgs = list(SDK_PACKAGES)
        if language:
            pkgs = [p for p in pkgs if p.language == language]
        return pkgs

    async def create_api_key(
        self,
        name: str,
        organization_id: str,
        tier: str = "free",
        scopes: list[str] | None = None,
    ) -> tuple[APIKey, str]:
        """Create a new API key. Returns (key_object, raw_key)."""
        raw_key = f"ca_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:10]
        api_tier = APIKeyTier(tier)

        key = APIKey(
            key_prefix=key_prefix,
            key_hash=key_hash,
            name=name,
            tier=api_tier,
            status=APIKeyStatus.ACTIVE,
            organization_id=organization_id,
            rate_limit_per_minute=TIER_RATE_LIMITS.get(api_tier, 60),
            scopes=scopes or ["read"],
            created_at=datetime.now(UTC),
        )
        self._api_keys[key_hash] = key
        logger.info("API key created", name=name, tier=tier)
        return key, raw_key

    async def validate_api_key(self, raw_key: str) -> APIKey | None:
        """Validate an API key and return the key object."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key = self._api_keys.get(key_hash)
        if not key:
            return None
        if key.status != APIKeyStatus.ACTIVE:
            return None
        if key.expires_at and key.expires_at < datetime.now(UTC):
            key.status = APIKeyStatus.EXPIRED
            return None
        key.last_used_at = datetime.now(UTC)
        key.total_requests += 1
        return key

    async def revoke_api_key(self, key_id: UUID) -> bool:
        for key in self._api_keys.values():
            if key.id == key_id:
                key.status = APIKeyStatus.REVOKED
                logger.info("API key revoked", key_id=str(key_id))
                return True
        return False

    def list_api_keys(self, organization_id: str | None = None) -> list[APIKey]:
        keys = list(self._api_keys.values())
        if organization_id:
            keys = [k for k in keys if k.organization_id == organization_id]
        return sorted(keys, key=lambda k: k.created_at or datetime.min.replace(tzinfo=UTC), reverse=True)

    async def record_usage(
        self,
        api_key_id: UUID,
        endpoint: str,
        method: str = "GET",
        status_code: int = 200,
        response_time_ms: float = 0.0,
    ) -> APIUsageRecord:
        record = APIUsageRecord(
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            timestamp=datetime.now(UTC),
        )
        self._usage_records.append(record)
        return record

    def get_usage_summary(self, organization_id: str | None = None) -> SDKUsageSummary:
        keys = self.list_api_keys(organization_id)
        active_keys = [k for k in keys if k.status == APIKeyStatus.ACTIVE]

        by_tier: dict[str, int] = {}
        for k in keys:
            by_tier[k.tier.value] = by_tier.get(k.tier.value, 0) + k.total_requests

        by_endpoint: dict[str, int] = {}
        total_time = 0.0
        for r in self._usage_records:
            by_endpoint[r.endpoint] = by_endpoint.get(r.endpoint, 0) + 1
            total_time += r.response_time_ms

        total_reqs = len(self._usage_records)
        avg_time = round(total_time / total_reqs, 2) if total_reqs else 0.0

        return SDKUsageSummary(
            total_keys=len(keys),
            active_keys=len(active_keys),
            total_requests=total_reqs,
            requests_by_tier=by_tier,
            requests_by_endpoint=by_endpoint,
            avg_response_time_ms=avg_time,
            sdk_downloads={p.language.value: p.downloads for p in SDK_PACKAGES},
        )

    def get_rate_limit_info(self, api_key: APIKey) -> RateLimitInfo:
        return RateLimitInfo(
            tier=api_key.tier.value,
            limit_per_minute=api_key.rate_limit_per_minute,
            remaining=max(0, api_key.rate_limit_per_minute - (api_key.total_requests % api_key.rate_limit_per_minute)),
        )
