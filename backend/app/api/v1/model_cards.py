"""API endpoints for AI Model Card Generator."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.model_cards import (
    ModelType,
    BiasCategory,
    ModelCardGenerator,
    get_model_card_generator,
)


router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class PerformanceMetricsRequest(BaseModel):
    """Performance metrics for model card."""
    
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1_score: float | None = None
    auc_roc: float | None = None
    custom_metrics: dict[str, float] = Field(default_factory=dict)


class FairnessMetricsRequest(BaseModel):
    """Fairness metrics for model card."""
    
    demographic_parity: dict[str, float] = Field(default_factory=dict)
    disparate_impact: dict[str, float] = Field(default_factory=dict)
    bias_detected: list[str] = Field(default_factory=list)
    bias_severity: dict[str, str] = Field(default_factory=dict)
    mitigation_techniques: list[str] = Field(default_factory=list)


class IntendedUseRequest(BaseModel):
    """Intended use documentation."""
    
    primary_uses: list[str] = Field(default_factory=list)
    primary_users: list[str] = Field(default_factory=list)
    prohibited_uses: list[str] = Field(default_factory=list)
    human_oversight_required: bool = True
    oversight_description: str | None = None


class TrainingDataRequest(BaseModel):
    """Training data documentation."""
    
    data_sources: list[str] = Field(default_factory=list)
    total_samples: int | None = None
    contains_pii: bool = False
    pii_handling: str | None = None
    preprocessing_steps: list[str] = Field(default_factory=list)


class LimitationsRequest(BaseModel):
    """Model limitations documentation."""
    
    technical_limitations: list[str] = Field(default_factory=list)
    out_of_scope_uses: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)


class CreateModelCardRequest(BaseModel):
    """Request to create a model card."""
    
    model_name: str
    model_version: str
    model_type: str
    description: str
    developers: list[str] = Field(default_factory=list)
    license: str | None = None
    framework: str | None = None
    architecture: str | None = None
    intended_use: IntendedUseRequest | None = None
    training_data: TrainingDataRequest | None = None
    performance: PerformanceMetricsRequest | None = None
    fairness: FairnessMetricsRequest | None = None
    limitations: LimitationsRequest | None = None


class UpdateModelCardRequest(BaseModel):
    """Request to update a model card."""
    
    description: str | None = None
    developers: list[str] | None = None
    license: str | None = None


class ModelCardSummaryResponse(BaseModel):
    """Summary response for a model card."""
    
    id: str
    model_name: str
    model_version: str
    model_type: str
    short_description: str | None
    risk_level: str | None
    category: str | None
    compliance_score: float
    status: str
    created_at: str
    updated_at: str


class RiskClassificationResponse(BaseModel):
    """Response for risk classification."""
    
    risk_level: str
    category: str | None
    prohibited_practice: str | None
    requirements: list[str]
    can_deploy: bool
    conformity_assessment_required: bool
    transparency_requirements: str | None
    reason: str | None = None


class ComplianceGapsResponse(BaseModel):
    """Response for compliance gap assessment."""
    
    compliance_score: float
    gaps_count: int
    gaps: list[str]
    recommendations: list[str]
    ready_for_deployment: bool
    risk_level: str | None


class ModelCardDetailResponse(BaseModel):
    """Detailed model card response."""
    
    id: str
    model_name: str
    model_version: str
    model_type: str
    description: str
    developers: list[str]
    license: str | None
    framework: str | None
    architecture: str | None
    
    # Compliance info
    risk_level: str | None
    category: str | None
    compliance_score: float
    conformity_assessment_required: bool
    conformity_assessment_completed: bool
    
    # Documentation sections
    intended_use: dict[str, Any]
    training_data: dict[str, Any]
    performance: dict[str, Any]
    fairness: dict[str, Any]
    limitations: dict[str, Any]
    ethical_considerations: dict[str, Any]
    regulatory: dict[str, Any]
    
    status: str
    created_at: str
    updated_at: str


# ============================================================================
# Card Management Endpoints
# ============================================================================


@router.post("/cards", response_model=ModelCardSummaryResponse)
async def create_model_card(
    request: CreateModelCardRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ModelCardSummaryResponse:
    """Create a new AI Model Card.
    
    Model cards document AI systems for EU AI Act compliance, including:
    - Model description and intended use
    - Training data and performance metrics
    - Fairness assessment and limitations
    - Regulatory classification
    """
    generator = get_model_card_generator()
    
    try:
        model_type = ModelType(request.model_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model type. Valid types: {[t.value for t in ModelType]}",
        )
    
    # Build kwargs for optional sections
    kwargs: dict[str, Any] = {
        "developers": request.developers,
        "license": request.license,
        "framework": request.framework,
        "architecture": request.architecture,
    }
    
    card = await generator.create_model_card(
        model_name=request.model_name,
        model_version=request.model_version,
        model_type=model_type,
        description=request.description,
        organization_id=organization.id,
        **kwargs,
    )
    
    # Update sections if provided
    if request.intended_use:
        card.intended_use.primary_uses = request.intended_use.primary_uses
        card.intended_use.primary_users = request.intended_use.primary_users
        card.intended_use.prohibited_uses = request.intended_use.prohibited_uses
        card.intended_use.human_oversight_required = request.intended_use.human_oversight_required
        card.intended_use.oversight_description = request.intended_use.oversight_description
    
    if request.training_data:
        card.training_data.data_sources = request.training_data.data_sources
        card.training_data.total_samples = request.training_data.total_samples
        card.training_data.contains_pii = request.training_data.contains_pii
        card.training_data.pii_handling = request.training_data.pii_handling
        card.training_data.preprocessing_steps = request.training_data.preprocessing_steps
    
    if request.performance:
        card.performance.accuracy = request.performance.accuracy
        card.performance.precision = request.performance.precision
        card.performance.recall = request.performance.recall
        card.performance.f1_score = request.performance.f1_score
        card.performance.auc_roc = request.performance.auc_roc
        card.performance.custom_metrics = request.performance.custom_metrics
    
    if request.fairness:
        card.fairness.demographic_parity = request.fairness.demographic_parity
        card.fairness.disparate_impact = request.fairness.disparate_impact
        card.fairness.bias_detected = [BiasCategory(b) for b in request.fairness.bias_detected if b in [e.value for e in BiasCategory]]
        card.fairness.bias_severity = request.fairness.bias_severity
        card.fairness.mitigation_techniques = request.fairness.mitigation_techniques
    
    if request.limitations:
        card.limitations.technical_limitations = request.limitations.technical_limitations
        card.limitations.out_of_scope_uses = request.limitations.out_of_scope_uses
        card.limitations.failure_modes = request.limitations.failure_modes
    
    return ModelCardSummaryResponse(
        id=str(card.id),
        model_name=card.model_name,
        model_version=card.model_version,
        model_type=card.model_type.value,
        short_description=card.description[:100] + "..." if len(card.description) > 100 else card.description,
        risk_level=card.regulatory.eu_ai_act_risk_level.value if card.regulatory.eu_ai_act_risk_level else None,
        category=card.regulatory.eu_ai_act_category.value if card.regulatory.eu_ai_act_category else None,
        compliance_score=card.get_compliance_score(),
        status=card.status,
        created_at=card.created_at.isoformat(),
        updated_at=card.updated_at.isoformat(),
    )


@router.get("/cards", response_model=list[ModelCardSummaryResponse])
async def list_model_cards(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[ModelCardSummaryResponse]:
    """List all model cards for the organization."""
    generator = get_model_card_generator()
    cards = await generator.list_model_cards(organization_id=organization.id)
    
    return [
        ModelCardSummaryResponse(
            id=str(card.id),
            model_name=card.model_name,
            model_version=card.model_version,
            model_type=card.model_type.value,
            short_description=card.description[:100] + "..." if len(card.description) > 100 else card.description,
            risk_level=card.regulatory.eu_ai_act_risk_level.value if card.regulatory.eu_ai_act_risk_level else None,
            category=card.regulatory.eu_ai_act_category.value if card.regulatory.eu_ai_act_category else None,
            compliance_score=card.get_compliance_score(),
            status=card.status,
            created_at=card.created_at.isoformat(),
            updated_at=card.updated_at.isoformat(),
        )
        for card in cards
    ]


@router.get("/cards/{card_id}", response_model=ModelCardDetailResponse)
async def get_model_card(
    card_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ModelCardDetailResponse:
    """Get a model card by ID with full details."""
    generator = get_model_card_generator()
    
    try:
        card_uuid = UUID(card_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid card ID format",
        )
    
    card = await generator.get_model_card(card_uuid)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model card not found",
        )
    
    return ModelCardDetailResponse(
        id=str(card.id),
        model_name=card.model_name,
        model_version=card.model_version,
        model_type=card.model_type.value,
        description=card.description,
        developers=card.developers,
        license=card.license,
        framework=card.framework,
        architecture=card.architecture,
        risk_level=card.regulatory.eu_ai_act_risk_level.value if card.regulatory.eu_ai_act_risk_level else None,
        category=card.regulatory.eu_ai_act_category.value if card.regulatory.eu_ai_act_category else None,
        compliance_score=card.get_compliance_score(),
        conformity_assessment_required=card.regulatory.conformity_assessment_required,
        conformity_assessment_completed=card.regulatory.conformity_assessment_completed,
        intended_use={
            "primary_uses": card.intended_use.primary_uses,
            "primary_users": card.intended_use.primary_users,
            "prohibited_uses": card.intended_use.prohibited_uses,
            "human_oversight_required": card.intended_use.human_oversight_required,
            "oversight_description": card.intended_use.oversight_description,
        },
        training_data={
            "data_sources": card.training_data.data_sources,
            "total_samples": card.training_data.total_samples,
            "contains_pii": card.training_data.contains_pii,
            "pii_handling": card.training_data.pii_handling,
            "preprocessing_steps": card.training_data.preprocessing_steps,
        },
        performance={
            "accuracy": card.performance.accuracy,
            "precision": card.performance.precision,
            "recall": card.performance.recall,
            "f1_score": card.performance.f1_score,
            "auc_roc": card.performance.auc_roc,
            "custom_metrics": card.performance.custom_metrics,
        },
        fairness={
            "demographic_parity": card.fairness.demographic_parity,
            "disparate_impact": card.fairness.disparate_impact,
            "bias_detected": [b.value for b in card.fairness.bias_detected],
            "bias_severity": card.fairness.bias_severity,
            "mitigation_techniques": card.fairness.mitigation_techniques,
        },
        limitations={
            "technical_limitations": card.limitations.technical_limitations,
            "out_of_scope_uses": card.limitations.out_of_scope_uses,
            "failure_modes": card.limitations.failure_modes,
        },
        ethical_considerations={
            "ethics_review_conducted": card.ethical_considerations.ethics_review_conducted,
            "ethical_risks": card.ethical_considerations.ethical_risks,
            "risk_mitigations": card.ethical_considerations.risk_mitigations,
            "affected_stakeholders": card.ethical_considerations.affected_stakeholders,
        },
        regulatory={
            "eu_ai_act_risk_level": card.regulatory.eu_ai_act_risk_level.value if card.regulatory.eu_ai_act_risk_level else None,
            "eu_ai_act_category": card.regulatory.eu_ai_act_category.value if card.regulatory.eu_ai_act_category else None,
            "conformity_assessment_required": card.regulatory.conformity_assessment_required,
            "conformity_assessment_completed": card.regulatory.conformity_assessment_completed,
            "gdpr_compliant": card.regulatory.gdpr_compliant,
            "dpia_conducted": card.regulatory.dpia_conducted,
        },
        status=card.status,
        created_at=card.created_at.isoformat(),
        updated_at=card.updated_at.isoformat(),
    )


# ============================================================================
# Classification Endpoints
# ============================================================================


@router.post("/cards/{card_id}/classify", response_model=RiskClassificationResponse)
async def classify_risk(
    card_id: str,
    use_case_description: str | None = None,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> RiskClassificationResponse:
    """Classify AI system risk level per EU AI Act.
    
    Determines:
    - Risk level (unacceptable, high, limited, minimal)
    - System category
    - Applicable requirements
    - Whether conformity assessment is needed
    """
    generator = get_model_card_generator()
    
    try:
        card_uuid = UUID(card_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid card ID format",
        )
    
    card = await generator.get_model_card(card_uuid)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model card not found",
        )
    
    result = await generator.classify_ai_risk(card, use_case_description)
    
    return RiskClassificationResponse(
        risk_level=result["risk_level"].value,
        category=result["category"].value if result["category"] else None,
        prohibited_practice=result["prohibited_practice"],
        requirements=result["requirements"],
        can_deploy=result["can_deploy"],
        conformity_assessment_required=result.get("conformity_assessment_required", False),
        transparency_requirements=result.get("transparency_requirements"),
        reason=result.get("reason"),
    )


@router.post("/cards/{card_id}/assess-compliance", response_model=ComplianceGapsResponse)
async def assess_compliance_gaps(
    card_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ComplianceGapsResponse:
    """Assess compliance gaps in a model card.
    
    Reviews the model card for completeness and identifies:
    - Missing documentation
    - EU AI Act requirement gaps
    - Recommendations for improvement
    """
    generator = get_model_card_generator()
    
    try:
        card_uuid = UUID(card_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid card ID format",
        )
    
    card = await generator.get_model_card(card_uuid)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model card not found",
        )
    
    result = await generator.assess_compliance_gaps(card)
    
    return ComplianceGapsResponse(
        compliance_score=result["compliance_score"],
        gaps_count=result["gaps_count"],
        gaps=result["gaps"],
        recommendations=result["recommendations"],
        ready_for_deployment=result["ready_for_deployment"],
        risk_level=result["risk_level"],
    )


# ============================================================================
# Export Endpoints
# ============================================================================


@router.get("/cards/{card_id}/export/markdown")
async def export_markdown(
    card_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, str]:
    """Export model card as Markdown documentation."""
    generator = get_model_card_generator()
    
    try:
        card_uuid = UUID(card_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid card ID format",
        )
    
    card = await generator.get_model_card(card_uuid)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model card not found",
        )
    
    markdown = await generator.generate_markdown(card)
    
    return {
        "filename": f"{card.model_name.replace(' ', '_')}_model_card.md",
        "content": markdown,
        "content_type": "text/markdown",
    }


@router.get("/cards/{card_id}/export/json")
async def export_json(
    card_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Export model card as JSON (Hugging Face compatible format)."""
    generator = get_model_card_generator()
    
    try:
        card_uuid = UUID(card_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid card ID format",
        )
    
    card = await generator.get_model_card(card_uuid)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model card not found",
        )
    
    json_data = await generator.export_json(card)
    
    return {
        "filename": f"{card.model_name.replace(' ', '_')}_model_card.json",
        "data": json_data,
    }


