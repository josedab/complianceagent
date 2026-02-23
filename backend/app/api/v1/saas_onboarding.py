"""API endpoints for Zero-Config Compliance SaaS."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.saas_onboarding import SaaSOnboardingService


logger = structlog.get_logger()
router = APIRouter()


class CreateTenantRequest(BaseModel):
    name: str = Field(...)
    owner_email: str = Field(...)
    plan: str = Field(default="free")
    region: str = Field(default="us-east-1")


class TenantSchema(BaseModel):
    id: str
    name: str
    slug: str
    owner_email: str
    plan: str
    status: str
    repo_limit: int
    repos_connected: int
    onboarding_step: str
    onboarding_completed: bool
    created_at: str | None


class AdvanceOnboardingRequest(BaseModel):
    step: str = Field(...)
    data: dict[str, Any] = Field(default_factory=dict)


class ProgressSchema(BaseModel):
    current_step: str
    steps_completed: list[str]
    time_to_first_scan_seconds: float | None
    completed_at: str | None


class UsageLimitsSchema(BaseModel):
    plan: str
    max_repos: int
    max_scans_per_day: int
    max_api_calls_per_minute: int
    ai_features_enabled: bool
    sso_enabled: bool
    support_tier: str


class MetricsSchema(BaseModel):
    total_tenants: int
    active_tenants: int
    by_plan: dict[str, int]
    avg_time_to_first_scan_min: float
    onboarding_completion_rate: float
    total_repos_connected: int


def _tenant_to_schema(t: Any) -> TenantSchema:
    return TenantSchema(
        id=str(t.id),
        name=t.name,
        slug=t.slug,
        owner_email=t.owner_email,
        plan=t.plan.value,
        status=t.status.value,
        repo_limit=t.repo_limit,
        repos_connected=t.repos_connected,
        onboarding_step=t.onboarding_step.value,
        onboarding_completed=t.onboarding_completed,
        created_at=t.created_at.isoformat() if t.created_at else None,
    )


@router.post(
    "/tenants",
    response_model=TenantSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create tenant",
)
async def create_tenant(request: CreateTenantRequest, db: DB) -> TenantSchema:
    service = SaaSOnboardingService(db=db)
    t = await service.create_tenant(
        name=request.name,
        owner_email=request.owner_email,
        plan=request.plan,
        region=request.region,
    )
    return _tenant_to_schema(t)


@router.get("/tenants/{slug}", response_model=TenantSchema, summary="Get tenant")
async def get_tenant(slug: str, db: DB) -> TenantSchema:
    service = SaaSOnboardingService(db=db)
    t = service.get_tenant(slug)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return _tenant_to_schema(t)


@router.post(
    "/tenants/{slug}/onboarding",
    response_model=ProgressSchema,
    summary="Advance onboarding",
)
async def advance_onboarding(
    slug: str, request: AdvanceOnboardingRequest, db: DB
) -> ProgressSchema:
    service = SaaSOnboardingService(db=db)
    p = await service.advance_onboarding(slug, request.step, request.data)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return ProgressSchema(
        current_step=p.current_step.value,
        steps_completed=p.steps_completed,
        time_to_first_scan_seconds=p.time_to_first_scan_seconds,
        completed_at=p.completed_at.isoformat() if p.completed_at else None,
    )


@router.put("/tenants/{slug}/plan", response_model=TenantSchema, summary="Upgrade plan")
async def upgrade_plan(slug: str, plan: str, db: DB) -> TenantSchema:
    service = SaaSOnboardingService(db=db)
    t = await service.upgrade_plan(slug, plan)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return _tenant_to_schema(t)


@router.get(
    "/plans/{plan}/limits",
    response_model=UsageLimitsSchema,
    summary="Get plan limits",
)
async def get_plan_limits(plan: str, db: DB) -> UsageLimitsSchema:
    service = SaaSOnboardingService(db=db)
    l = service.get_usage_limits(plan)
    return UsageLimitsSchema(
        plan=l.plan.value,
        max_repos=l.max_repos,
        max_scans_per_day=l.max_scans_per_day,
        max_api_calls_per_minute=l.max_api_calls_per_minute,
        ai_features_enabled=l.ai_features_enabled,
        sso_enabled=l.sso_enabled,
        support_tier=l.support_tier,
    )


@router.get("/metrics", response_model=MetricsSchema, summary="Get SaaS metrics")
async def get_metrics(db: DB) -> MetricsSchema:
    service = SaaSOnboardingService(db=db)
    m = service.get_metrics()
    return MetricsSchema(
        total_tenants=m.total_tenants,
        active_tenants=m.active_tenants,
        by_plan=m.by_plan,
        avg_time_to_first_scan_min=m.avg_time_to_first_scan_min,
        onboarding_completion_rate=m.onboarding_completion_rate,
        total_repos_connected=m.total_repos_connected,
    )
