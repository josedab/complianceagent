"""API endpoints for Industry Compliance Starter Packs."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization
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


class WizardQuestionSchema(BaseModel):
    """A question in a wizard step."""

    id: str
    question: str
    question_type: str
    options: list[dict[str, str]]
    required: bool
    depends_on: str | None
    depends_value: str | None


class WizardStepSchema(BaseModel):
    """A step in the guided onboarding wizard."""

    step_type: str
    title: str
    description: str
    questions: list[WizardQuestionSchema]
    completed: bool
    answers: dict[str, Any]


class ProvisionWithWizardRequest(BaseModel):
    """Provision with wizard answers request."""

    vertical: str = Field(..., description="Industry vertical")
    wizard_answers: dict[str, Any] = Field(default_factory=dict, description="Answers from wizard")


class ProvisioningResultSchema(BaseModel):
    """Provisioning result from wizard."""

    id: str
    vertical: str
    status: str
    regulations_activated: int
    policies_created: int
    scan_configs_created: int
    frameworks_registered: int
    checklist_items: list[dict[str, Any]]
    warnings: list[str]
    provisioned_at: str


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
                framework=r.framework,
                name=r.name,
                description=r.description,
                mandatory=r.mandatory,
            )
            for r in pack.regulations
        ],
        policies=[
            PolicyTemplateSchema(
                id=str(p.id),
                name=p.name,
                description=p.description,
                category=p.category,
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


@router.post(
    "/provision-wizard",
    response_model=ProvisioningResultSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Provision with wizard",
)
async def provision_with_wizard(
    request: ProvisionWithWizardRequest,
    db: DB,
) -> ProvisioningResultSchema:
    """Provision an industry pack using guided wizard answers."""
    service = IndustryPacksService(db=db)
    result = await service.provision_with_wizard(request.vertical, request.wizard_answers)
    return ProvisioningResultSchema(**result.to_dict())


@router.get(
    "/verticals",
    summary="List supported verticals",
)
async def list_verticals() -> dict:
    """List supported industry verticals."""
    return {
        "verticals": [
            {"value": v.value, "name": v.value.replace("_", " ").title()} for v in IndustryVertical
        ]
    }


@router.get(
    "/{vertical}/wizard",
    response_model=list[WizardStepSchema],
    summary="Get wizard steps",
)
async def get_wizard_steps(
    vertical: str,
    db: DB,
) -> list[WizardStepSchema]:
    """Get guided onboarding wizard steps for an industry vertical."""
    service = IndustryPacksService(db=db)
    steps = service.get_wizard_steps(vertical)
    return [WizardStepSchema(**s.to_dict()) for s in steps]


# ---------------------------------------------------------------------------
# v2: Enhanced Starter Packs with Onboarding Wizard
# ---------------------------------------------------------------------------


class StarterPackSchema(BaseModel):
    """An industry starter pack configuration."""

    id: str
    industry: str
    name: str
    description: str
    regulations: list[str]
    lint_rules: list[str]
    policy_templates: list[str]
    cicd_checks: list[str]
    estimated_setup_minutes: int
    icon: str


class ProvisionRequest(BaseModel):
    """Request to provision a starter pack."""

    pack_id: str = Field(..., description="Pack ID: fintech, healthtech, ai_company, ecommerce")


class OnboardingProgressSchema(BaseModel):
    """Onboarding wizard progress."""

    provision_id: str
    pack_id: str
    total_steps: int
    completed_steps: int
    progress_pct: float
    is_complete: bool
    steps: list[dict]


class UpdateStepRequest(BaseModel):
    """Request to update an onboarding step."""

    step_id: str
    status: str = Field("completed", description="Status: pending, in_progress, completed, skipped")


@router.get(
    "/v2/starter-packs", response_model=list[StarterPackSchema], summary="List starter packs"
)
async def list_starter_packs() -> list[StarterPackSchema]:
    """List all available industry compliance starter packs."""
    from app.services.industry_packs.starter_packs import StarterPackService

    service = StarterPackService()
    packs = service.list_packs()
    return [
        StarterPackSchema(
            id=p.id,
            industry=p.industry.value,
            name=p.name,
            description=p.description,
            regulations=p.regulations,
            lint_rules=p.lint_rules,
            policy_templates=p.policy_templates,
            cicd_checks=p.cicd_checks,
            estimated_setup_minutes=p.estimated_setup_minutes,
            icon=p.icon,
        )
        for p in packs
    ]


@router.get(
    "/v2/starter-packs/{pack_id}", response_model=StarterPackSchema, summary="Get starter pack"
)
async def get_starter_pack(pack_id: str) -> StarterPackSchema:
    """Get a specific starter pack by ID."""
    from app.services.industry_packs.starter_packs import StarterPackService

    service = StarterPackService()
    pack = service.get_pack(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail=f"Pack '{pack_id}' not found")
    return StarterPackSchema(
        id=pack.id,
        industry=pack.industry.value,
        name=pack.name,
        description=pack.description,
        regulations=pack.regulations,
        lint_rules=pack.lint_rules,
        policy_templates=pack.policy_templates,
        cicd_checks=pack.cicd_checks,
        estimated_setup_minutes=pack.estimated_setup_minutes,
        icon=pack.icon,
    )


@router.post("/v2/provision", summary="Provision a starter pack")
async def provision_starter_pack(
    request: ProvisionRequest,
    organization: CurrentOrganization,
) -> dict:
    """Provision a starter pack for the current organization."""
    from app.services.industry_packs.starter_packs import StarterPackService

    service = StarterPackService()
    result = await service.provision(
        organization_id=str(organization.id),
        pack_id=request.pack_id,
    )
    return {
        "provision_id": str(result.id),
        "pack_id": result.pack_id,
        "industry": result.industry,
        "regulations_enabled": result.regulations_enabled,
        "policies_created": result.policies_created,
        "lint_rules_enabled": result.lint_rules_enabled,
        "cicd_configured": result.cicd_configured,
    }


@router.get(
    "/v2/onboarding/{provision_id}",
    response_model=OnboardingProgressSchema,
    summary="Onboarding progress",
)
async def get_onboarding_progress(provision_id: str) -> OnboardingProgressSchema:
    """Get onboarding wizard progress for a provisioned pack."""
    from uuid import UUID

    from app.services.industry_packs.starter_packs import StarterPackService

    service = StarterPackService()
    progress = await service.get_onboarding_progress(UUID(provision_id))
    if "error" in progress:
        raise HTTPException(status_code=404, detail=progress["error"])
    return OnboardingProgressSchema(**progress)


@router.put("/v2/onboarding/{provision_id}/steps", summary="Update onboarding step")
async def update_onboarding_step(
    provision_id: str,
    request: UpdateStepRequest,
) -> dict:
    """Update the status of an onboarding step."""
    from uuid import UUID

    from app.services.industry_packs.starter_packs import OnboardingStepStatus, StarterPackService

    service = StarterPackService()
    result = await service.update_onboarding_step(
        provision_id=UUID(provision_id),
        step_id=request.step_id,
        status=OnboardingStepStatus(request.status),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Provision not found")
    return {"status": "updated", "step_id": request.step_id}
