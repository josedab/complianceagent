"""API endpoints for Predictive Compliance Cost Calculator."""

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep, CurrentOrganization, OrgMember
from app.services.cost_calculator import (
    CostCalculatorService,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Request Models ---


class PredictCostRequest(BaseModel):
    regulation: str = Field(..., description="Regulation name (e.g., GDPR, HIPAA, SOC2)")
    team_size: int = Field(default=10, ge=1, le=500, description="Engineering team size")
    avg_hourly_rate: float = Field(
        default=75.0, ge=1.0, description="Average hourly developer rate in USD"
    )
    industry: str = Field(
        default="saas",
        description="Industry (saas, fintech, healthtech, enterprise, startup, government)",
    )


class CompareRequest(BaseModel):
    regulations: list[str] = Field(..., min_length=1, description="List of regulations to compare")
    delay_months: int = Field(default=0, ge=0, le=36, description="Months of delay to model")
    team_size: int = Field(default=10, ge=1, le=500, description="Engineering team size")
    avg_hourly_rate: float = Field(
        default=75.0, ge=1.0, description="Average hourly developer rate in USD"
    )
    industry: str = Field(default="saas", description="Industry vertical")


class RecordActualRequest(BaseModel):
    prediction_id: str = Field(..., description="Original prediction ID")
    actual_days: float = Field(..., ge=0, description="Actual developer-days spent")
    actual_cost: float = Field(..., ge=0, description="Actual cost in USD")


class ExecutiveReportRequest(BaseModel):
    regulations: list[str] = Field(
        ..., min_length=1, description="List of regulations to include in the report"
    )
    team_size: int = Field(default=10, ge=1, le=500, description="Engineering team size")
    avg_hourly_rate: float = Field(
        default=75.0, ge=1.0, description="Average hourly developer rate in USD"
    )
    industry: str = Field(default="saas", description="Industry vertical")


# --- Response Models ---


class CostBreakdownSchema(BaseModel):
    category: str
    description: str
    developer_days: float
    cost_usd: float
    complexity: str


class ComparableImplSchema(BaseModel):
    regulation: str
    industry: str
    company_size: str
    actual_days: float
    actual_cost: float
    year: int


class CostPredictionSchema(BaseModel):
    id: str
    regulation: str
    category: str
    affected_files: int
    affected_modules: int
    estimated_developer_days: float
    estimated_cost_usd: float
    confidence_pct: float
    cost_range_low: float
    cost_range_high: float
    risk_score: float
    breakdown: list[CostBreakdownSchema]
    comparable_implementations: list[ComparableImplSchema]
    predicted_at: str


class ScenarioComparisonSchema(BaseModel):
    id: str
    scenarios: list[CostPredictionSchema]
    recommendation: str
    total_cost_now: float
    total_cost_delayed: float
    delay_risk_premium_pct: float


class CostHistorySchema(BaseModel):
    id: str
    regulation: str
    predicted_cost: float
    actual_cost: float
    accuracy_pct: float
    completed_at: str


class ROISummarySchema(BaseModel):
    annual_manual_cost: float
    annual_automated_cost: float
    annual_savings: float
    roi_pct: float
    payback_months: float
    compared_to: str


class RegulationInfoSchema(BaseModel):
    regulation: str
    category: str
    base_developer_days: float
    cost_multiplier: float


class PriorityRegulationSchema(BaseModel):
    regulation: str
    cost: float
    risk_score: float
    fine_risk: float
    priority_score: float


class ExecutiveReportSchema(BaseModel):
    id: str
    org_id: str
    total_portfolio_cost: float
    total_risk_exposure: float
    annual_fine_risk: float
    roi_with_automation: float
    payback_period_months: float
    priority_regulations: list[PriorityRegulationSchema]
    cost_by_regulation: dict[str, float]
    three_year_projection: dict[str, float]
    recommendations: list[str]
    generated_at: str


# --- Helpers ---


def _prediction_to_schema(p) -> CostPredictionSchema:
    """Convert a CostPrediction dataclass to the response schema."""
    return CostPredictionSchema(
        id=str(p.id),
        regulation=p.regulation,
        category=p.category.value,
        affected_files=p.affected_files,
        affected_modules=p.affected_modules,
        estimated_developer_days=p.estimated_developer_days,
        estimated_cost_usd=p.estimated_cost_usd,
        confidence_pct=p.confidence_pct,
        cost_range_low=p.cost_range_low,
        cost_range_high=p.cost_range_high,
        risk_score=p.risk_score,
        breakdown=[
            CostBreakdownSchema(
                category=b.category,
                description=b.description,
                developer_days=b.developer_days,
                cost_usd=b.cost_usd,
                complexity=b.complexity.value,
            )
            for b in p.breakdown
        ],
        comparable_implementations=[
            ComparableImplSchema(
                regulation=c.regulation,
                industry=c.industry,
                company_size=c.company_size,
                actual_days=c.actual_days,
                actual_cost=c.actual_cost,
                year=c.year,
            )
            for c in p.comparable_implementations
        ],
        predicted_at=p.predicted_at.isoformat(),
    )


# --- Endpoints ---


@router.post(
    "/predict",
    response_model=CostPredictionSchema,
    summary="Predict compliance cost",
    description="Predict time, cost, and risk for implementing a compliance regulation",
)
async def predict_cost(
    request: PredictCostRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> CostPredictionSchema:
    service = CostCalculatorService(db=db, copilot_client=copilot)
    prediction = await service.predict_cost(
        regulation=request.regulation,
        org_id=str(organization.id),
        team_size=request.team_size,
        avg_hourly_rate=request.avg_hourly_rate,
        industry=request.industry,
    )
    return _prediction_to_schema(prediction)


@router.post(
    "/compare",
    response_model=ScenarioComparisonSchema,
    summary="Compare cost scenarios",
    description="Compare compliance costs for multiple regulations with optional delay modelling",
)
async def compare_scenarios(
    request: CompareRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> ScenarioComparisonSchema:
    service = CostCalculatorService(db=db, copilot_client=copilot)
    comparison = await service.compare_scenarios(
        regulations=request.regulations,
        org_id=str(organization.id),
        delay_months=request.delay_months,
        team_size=request.team_size,
        avg_hourly_rate=request.avg_hourly_rate,
        industry=request.industry,
    )
    return ScenarioComparisonSchema(
        id=str(comparison.id),
        scenarios=[_prediction_to_schema(s) for s in comparison.scenarios],
        recommendation=comparison.recommendation,
        total_cost_now=comparison.total_cost_now,
        total_cost_delayed=comparison.total_cost_delayed,
        delay_risk_premium_pct=comparison.delay_risk_premium_pct,
    )


@router.get(
    "/roi",
    response_model=ROISummarySchema,
    summary="Calculate compliance ROI",
    description="Calculate ROI of automated compliance vs manual processes",
)
async def calculate_roi(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    industry: str = "saas",
) -> ROISummarySchema:
    service = CostCalculatorService(db=db)
    summary = await service.calculate_roi(
        org_id=str(organization.id),
        industry=industry,
    )
    return ROISummarySchema(
        annual_manual_cost=summary.annual_manual_cost,
        annual_automated_cost=summary.annual_automated_cost,
        annual_savings=summary.annual_savings,
        roi_pct=summary.roi_pct,
        payback_months=summary.payback_months,
        compared_to=summary.compared_to,
    )


@router.get(
    "/history",
    response_model=list[CostHistorySchema],
    summary="Get prediction history",
    description="Get historical prediction accuracy for the organization",
)
async def get_prediction_history(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    limit: int = 20,
) -> list[CostHistorySchema]:
    service = CostCalculatorService(db=db)
    history = await service.get_prediction_history(
        org_id=str(organization.id),
        limit=limit,
    )
    return [
        CostHistorySchema(
            id=str(h.id),
            regulation=h.regulation,
            predicted_cost=h.predicted_cost,
            actual_cost=h.actual_cost,
            accuracy_pct=h.accuracy_pct,
            completed_at=h.completed_at.isoformat(),
        )
        for h in history
    ]


@router.post(
    "/record-actual",
    response_model=CostHistorySchema,
    summary="Record actual cost",
    description="Record actual implementation cost for prediction accuracy tracking",
)
async def record_actual_cost(
    request: RecordActualRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> CostHistorySchema:
    service = CostCalculatorService(db=db)
    record = await service.record_actual_cost(
        prediction_id=request.prediction_id,
        actual_days=request.actual_days,
        actual_cost=request.actual_cost,
    )
    return CostHistorySchema(
        id=str(record.id),
        regulation=record.regulation,
        predicted_cost=record.predicted_cost,
        actual_cost=record.actual_cost,
        accuracy_pct=record.accuracy_pct,
        completed_at=record.completed_at.isoformat(),
    )


@router.get(
    "/regulations",
    response_model=list[RegulationInfoSchema],
    summary="List supported regulations",
    description="List all supported regulations with their base cost estimates",
)
async def list_regulations() -> list[RegulationInfoSchema]:
    from app.services.cost_calculator.service import _BASE_ESTIMATES

    return [
        RegulationInfoSchema(
            regulation=key.upper().replace("_", " "),
            category=cat.value,
            base_developer_days=days,
            cost_multiplier=mult,
        )
        for key, (days, mult, cat) in sorted(_BASE_ESTIMATES.items())
    ]


@router.post(
    "/executive-report",
    response_model=ExecutiveReportSchema,
    summary="Generate executive report",
    description="Generate a CFO-ready executive compliance cost report with risk exposure, ROI, and recommendations",
)
async def generate_executive_report(
    request: ExecutiveReportRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> ExecutiveReportSchema:
    service = CostCalculatorService(db=db, copilot_client=copilot)
    report = await service.generate_executive_report(
        org_id=str(organization.id),
        regulations=request.regulations,
        team_size=request.team_size,
        avg_hourly_rate=request.avg_hourly_rate,
        industry=request.industry,
    )
    return ExecutiveReportSchema(
        id=str(report.id),
        org_id=report.org_id,
        total_portfolio_cost=report.total_portfolio_cost,
        total_risk_exposure=report.total_risk_exposure,
        annual_fine_risk=report.annual_fine_risk,
        roi_with_automation=report.roi_with_automation,
        payback_period_months=report.payback_period_months,
        priority_regulations=[
            PriorityRegulationSchema(
                regulation=p["regulation"],
                cost=p["cost"],
                risk_score=p["risk_score"],
                fine_risk=p["fine_risk"],
                priority_score=p["priority_score"],
            )
            for p in report.priority_regulations
        ],
        cost_by_regulation=report.cost_by_regulation,
        three_year_projection=report.three_year_projection,
        recommendations=report.recommendations,
        generated_at=report.generated_at.isoformat(),
    )
