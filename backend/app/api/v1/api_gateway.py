"""API endpoints for Compliance API Gateway."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.api_gateway import APIGatewayService


logger = structlog.get_logger()
router = APIRouter()


class CreateClientRequest(BaseModel):
    name: str = Field(...)
    description: str = Field(default="")
    scopes: list[str] = Field(default_factory=list)
    rate_limit_per_minute: int = Field(default=60)
    webhook_url: str = Field(default="")


class ClientSchema(BaseModel):
    id: str
    name: str
    description: str
    api_key: str
    scopes: list[str]
    rate_limit_per_minute: int
    webhook_url: str
    active: bool
    created_at: str | None


class RateLimitSchema(BaseModel):
    client_id: str
    limit_per_minute: int
    remaining: int
    reset_at: str | None
    total_requests: int


class PortalSchema(BaseModel):
    total_clients: int
    active_clients: int
    endpoints: list[dict[str, Any]]
    api_version: str
    docs_url: str


class GatewayStatsSchema(BaseModel):
    total_clients: int
    active_clients: int
    total_requests: int
    requests_today: int
    rate_limited_count: int
    by_endpoint: dict[str, int]
    by_client: dict[str, int]


@router.post("/clients", response_model=ClientSchema, status_code=status.HTTP_201_CREATED, summary="Create API client")
async def create_client(request: CreateClientRequest, db: DB) -> ClientSchema:
    service = APIGatewayService(db=db)
    c = await service.create_client(
        name=request.name, description=request.description, scopes=request.scopes,
        rate_limit_per_minute=request.rate_limit_per_minute, webhook_url=request.webhook_url,
    )
    return ClientSchema(
        id=str(c.id), name=c.name, description=c.description, api_key=c.api_key,
        scopes=c.scopes, rate_limit_per_minute=c.rate_limit_per_minute,
        webhook_url=c.webhook_url, active=c.active,
        created_at=c.created_at.isoformat() if c.created_at else None,
    )


@router.get("/clients", response_model=list[ClientSchema], summary="List API clients")
async def list_clients(db: DB, active_only: bool = False) -> list[ClientSchema]:
    service = APIGatewayService(db=db)
    clients = service.list_clients(active_only=active_only)
    return [
        ClientSchema(
            id=str(c.id), name=c.name, description=c.description, api_key=c.api_key,
            scopes=c.scopes, rate_limit_per_minute=c.rate_limit_per_minute,
            webhook_url=c.webhook_url, active=c.active,
            created_at=c.created_at.isoformat() if c.created_at else None,
        )
        for c in clients
    ]


@router.delete("/clients/{client_id}", summary="Delete API client")
async def delete_client(client_id: str, db: DB) -> dict:
    service = APIGatewayService(db=db)
    ok = await service.delete_client(client_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return {"status": "deleted", "client_id": client_id}


@router.get("/rate-limit/{client_id}", response_model=RateLimitSchema, summary="Get rate limit status")
async def get_rate_limit(client_id: str, db: DB) -> RateLimitSchema:
    service = APIGatewayService(db=db)
    r = service.get_rate_limit(client_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return RateLimitSchema(
        client_id=str(r.client_id), limit_per_minute=r.limit_per_minute,
        remaining=r.remaining, reset_at=r.reset_at.isoformat() if r.reset_at else None,
        total_requests=r.total_requests,
    )


@router.get("/portal", response_model=PortalSchema, summary="Get developer portal info")
async def get_portal(db: DB) -> PortalSchema:
    service = APIGatewayService(db=db)
    p = service.get_portal()
    return PortalSchema(
        total_clients=p.total_clients, active_clients=p.active_clients,
        endpoints=p.endpoints, api_version=p.api_version, docs_url=p.docs_url,
    )


@router.get("/stats", response_model=GatewayStatsSchema, summary="Get gateway stats")
async def get_stats(db: DB) -> GatewayStatsSchema:
    service = APIGatewayService(db=db)
    s = service.get_stats()
    return GatewayStatsSchema(
        total_clients=s.total_clients, active_clients=s.active_clients,
        total_requests=s.total_requests, requests_today=s.requests_today,
        rate_limited_count=s.rate_limited_count, by_endpoint=s.by_endpoint,
        by_client=s.by_client,
    )
