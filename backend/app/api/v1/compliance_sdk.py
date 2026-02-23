"""API endpoints for Compliance SDK."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.compliance_sdk import ComplianceSDKService, SDKLanguage


logger = structlog.get_logger()
router = APIRouter()


class SDKPackageSchema(BaseModel):
    language: str
    name: str
    version: str
    install_command: str
    registry_url: str
    description: str

class CreateAPIKeyRequest(BaseModel):
    name: str = Field(...)
    organization_id: str = Field(...)
    tier: str = Field(default="free")
    scopes: list[str] = Field(default_factory=lambda: ["read"])

class APIKeySchema(BaseModel):
    id: str
    key_prefix: str
    name: str
    tier: str
    status: str
    rate_limit_per_minute: int
    scopes: list[str]
    created_at: str | None
    total_requests: int

class APIKeyCreatedSchema(BaseModel):
    key: APIKeySchema
    raw_key: str

class UsageSummarySchema(BaseModel):
    total_keys: int
    active_keys: int
    total_requests: int
    requests_by_tier: dict[str, int]
    requests_by_endpoint: dict[str, int]
    avg_response_time_ms: float
    sdk_downloads: dict[str, int]

class RateLimitSchema(BaseModel):
    tier: str
    limit_per_minute: int
    remaining: int


@router.get("/sdks", response_model=list[SDKPackageSchema], summary="List SDK packages")
async def list_sdks(db: DB, language: str | None = None) -> list[SDKPackageSchema]:
    service = ComplianceSDKService(db=db)
    lang = SDKLanguage(language) if language else None
    pkgs = service.list_sdk_packages(language=lang)
    return [
        SDKPackageSchema(
            language=p.language.value, name=p.name, version=p.version,
            install_command=p.install_command, registry_url=p.registry_url, description=p.description,
        ) for p in pkgs
    ]

@router.post("/keys", response_model=APIKeyCreatedSchema, status_code=status.HTTP_201_CREATED, summary="Create API key")
async def create_api_key(request: CreateAPIKeyRequest, db: DB) -> APIKeyCreatedSchema:
    service = ComplianceSDKService(db=db)
    key, raw = await service.create_api_key(
        name=request.name, organization_id=request.organization_id,
        tier=request.tier, scopes=request.scopes,
    )
    return APIKeyCreatedSchema(
        key=APIKeySchema(
            id=str(key.id), key_prefix=key.key_prefix, name=key.name,
            tier=key.tier.value, status=key.status.value,
            rate_limit_per_minute=key.rate_limit_per_minute, scopes=key.scopes,
            created_at=key.created_at.isoformat() if key.created_at else None,
            total_requests=key.total_requests,
        ),
        raw_key=raw,
    )

@router.get("/keys", response_model=list[APIKeySchema], summary="List API keys")
async def list_api_keys(db: DB, organization_id: str | None = None) -> list[APIKeySchema]:
    service = ComplianceSDKService(db=db)
    keys = service.list_api_keys(organization_id=organization_id)
    return [
        APIKeySchema(
            id=str(k.id), key_prefix=k.key_prefix, name=k.name,
            tier=k.tier.value, status=k.status.value,
            rate_limit_per_minute=k.rate_limit_per_minute, scopes=k.scopes,
            created_at=k.created_at.isoformat() if k.created_at else None,
            total_requests=k.total_requests,
        ) for k in keys
    ]

@router.delete("/keys/{key_id}", summary="Revoke API key")
async def revoke_api_key(key_id: UUID, db: DB) -> dict:
    service = ComplianceSDKService(db=db)
    ok = await service.revoke_api_key(key_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key not found")
    return {"status": "revoked", "key_id": str(key_id)}

@router.get("/usage", response_model=UsageSummarySchema, summary="Get usage summary")
async def get_usage_summary(db: DB, organization_id: str | None = None) -> UsageSummarySchema:
    service = ComplianceSDKService(db=db)
    summary = service.get_usage_summary(organization_id=organization_id)
    return UsageSummarySchema(
        total_keys=summary.total_keys, active_keys=summary.active_keys,
        total_requests=summary.total_requests, requests_by_tier=summary.requests_by_tier,
        requests_by_endpoint=summary.requests_by_endpoint,
        avg_response_time_ms=summary.avg_response_time_ms, sdk_downloads=summary.sdk_downloads,
    )
