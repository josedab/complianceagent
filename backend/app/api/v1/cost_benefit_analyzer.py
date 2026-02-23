"""API endpoints for Compliance Cost-Benefit Analyzer."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.cost_benefit_analyzer import CostBenefitAnalyzerService


logger = structlog.get_logger()
router = APIRouter()


class AddInvestmentRequest(BaseModel):
    name: str = Field(...)
    framework: str = Field(...)
    category: str = Field(default="engineering")
    cost_usd: float = Field(default=0)
    engineering_hours: float = Field(default=0)
    score_impact: float = Field(default=0)


class InvestmentSchema(BaseModel):
    id: str
    name: str
    framework: str
    category: str
    cost_usd: float
    engineering_hours: float
    status: str
    score_impact: float
    risk_reduction_usd: float


class ROISchema(BaseModel):
    investment_name: str
    total_cost: float
    risk_reduction: float
    roi_pct: float
    payback_months: float
    net_benefit: float
    score_improvement: float


class CostBreakdownSchema(BaseModel):
    framework: str
    total_cost: float
    by_category: dict[str, float]
    engineering_hours: float
    cost_per_point: float


class ExecutiveReportSchema(BaseModel):
    id: str
    period: str
    total_investment: float
    total_risk_reduction: float
    overall_roi_pct: float
    framework_breakdown: list[CostBreakdownSchema]
    highlights: list[str]
    recommendations: list[str]
    generated_at: str | None


class StatsSchema(BaseModel):
    total_investments: int
    total_spend: float
    total_risk_reduction: float
    avg_roi_pct: float
    by_framework: dict[str, float]
    by_category: dict[str, float]


@router.post(
    "/investments",
    response_model=InvestmentSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Add investment",
)
async def add_investment(request: AddInvestmentRequest, db: DB) -> InvestmentSchema:
    service = CostBenefitAnalyzerService(db=db)
    i = await service.add_investment(
        name=request.name,
        framework=request.framework,
        category=request.category,
        cost_usd=request.cost_usd,
        engineering_hours=request.engineering_hours,
        score_impact=request.score_impact,
    )
    return InvestmentSchema(
        id=str(i.id),
        name=i.name,
        framework=i.framework,
        category=i.category.value,
        cost_usd=i.cost_usd,
        engineering_hours=i.engineering_hours,
        status=i.status.value,
        score_impact=i.score_impact,
        risk_reduction_usd=i.risk_reduction_usd,
    )


@router.get("/investments", response_model=list[InvestmentSchema], summary="List investments")
async def list_investments(db: DB, framework: str | None = None) -> list[InvestmentSchema]:
    service = CostBenefitAnalyzerService(db=db)
    invs = service.list_investments(framework=framework)
    return [
        InvestmentSchema(
            id=str(i.id),
            name=i.name,
            framework=i.framework,
            category=i.category.value,
            cost_usd=i.cost_usd,
            engineering_hours=i.engineering_hours,
            status=i.status.value,
            score_impact=i.score_impact,
            risk_reduction_usd=i.risk_reduction_usd,
        )
        for i in invs
    ]


@router.get("/investments/{investment_id}/roi", response_model=ROISchema, summary="Calculate ROI")
async def calculate_roi(investment_id: UUID, db: DB) -> ROISchema:
    service = CostBenefitAnalyzerService(db=db)
    r = await service.calculate_roi(investment_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investment not found")
    return ROISchema(
        investment_name=r.investment_name,
        total_cost=r.total_cost,
        risk_reduction=r.risk_reduction,
        roi_pct=r.roi_pct,
        payback_months=r.payback_months,
        net_benefit=r.net_benefit,
        score_improvement=r.score_improvement,
    )


@router.get("/breakdown", response_model=list[CostBreakdownSchema], summary="Get cost breakdown")
async def get_breakdown(db: DB, framework: str | None = None) -> list[CostBreakdownSchema]:
    service = CostBenefitAnalyzerService(db=db)
    bds = service.get_cost_breakdown(framework=framework)
    return [
        CostBreakdownSchema(
            framework=b.framework,
            total_cost=b.total_cost,
            by_category=b.by_category,
            engineering_hours=b.engineering_hours,
            cost_per_point=b.cost_per_point,
        )
        for b in bds
    ]


@router.post(
    "/executive-report", response_model=ExecutiveReportSchema, summary="Generate executive report"
)
async def generate_report(db: DB, period: str = "Q1 2026") -> ExecutiveReportSchema:
    service = CostBenefitAnalyzerService(db=db)
    r = await service.generate_executive_report(period=period)
    return ExecutiveReportSchema(
        id=str(r.id),
        period=r.period,
        total_investment=r.total_investment,
        total_risk_reduction=r.total_risk_reduction,
        overall_roi_pct=r.overall_roi_pct,
        framework_breakdown=[
            CostBreakdownSchema(
                framework=b.framework,
                total_cost=b.total_cost,
                by_category=b.by_category,
                engineering_hours=b.engineering_hours,
                cost_per_point=b.cost_per_point,
            )
            for b in r.framework_breakdown
        ],
        highlights=r.highlights,
        recommendations=r.recommendations,
        generated_at=r.generated_at.isoformat() if r.generated_at else None,
    )


@router.get("/stats", response_model=StatsSchema, summary="Get cost-benefit stats")
async def get_stats(db: DB) -> StatsSchema:
    service = CostBenefitAnalyzerService(db=db)
    s = service.get_stats()
    return StatsSchema(
        total_investments=s.total_investments,
        total_spend=s.total_spend,
        total_risk_reduction=s.total_risk_reduction,
        avg_roi_pct=s.avg_roi_pct,
        by_framework=s.by_framework,
        by_category=s.by_category,
    )
