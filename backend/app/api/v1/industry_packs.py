"""API endpoints for Industry Compliance Starter Packs."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB

from app.services.industry_packs import IndustryPacksService, IndustryVertical


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class RegulationBundleSchema(BaseModel):
    """Regulation bundle in a pack."""

    framework: str
    name: str
    description: str
    mandatory: bool


class PolicyTemplateSchema(BaseModel):
    """Policy template summary."""

    id: str
    name: str
    description: str
    category: str


class PackSummarySchema(BaseModel):
    """Industry pack summary."""

    vertical: str
    name: str
    description: str
    version: str
    regulations_count: int
    policies_count: int
    estimated_setup_minutes: int


class PackDetailSchema(PackSummarySchema):
    """Detailed industry pack."""

    regulations: list[RegulationBundleSchema]
    policies: list[PolicyTemplateSchema]
    recommended_jurisdictions: list[str]
    tech_stack_recommendations: dict[str, Any]
    setup_checklist: list[str]


class ProvisionRequest(BaseModel):
    """Provision pack request."""

    vertical: str = Field(..., description="Industry vertical")
    jurisdictions: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)


class ProvisionResponse(BaseModel):
    """Provision result."""

    pack_id: str
    vertical: str
    regulations_activated: int
    policies_created: int
    scans_triggered: int
    setup_checklist: list[str]
    next_steps: list[str]


class WizardStepRequest(BaseModel):
    """Wizard step advance request."""

    vertical: str | None = None
    jurisdictions: list[str] | None = None
    tech_stack: list[str] | None = None


class WizardStateResponse(BaseModel):
    """Wizard state response."""

    step: int
    total_steps: int
    vertical: str | None
    jurisdictions: list[str]
    tech_stack: list[str]
    completed: bool


# --- Endpoints ---


@router.get(
    "",
    response_model=list[PackSummarySchema],
    summary="List industry packs",
    description="List available industry compliance starter packs",
)
async def list_packs(
    db: DB,
    vertical: str | None = None,
) -> list[PackSummarySchema]:
    """List available industry packs."""
    service = IndustryPacksService(db=db)
    v = IndustryVertical(vertical) if vertical else None
    packs = await service.list_packs(vertical=v)
    return [
        PackSummarySchema(
            vertical=p.vertical.value,
            name=p.name,
            description=p.description,
            version=p.version,
            regulations_count=len(p.regulations),
            policies_count=len(p.policies),
            estimated_setup_minutes=p.estimated_setup_minutes,
        )
        for p in packs
    ]


@router.get(
    "/{vertical}",
    response_model=PackDetailSchema,
    summary="Get industry pack",
)
async def get_pack(
    vertical: str,
    db: DB,
) -> PackDetailSchema:
    """Get detailed industry pack."""
    service = IndustryPacksService(db=db)
    pack = await service.get_pack(IndustryVertical(vertical))
    if not pack:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pack not found")

    return PackDetailSchema(
        vertical=pack.vertical.value,
        name=pack.name,
        description=pack.description,
        version=pack.version,
        regulations_count=len(pack.regulations),
        policies_count=len(pack.policies),
        estimated_setup_minutes=pack.estimated_setup_minutes,
        regulations=[
            RegulationBundleSchema(
                framework=r.framework, name=r.name,
                description=r.description, mandatory=r.mandatory,
            )
            for r in pack.regulations
        ],
        policies=[
            PolicyTemplateSchema(
                id=str(p.id), name=p.name,
                description=p.description, category=p.category,
            )
            for p in pack.policies
        ],
        recommended_jurisdictions=pack.recommended_jurisdictions,
        tech_stack_recommendations=pack.tech_stack_recommendations,
        setup_checklist=pack.setup_checklist,
    )


@router.post(
    "/provision",
    response_model=ProvisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Provision industry pack",
)
async def provision_pack(
    request: ProvisionRequest,
    db: DB,
) -> ProvisionResponse:
    """Provision an industry pack for the current tenant."""
    service = IndustryPacksService(db=db)
    result = await service.provision_pack(
        vertical=IndustryVertical(request.vertical),
        jurisdictions=request.jurisdictions,
        tech_stack=request.tech_stack,
    )
    return ProvisionResponse(
        pack_id=str(result.pack_id),
        vertical=result.vertical.value,
        regulations_activated=result.regulations_activated,
        policies_created=result.policies_created,
        scans_triggered=result.scans_triggered,
        setup_checklist=result.setup_checklist,
        next_steps=result.next_steps,
    )


@router.get(
    "/verticals",
    summary="List supported verticals",
)
async def list_verticals() -> dict:
    """List supported industry verticals."""
    return {
        "verticals": [
            {"value": v.value, "name": v.value.replace("_", " ").title()}
            for v in IndustryVertical
        ]
    }
