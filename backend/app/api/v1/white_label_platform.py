"""API endpoints for White Label Platform."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.white_label_platform import WhiteLabelPlatformService


logger = structlog.get_logger()
router = APIRouter()


class OnboardPartnerRequest(BaseModel):
    name: str = Field(...)
    tier: str = Field(...)
    domain: str = Field(...)
    branding: dict = Field(default_factory=dict)


class CreateInstanceRequest(BaseModel):
    partner_id: str = Field(...)
    tenant_name: str = Field(...)


class PartnerSchema(BaseModel):
    id: str
    name: str
    tier: str
    domain: str
    branding: dict
    status: str
    created_at: str | None


class InstanceSchema(BaseModel):
    id: str
    partner_id: str
    tenant_name: str
    status: str
    url: str
    created_at: str | None


class AnalyticsSchema(BaseModel):
    partner_id: str
    active_users: int
    total_scans: int
    revenue: float
    compliance_score: float
    period: str


class StatsSchema(BaseModel):
    total_partners: int
    total_instances: int
    active_instances: int
    total_revenue: float
    avg_compliance_score: float


@router.post(
    "/partners",
    response_model=PartnerSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Onboard partner",
)
async def onboard_partner(request: OnboardPartnerRequest, db: DB) -> PartnerSchema:
    """Onboard a new white-label partner."""
    service = WhiteLabelPlatformService(db=db)
    partner = await service.onboard_partner(
        name=request.name,
        tier=request.tier,
        domain=request.domain,
        branding=request.branding,
    )
    return PartnerSchema(
        id=str(partner.id),
        name=partner.name,
        tier=partner.tier,
        domain=partner.domain,
        branding=partner.branding,
        status=partner.status,
        created_at=partner.created_at.isoformat() if partner.created_at else None,
    )


@router.post(
    "/instances",
    response_model=InstanceSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create instance",
)
async def create_instance(request: CreateInstanceRequest, db: DB) -> InstanceSchema:
    """Create a new tenant instance for a partner."""
    service = WhiteLabelPlatformService(db=db)
    instance = await service.create_instance(
        partner_id=request.partner_id, tenant_name=request.tenant_name
    )
    return InstanceSchema(
        id=str(instance.id),
        partner_id=str(instance.partner_id),
        tenant_name=instance.tenant_name,
        status=instance.status,
        url=instance.url,
        created_at=instance.created_at.isoformat() if instance.created_at else None,
    )


@router.get(
    "/partners/{partner_id}/analytics",
    response_model=AnalyticsSchema,
    summary="Get partner analytics",
)
async def get_partner_analytics(partner_id: UUID, db: DB) -> AnalyticsSchema:
    """Get analytics for a specific partner."""
    service = WhiteLabelPlatformService(db=db)
    analytics = service.get_partner_analytics(partner_id=partner_id)
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found"
        )
    return AnalyticsSchema(
        partner_id=str(analytics.partner_id),
        active_users=analytics.active_users,
        total_scans=analytics.total_scans,
        revenue=analytics.revenue,
        compliance_score=analytics.compliance_score,
        period=analytics.period,
    )


@router.post("/instances/{instance_id}/suspend", summary="Suspend instance")
async def suspend_instance(instance_id: UUID, db: DB) -> dict:
    """Suspend a tenant instance."""
    service = WhiteLabelPlatformService(db=db)
    ok = await service.suspend_instance(instance_id=instance_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Instance not found"
        )
    return {"status": "suspended", "instance_id": str(instance_id)}


@router.get("/partners", response_model=list[PartnerSchema], summary="List partners")
async def list_partners(db: DB) -> list[PartnerSchema]:
    """List all white-label partners."""
    service = WhiteLabelPlatformService(db=db)
    partners = service.list_partners()
    return [
        PartnerSchema(
            id=str(p.id),
            name=p.name,
            tier=p.tier,
            domain=p.domain,
            branding=p.branding,
            status=p.status,
            created_at=p.created_at.isoformat() if p.created_at else None,
        )
        for p in partners
    ]


@router.get(
    "/instances", response_model=list[InstanceSchema], summary="List instances"
)
async def list_instances(db: DB) -> list[InstanceSchema]:
    """List all tenant instances."""
    service = WhiteLabelPlatformService(db=db)
    instances = service.list_instances()
    return [
        InstanceSchema(
            id=str(i.id),
            partner_id=str(i.partner_id),
            tenant_name=i.tenant_name,
            status=i.status,
            url=i.url,
            created_at=i.created_at.isoformat() if i.created_at else None,
        )
        for i in instances
    ]


@router.get("/stats", response_model=StatsSchema, summary="Get stats")
async def get_stats(db: DB) -> StatsSchema:
    """Get white-label platform statistics."""
    service = WhiteLabelPlatformService(db=db)
    stats = service.get_stats()
    return StatsSchema(
        total_partners=stats.total_partners,
        total_instances=stats.total_instances,
        active_instances=stats.active_instances,
        total_revenue=stats.total_revenue,
        avg_compliance_score=stats.avg_compliance_score,
    )
