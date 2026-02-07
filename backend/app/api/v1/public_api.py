"""API endpoints for Public API & SDK Management."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB

from app.services.public_api import (
    APIKeyScope,
    PublicAPIService,
    RateLimitTier,
)

logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class CreateAPIKeyRequest(BaseModel):
    """Request to create an API key."""

    name: str = Field(..., min_length=1, max_length=255)
    scopes: list[str] = Field(default_factory=lambda: ["read"])
    tier: str = Field(default="free")
    expires_days: int | None = Field(default=None)


class APIKeyResponse(BaseModel):
    """API key response (without raw key)."""

    id: str
    name: str
    key_prefix: str
    scopes: list[str]
    status: str
    rate_limit_tier: str
    created_at: str | None
    last_used_at: str | None
    total_requests: int


class APIKeyCreatedResponse(APIKeyResponse):
    """API key creation response (includes raw key, shown only once)."""

    raw_key: str


class UsageSummarySchema(BaseModel):
    """API usage summary."""

    key_id: str
    period: str
    total_requests: int
    successful_requests: int
    error_requests: int
    avg_latency_ms: float
    top_endpoints: list[dict[str, Any]]


class RateLimitSchema(BaseModel):
    """Rate limit info."""

    tier: str
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_size: int


class SDKInfoSchema(BaseModel):
    """SDK information."""

    language: str
    package_name: str
    version: str
    install_command: str
    documentation_url: str
    source_url: str


# --- Endpoints ---


@router.post(
    "/keys",
    response_model=APIKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create API key",
    description="Create a new API key. The raw key is only shown once.",
)
async def create_api_key(request: CreateAPIKeyRequest, db: DB) -> APIKeyCreatedResponse:
    """Create a new API key."""
    service = PublicAPIService(db=db)
    scopes = [APIKeyScope(s) for s in request.scopes]
    tier = RateLimitTier(request.tier)

    key, raw_key = await service.create_api_key(
        name=request.name, scopes=scopes, tier=tier,
        expires_days=request.expires_days,
    )

    return APIKeyCreatedResponse(
        id=str(key.id), name=key.name, key_prefix=key.key_prefix,
        scopes=[s.value for s in key.scopes], status=key.status.value,
        rate_limit_tier=key.rate_limit_tier.value,
        created_at=key.created_at.isoformat() if key.created_at else None,
        last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
        total_requests=key.total_requests, raw_key=raw_key,
    )


@router.get(
    "/keys",
    response_model=list[APIKeyResponse],
    summary="List API keys",
)
async def list_api_keys(db: DB) -> list[APIKeyResponse]:
    """List all API keys."""
    service = PublicAPIService(db=db)
    keys = await service.list_keys()
    return [
        APIKeyResponse(
            id=str(k.id), name=k.name, key_prefix=k.key_prefix,
            scopes=[s.value for s in k.scopes], status=k.status.value,
            rate_limit_tier=k.rate_limit_tier.value,
            created_at=k.created_at.isoformat() if k.created_at else None,
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            total_requests=k.total_requests,
        )
        for k in keys
    ]


@router.delete(
    "/keys/{key_id}",
    summary="Revoke API key",
)
async def revoke_api_key(key_id: UUID, db: DB) -> dict:
    """Revoke an API key."""
    service = PublicAPIService(db=db)
    revoked = await service.revoke_key(key_id)
    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return {"status": "revoked", "key_id": str(key_id)}


@router.get(
    "/keys/{key_id}/usage",
    response_model=UsageSummarySchema,
    summary="Get API key usage",
)
async def get_key_usage(
    key_id: UUID, db: DB, period: str = "day",
) -> UsageSummarySchema:
    """Get usage summary for an API key."""
    service = PublicAPIService(db=db)
    summary = await service.get_usage_summary(key_id, period=period)
    return UsageSummarySchema(
        key_id=str(summary.key_id), period=summary.period,
        total_requests=summary.total_requests,
        successful_requests=summary.successful_requests,
        error_requests=summary.error_requests,
        avg_latency_ms=summary.avg_latency_ms,
        top_endpoints=summary.top_endpoints,
    )


@router.get(
    "/rate-limits",
    response_model=list[RateLimitSchema],
    summary="Get rate limits",
)
async def get_rate_limits(db: DB) -> list[RateLimitSchema]:
    """Get rate limit configurations for all tiers."""
    service = PublicAPIService(db=db)
    limits = await service.get_rate_limits()
    return [
        RateLimitSchema(
            tier=config.tier.value,
            requests_per_minute=config.requests_per_minute,
            requests_per_hour=config.requests_per_hour,
            requests_per_day=config.requests_per_day,
            burst_size=config.burst_size,
        )
        for config in limits.values()
    ]


@router.get(
    "/sdks",
    response_model=list[SDKInfoSchema],
    summary="List available SDKs",
)
async def list_sdks(db: DB) -> list[SDKInfoSchema]:
    """List available client SDKs."""
    service = PublicAPIService(db=db)
    sdks = await service.list_sdks()
    return [
        SDKInfoSchema(
            language=s.language, package_name=s.package_name,
            version=s.version, install_command=s.install_command,
            documentation_url=s.documentation_url, source_url=s.source_url,
        )
        for s in sdks
    ]
