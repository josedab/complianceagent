"""API endpoints for Client SDK management."""

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.client_sdk import ClientSDKService


logger = structlog.get_logger()
router = APIRouter()


# --- Endpoints ---


@router.get("/endpoints")
async def list_endpoints(
    db: DB,
    method: str | None = Query(None, description="Filter by HTTP method"),
) -> list[dict]:
    """List available API endpoints."""
    svc = ClientSDKService()
    return await svc.list_endpoints(db, method=method)


@router.get("/packages")
async def list_packages(
    db: DB,
    runtime: str | None = Query(None, description="Filter by runtime"),
) -> list[dict]:
    """List available SDK packages."""
    svc = ClientSDKService()
    return await svc.list_packages(db, runtime=runtime)


@router.get("/packages/{runtime}")
async def get_package(runtime: str, db: DB) -> dict:
    """Get SDK package details for a specific runtime."""
    svc = ClientSDKService()
    return await svc.get_package(db, runtime=runtime)


@router.post("/generate/{runtime}")
async def generate_client(runtime: str, db: DB) -> dict:
    """Generate a client SDK for the given runtime."""
    svc = ClientSDKService()
    return await svc.generate_client(db, runtime=runtime)


@router.get("/config")
async def get_default_config(db: DB) -> dict:
    """Get default SDK configuration."""
    svc = ClientSDKService()
    return await svc.get_default_config(db)


@router.get("/stats")
async def get_stats(db: DB) -> dict:
    """Get client SDK statistics."""
    svc = ClientSDKService()
    return await svc.get_stats(db)


# --- Production Endpoints: OAuth2, API Keys, Rate Limits, OpenAPI ---


class OAuth2ClientRequest(BaseModel):
    name: str = Field(..., description="Client application name")
    redirect_uris: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=lambda: ["read", "write"])


class TokenExchangeRequest(BaseModel):
    grant_type: str = Field(default="client_credentials")
    client_id: str = Field(...)
    client_secret: str = Field(...)
    scope: str = Field(default="read write")


class CreateAPIKeyRequest(BaseModel):
    name: str = Field(..., description="Key name")
    tier: str = Field(default="free", description="Rate limit tier")
    scopes: list[str] = Field(default_factory=lambda: ["read"])
    test_mode: bool = Field(default=False)


@router.post("/oauth2/clients", summary="Register OAuth2 client")
async def register_oauth2_client(request: OAuth2ClientRequest, db: DB) -> dict:
    svc = ClientSDKService(db=db)
    client, secret = await svc.register_oauth2_client(
        name=request.name, redirect_uris=request.redirect_uris, scopes=request.scopes,
    )
    return {"client_id": client.client_id, "client_secret": secret, "name": client.name}


@router.post("/oauth2/token", summary="Exchange credentials for token")
async def token_exchange(request: TokenExchangeRequest, db: DB) -> dict:
    svc = ClientSDKService(db=db)
    token = await svc.token_exchange(
        grant_type=request.grant_type, client_id=request.client_id,
        client_secret=request.client_secret, scope=request.scope,
    )
    if not token:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": token.access_token, "token_type": token.token_type, "expires_in": token.expires_in, "scope": token.scope}


@router.post("/api-keys", summary="Create API key")
async def create_api_key(request: CreateAPIKeyRequest, db: DB) -> dict:
    svc = ClientSDKService(db=db)
    key, raw = await svc.create_api_key(
        name=request.name, tier=request.tier, scopes=request.scopes, test_mode=request.test_mode,
    )
    return {"key_id": str(key.id), "api_key": raw, "name": key.name, "tier": key.tier.value}


@router.get("/api-keys", summary="List API keys")
async def list_api_keys(db: DB) -> list[dict]:
    svc = ClientSDKService(db=db)
    keys = svc.list_api_keys()
    return [{"id": str(k.id), "name": k.name, "prefix": k.key_prefix, "tier": k.tier.value, "status": k.status.value, "usage_count": k.usage_count} for k in keys]


@router.delete("/api-keys/{key_id}", summary="Revoke API key")
async def revoke_api_key(key_id: str, db: DB) -> dict:
    svc = ClientSDKService(db=db)
    ok = await svc.revoke_api_key(key_id)
    return {"revoked": ok}


@router.get("/rate-limits", summary="List rate limit tiers")
async def list_rate_limits(db: DB) -> list[dict]:
    svc = ClientSDKService(db=db)
    tiers = svc.list_rate_limit_tiers()
    return [{"tier": t.tier.value, "rpm": t.requests_per_minute, "rph": t.requests_per_hour, "rpd": t.requests_per_day, "burst": t.burst_limit} for t in tiers]


@router.get("/openapi-spec", summary="Get OpenAPI specification")
async def get_openapi_spec(db: DB) -> dict:
    svc = ClientSDKService(db=db)
    return svc.generate_openapi_spec()


@router.get("/developer-portal", summary="Get developer portal content")
async def get_developer_portal(db: DB) -> dict:
    svc = ClientSDKService(db=db)
    return svc.get_developer_portal()