# ============================================================================
# Reference Data
# ============================================================================


@router.get("/reference/model-types")
async def get_model_types() -> list[str]:
    """Get available model types."""
    return [t.value for t in ModelType]


@router.get("/reference/risk-levels")
async def get_risk_levels(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Get EU AI Act risk levels and their requirements."""
    from app.services.model_cards.models import (
        AIRiskLevel,
        HIGH_RISK_REQUIREMENTS,
        PROHIBITED_PRACTICES,
        TRANSPARENCY_REQUIREMENTS,
    )
    
    return {
        "risk_levels": [
            {
                "level": AIRiskLevel.UNACCEPTABLE.value,
                "description": "Banned - AI systems that pose an unacceptable risk",
                "requirements": PROHIBITED_PRACTICES,
            },
            {
                "level": AIRiskLevel.HIGH.value,
                "description": "Requires conformity assessment and compliance with strict requirements",
                "requirements": HIGH_RISK_REQUIREMENTS,
            },
            {
                "level": AIRiskLevel.LIMITED.value,
                "description": "Transparency obligations apply",
                "requirements": list(TRANSPARENCY_REQUIREMENTS.values()),
            },
            {
                "level": AIRiskLevel.MINIMAL.value,
                "description": "No specific requirements, voluntary codes of conduct encouraged",
                "requirements": [],
            },
        ],
    }


@router.get("/reference/high-risk-categories")
async def get_high_risk_categories(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[dict[str, str]]:
    """Get EU AI Act Annex III high-risk categories."""
    from app.services.model_cards.models import AISystemCategory, HIGH_RISK_CATEGORIES
    
    descriptions = {
        AISystemCategory.BIOMETRIC_ID: "Remote biometric identification systems",
        AISystemCategory.CRITICAL_INFRASTRUCTURE: "Safety components of critical infrastructure",
        AISystemCategory.EDUCATION_TRAINING: "AI systems used in education and vocational training",
        AISystemCategory.EMPLOYMENT: "AI systems used in employment, workers management and access to self-employment",
        AISystemCategory.ESSENTIAL_SERVICES: "Access to and enjoyment of essential private/public services",
        AISystemCategory.LAW_ENFORCEMENT: "AI systems used in law enforcement",
        AISystemCategory.MIGRATION_ASYLUM: "Migration, asylum and border control management",
        AISystemCategory.JUSTICE: "Administration of justice and democratic processes",
        AISystemCategory.DEMOCRATIC_PROCESS: "AI systems intended to influence electoral processes",
    }
    
    return [
        {"category": cat.value, "description": descriptions.get(cat, "")}
        for cat in HIGH_RISK_CATEGORIES
    ]
