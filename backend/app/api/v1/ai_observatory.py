"""API endpoints for AI Model Compliance Observatory."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.ai_observatory import (
    AIObservatoryService,
    AIRiskLevel,
    ModelStatus,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class RegisterModelRequest(BaseModel):
    """Request to register an AI model."""

    name: str = Field(..., description="Model name")
    model_type: str = Field(..., description="Model type (e.g. classifier, LLM)")
    version: str = Field(default="1.0.0")
    framework: str = Field(default="pytorch")
    use_case: str = Field(..., description="Intended use case")


class BiasAssessmentRequest(BaseModel):
    """Request to run bias assessment."""

    protected_attributes: list[str] = Field(..., description="Attributes to assess")


class UpdateStatusRequest(BaseModel):
    """Request to update model status."""

    status: str = Field(..., description="New status")


class AIModelSchema(BaseModel):
    """AI model response."""

    id: str
    name: str
    model_type: str
    version: str
    framework: str
    use_case: str
    risk_level: str
    status: str
    owner: str
    deployed_at: str | None
    last_assessed_at: str | None


class BiasMetricSchema(BaseModel):
    """Bias metric response."""

    id: str
    model_id: str
    metric_type: str
    value: float
    threshold: float
    is_passing: bool
    protected_attribute: str
    measured_at: str | None


class ExplainabilityReportSchema(BaseModel):
    """Explainability report response."""

    id: str
    model_id: str
    method: str
    feature_importance: dict[str, float]
    explanation_coverage: float
    gdpr_art22_compliant: bool
    eu_ai_act_art13_compliant: bool
    generated_at: str | None


class ModelComplianceReportSchema(BaseModel):
    """Model compliance report response."""

    id: str
    model_id: str
    risk_level: str
    bias_metrics: list[BiasMetricSchema]
    explainability: ExplainabilityReportSchema | None
    documentation_complete: bool
    human_oversight_implemented: bool
    technical_documentation: str
    overall_compliant: bool
    issues: list[str]
    recommendations: list[str]
    assessed_at: str | None


class ObservatoryDashboardSchema(BaseModel):
    """Observatory dashboard response."""

    total_models: int
    by_risk_level: dict[str, Any]
    compliant_count: int
    non_compliant_count: int
    avg_bias_score: float
    models_needing_review: int
    recent_alerts: list[dict[str, Any]]


# --- Helpers ---


def _model_to_schema(m) -> AIModelSchema:
    return AIModelSchema(
        id=str(m.id),
        name=m.name,
        model_type=m.model_type,
        version=m.version,
        framework=m.framework,
        use_case=m.use_case,
        risk_level=m.risk_level.value,
        status=m.status.value,
        owner=m.owner,
        deployed_at=m.deployed_at.isoformat() if m.deployed_at else None,
        last_assessed_at=m.last_assessed_at.isoformat() if m.last_assessed_at else None,
    )


def _bias_to_schema(b) -> BiasMetricSchema:
    return BiasMetricSchema(
        id=str(b.id),
        model_id=str(b.model_id),
        metric_type=b.metric_type.value,
        value=b.value,
        threshold=b.threshold,
        is_passing=b.is_passing,
        protected_attribute=b.protected_attribute,
        measured_at=b.measured_at.isoformat() if b.measured_at else None,
    )


def _explainability_to_schema(e) -> ExplainabilityReportSchema:
    return ExplainabilityReportSchema(
        id=str(e.id),
        model_id=str(e.model_id),
        method=e.method,
        feature_importance=e.feature_importance,
        explanation_coverage=e.explanation_coverage,
        gdpr_art22_compliant=e.gdpr_art22_compliant,
        eu_ai_act_art13_compliant=e.eu_ai_act_art13_compliant,
        generated_at=e.generated_at.isoformat() if e.generated_at else None,
    )


# --- Endpoints ---


@router.post(
    "/models",
    response_model=AIModelSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register AI model",
)
async def register_model(
    request: RegisterModelRequest,
    db: DB,
    copilot: CopilotDep,
) -> AIModelSchema:
    """Register a new AI model for compliance tracking."""
    service = AIObservatoryService(db=db, copilot_client=copilot)
    model = await service.register_model(
        name=request.name,
        model_type=request.model_type,
        version=request.version,
        framework=request.framework,
        use_case=request.use_case,
    )
    return _model_to_schema(model)


@router.get(
    "/models",
    response_model=list[AIModelSchema],
    summary="List AI models",
)
async def list_models(
    db: DB,
    copilot: CopilotDep,
    risk_level: str | None = None,
    model_status: str | None = None,
) -> list[AIModelSchema]:
    """List AI models with optional filters."""
    service = AIObservatoryService(db=db, copilot_client=copilot)
    rl = AIRiskLevel(risk_level) if risk_level else None
    ms = ModelStatus(model_status) if model_status else None
    models = await service.list_models(risk_level=rl, status=ms)
    return [_model_to_schema(m) for m in models]


@router.post(
    "/models/{model_id}/classify",
    response_model=AIModelSchema,
    summary="Classify AI model risk",
)
async def classify_risk(
    model_id: UUID,
    db: DB,
    copilot: CopilotDep,
) -> AIModelSchema:
    """Apply EU AI Act risk classification."""
    service = AIObservatoryService(db=db, copilot_client=copilot)
    model = await service.classify_risk(model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return _model_to_schema(model)


@router.post(
    "/models/{model_id}/bias-assessment",
    response_model=list[BiasMetricSchema],
    summary="Run bias assessment",
)
async def run_bias_assessment(
    model_id: UUID,
    request: BiasAssessmentRequest,
    db: DB,
    copilot: CopilotDep,
) -> list[BiasMetricSchema]:
    """Run bias assessment for protected attributes."""
    service = AIObservatoryService(db=db, copilot_client=copilot)
    metrics = await service.run_bias_assessment(model_id, request.protected_attributes)
    if not metrics:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return [_bias_to_schema(m) for m in metrics]


@router.post(
    "/models/{model_id}/explainability",
    response_model=ExplainabilityReportSchema,
    summary="Generate explainability report",
)
async def generate_explainability_report(
    model_id: UUID,
    db: DB,
    copilot: CopilotDep,
) -> ExplainabilityReportSchema:
    """Generate an explainability report for a model."""
    service = AIObservatoryService(db=db, copilot_client=copilot)
    report = await service.generate_explainability_report(model_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return _explainability_to_schema(report)


@router.post(
    "/models/{model_id}/assess",
    response_model=ModelComplianceReportSchema,
    summary="Assess model compliance",
)
async def assess_compliance(
    model_id: UUID,
    db: DB,
    copilot: CopilotDep,
) -> ModelComplianceReportSchema:
    """Full compliance assessment for a model."""
    service = AIObservatoryService(db=db, copilot_client=copilot)
    report = await service.assess_compliance(model_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return ModelComplianceReportSchema(
        id=str(report.id),
        model_id=str(report.model_id),
        risk_level=report.risk_level.value,
        bias_metrics=[_bias_to_schema(b) for b in report.bias_metrics],
        explainability=_explainability_to_schema(report.explainability)
        if report.explainability
        else None,
        documentation_complete=report.documentation_complete,
        human_oversight_implemented=report.human_oversight_implemented,
        technical_documentation=report.technical_documentation,
        overall_compliant=report.overall_compliant,
        issues=report.issues,
        recommendations=report.recommendations,
        assessed_at=report.assessed_at.isoformat() if report.assessed_at else None,
    )


@router.get(
    "/dashboard",
    response_model=ObservatoryDashboardSchema,
    summary="Get observatory dashboard",
)
async def get_dashboard(
    db: DB,
    copilot: CopilotDep,
) -> ObservatoryDashboardSchema:
    """Get AI observatory dashboard summary."""
    service = AIObservatoryService(db=db, copilot_client=copilot)
    dashboard = await service.get_dashboard()
    return ObservatoryDashboardSchema(
        total_models=dashboard.total_models,
        by_risk_level=dashboard.by_risk_level,
        compliant_count=dashboard.compliant_count,
        non_compliant_count=dashboard.non_compliant_count,
        avg_bias_score=dashboard.avg_bias_score,
        models_needing_review=dashboard.models_needing_review,
        recent_alerts=dashboard.recent_alerts,
    )


@router.patch(
    "/models/{model_id}/status",
    response_model=AIModelSchema,
    summary="Update model status",
)
async def update_model_status(
    model_id: UUID,
    request: UpdateStatusRequest,
    db: DB,
    copilot: CopilotDep,
) -> AIModelSchema:
    """Update an AI model's compliance status."""
    service = AIObservatoryService(db=db, copilot_client=copilot)
    model = await service.update_model_status(model_id, ModelStatus(request.status))
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return _model_to_schema(model)
