"""API endpoints for Compliance API Monetization Layer."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.services.api_monetization import APIMonetizationService, PricingTier

logger = structlog.get_logger()
router = APIRouter()


# --- Response Models ---

class ComplianceAPISchema(BaseModel):
    id: str
    name: str
    description: str
    endpoint: str
    regulation: str
    version: str
    status: str
    requests_per_month: int
    avg_latency_ms: float
    pricing_per_request: float
    documentation_url: str
    supported_languages: list[str]
    tags: list[str]


class SubscriptionSchema(BaseModel):
    id: str
    api_id: str
    tier: str
    monthly_quota: int
    monthly_cost: float
    api_key: str


class RevenueStatsSchema(BaseModel):
    total_apis: int
    total_developers: int
    total_requests_month: int
    monthly_revenue: float
    top_api: str
    revenue_growth_pct: float
    avg_revenue_per_api: float


class CreateSubscriptionRequest(BaseModel):
    api_id: str = Field(..., description="API to subscribe to")
    tier: str = Field(..., description="Pricing tier: free, starter, pro, enterprise")


# --- Endpoints ---

@router.get("/apis", response_model=list[ComplianceAPISchema])
async def list_apis(regulation: str | None = Query(None)) -> list[dict]:
    svc = APIMonetizationService()
    apis = await svc.list_apis(regulation=regulation)
    return [
        {"id": a.id, "name": a.name, "description": a.description, "endpoint": a.endpoint,
         "regulation": a.regulation, "version": a.version, "status": a.status.value,
         "requests_per_month": a.requests_per_month, "avg_latency_ms": a.avg_latency_ms,
         "pricing_per_request": a.pricing_per_request, "documentation_url": a.documentation_url,
         "supported_languages": a.supported_languages, "tags": a.tags}
        for a in apis
    ]


@router.get("/apis/{api_id}", response_model=ComplianceAPISchema)
async def get_api(api_id: str) -> dict:
    svc = APIMonetizationService()
    a = await svc.get_api(api_id)
    if not a:
        raise HTTPException(status_code=404, detail="API not found")
    return {
        "id": a.id, "name": a.name, "description": a.description, "endpoint": a.endpoint,
        "regulation": a.regulation, "version": a.version, "status": a.status.value,
        "requests_per_month": a.requests_per_month, "avg_latency_ms": a.avg_latency_ms,
        "pricing_per_request": a.pricing_per_request, "documentation_url": a.documentation_url,
        "supported_languages": a.supported_languages, "tags": a.tags,
    }


@router.post("/subscriptions", response_model=SubscriptionSchema, status_code=status.HTTP_201_CREATED)
async def create_subscription(req: CreateSubscriptionRequest) -> dict:
    svc = APIMonetizationService()
    from uuid import uuid4
    try:
        tier = PricingTier(req.tier)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid tier: {req.tier}")
    sub = await svc.create_subscription(uuid4(), req.api_id, tier)
    return {
        "id": str(sub.id), "api_id": sub.api_id, "tier": sub.tier.value,
        "monthly_quota": sub.monthly_quota, "monthly_cost": sub.monthly_cost,
        "api_key": sub.api_key,
    }


@router.get("/revenue", response_model=RevenueStatsSchema)
async def get_revenue_stats() -> dict:
    svc = APIMonetizationService()
    s = await svc.get_revenue_stats()
    return {
        "total_apis": s.total_apis, "total_developers": s.total_developers,
        "total_requests_month": s.total_requests_month, "monthly_revenue": s.monthly_revenue,
        "top_api": s.top_api, "revenue_growth_pct": s.revenue_growth_pct,
        "avg_revenue_per_api": s.avg_revenue_per_api,
    }
