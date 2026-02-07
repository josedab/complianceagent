"""API endpoints for SaaS Platform management."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentUser
from app.models.saas_tenant import TenantPlan
from app.services.saas_platform import (
    TenantConfig,
    get_saas_platform_service,
)

logger = structlog.get_logger()

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class ProvisionTenantRequest(BaseModel):
    """Request to provision a new tenant."""

    name: str = Field(..., description="Tenant display name")
    slug: str = Field(..., description="Unique tenant slug")
    plan: str = Field(default="free", description="Subscription plan")
    owner_email: str = Field(default="", description="Owner email address")
    industry: str = Field(default="", description="Industry vertical")
    jurisdictions: list[str] = Field(default_factory=list, description="Operating jurisdictions")
    github_org: str = Field(default="", description="GitHub organization")


class TenantResponse(BaseModel):
    """Tenant details response."""

    id: str
    name: str
    slug: str
    plan: str
    status: str
    domain: str | None
    settings: dict[str, Any]
    resource_limits: dict[str, Any]
    trial_ends_at: str | None
    onboarding_completed_at: str | None
    github_installation_id: int | None
    created_at: str


class ProvisionResponse(BaseModel):
    """Response after tenant provisioning."""

    tenant_id: str
    status: str
    api_key: str
    onboarding_steps: list[dict[str, Any]]
    dashboard_url: str


class UpdatePlanRequest(BaseModel):
    """Request to update tenant plan."""

    plan: str = Field(..., description="New plan: free, starter, professional, enterprise")


class SuspendRequest(BaseModel):
    """Request to suspend a tenant."""

    reason: str = Field(..., description="Reason for suspension")


class OnboardingStepResponse(BaseModel):
    """Onboarding step response."""

    id: str
    name: str
    description: str
    status: str
    completed_at: str | None


class UsageSummaryResponse(BaseModel):
    """Usage summary response."""

    tenant_id: str
    period: str
    api_calls: int
    scans_run: int
    regulations_tracked: int
    storage_mb: float
    seats_used: int


class LimitCheckResponse(BaseModel):
    """Resource limit check response."""

    resource: str
    within_limits: bool


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/provision", response_model=ProvisionResponse, status_code=status.HTTP_201_CREATED)
async def provision_tenant(
    request: ProvisionTenantRequest,
    current_user: CurrentUser,
    db: DB,
) -> ProvisionResponse:
    """Provision a new SaaS tenant."""
    service = get_saas_platform_service(db)

    config = TenantConfig(
        name=request.name,
        slug=request.slug,
        plan=request.plan,
        owner_email=request.owner_email,
        industry=request.industry,
        jurisdictions=request.jurisdictions,
        github_org=request.github_org,
    )

    try:
        result = await service.provision_tenant(config)
    except Exception as e:
        logger.error("Failed to provision tenant", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to provision tenant: {e}",
        )

    return ProvisionResponse(
        tenant_id=str(result.tenant_id),
        status=result.status,
        api_key=result.api_key,
        onboarding_steps=[s.to_dict() for s in result.onboarding_steps],
        dashboard_url=result.dashboard_url,
    )


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    current_user: CurrentUser,
    db: DB,
) -> TenantResponse:
    """Get tenant details."""
    service = get_saas_platform_service(db)
    tenant = await service.get_tenant(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        plan=tenant.plan.value,
        status=tenant.status.value,
        domain=tenant.domain,
        settings=tenant.settings,
        resource_limits=tenant.resource_limits,
        trial_ends_at=tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
        onboarding_completed_at=tenant.onboarding_completed_at.isoformat() if tenant.onboarding_completed_at else None,
        github_installation_id=tenant.github_installation_id,
        created_at=tenant.created_at.isoformat(),
    )


@router.put("/{tenant_id}/plan", response_model=TenantResponse)
async def update_tenant_plan(
    tenant_id: UUID,
    request: UpdatePlanRequest,
    current_user: CurrentUser,
    db: DB,
) -> TenantResponse:
    """Update a tenant's subscription plan."""
    service = get_saas_platform_service(db)

    try:
        plan = TenantPlan(request.plan)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan: {request.plan}. Valid plans: {[p.value for p in TenantPlan]}",
        )

    try:
        tenant = await service.update_tenant_plan(tenant_id, plan)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return TenantResponse(
        id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        plan=tenant.plan.value,
        status=tenant.status.value,
        domain=tenant.domain,
        settings=tenant.settings,
        resource_limits=tenant.resource_limits,
        trial_ends_at=tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
        onboarding_completed_at=tenant.onboarding_completed_at.isoformat() if tenant.onboarding_completed_at else None,
        github_installation_id=tenant.github_installation_id,
        created_at=tenant.created_at.isoformat(),
    )


@router.post("/{tenant_id}/suspend", status_code=status.HTTP_204_NO_CONTENT)
async def suspend_tenant(
    tenant_id: UUID,
    request: SuspendRequest,
    current_user: CurrentUser,
    db: DB,
) -> None:
    """Suspend a tenant."""
    service = get_saas_platform_service(db)

    try:
        await service.suspend_tenant(tenant_id, request.reason)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{tenant_id}/onboarding", response_model=list[OnboardingStepResponse])
async def get_onboarding_status(
    tenant_id: UUID,
    current_user: CurrentUser,
    db: DB,
) -> list[OnboardingStepResponse]:
    """Get onboarding status for a tenant."""
    service = get_saas_platform_service(db)

    try:
        steps = await service.get_onboarding_status(tenant_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return [
        OnboardingStepResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            status=s.status,
            completed_at=s.completed_at.isoformat() if s.completed_at else None,
        )
        for s in steps
    ]


@router.post(
    "/{tenant_id}/onboarding/{step_id}/complete",
    response_model=OnboardingStepResponse,
)
async def complete_onboarding_step(
    tenant_id: UUID,
    step_id: str,
    current_user: CurrentUser,
    db: DB,
) -> OnboardingStepResponse:
    """Complete an onboarding step."""
    service = get_saas_platform_service(db)

    try:
        step = await service.complete_onboarding_step(tenant_id, step_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return OnboardingStepResponse(
        id=step.id,
        name=step.name,
        description=step.description,
        status=step.status,
        completed_at=step.completed_at.isoformat() if step.completed_at else None,
    )


@router.get("/{tenant_id}/usage", response_model=UsageSummaryResponse)
async def get_usage_summary(
    tenant_id: UUID,
    current_user: CurrentUser,
    db: DB,
) -> UsageSummaryResponse:
    """Get usage summary for a tenant."""
    service = get_saas_platform_service(db)

    summary = await service.get_usage_summary(tenant_id)

    return UsageSummaryResponse(
        tenant_id=str(summary.tenant_id),
        period=summary.period,
        api_calls=summary.api_calls,
        scans_run=summary.scans_run,
        regulations_tracked=summary.regulations_tracked,
        storage_mb=summary.storage_mb,
        seats_used=summary.seats_used,
    )


@router.get("/{tenant_id}/limits/check", response_model=LimitCheckResponse)
async def check_resource_limit(
    tenant_id: UUID,
    resource: str = Query(..., description="Resource to check: repos, scans, api_calls, seats, storage"),
    current_user: CurrentUser = None,
    db: DB = None,
) -> LimitCheckResponse:
    """Check if a tenant is within resource limits."""
    service = get_saas_platform_service(db)

    try:
        within_limits = await service.check_resource_limits(tenant_id, resource)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return LimitCheckResponse(
        resource=resource,
        within_limits=within_limits,
    )
