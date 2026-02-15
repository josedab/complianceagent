"""API endpoints for Compliance Cost Attribution Engine."""

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.v1.deps import DB, CopilotDep
from app.services.cost_attribution import CostAttributionService, CostCategory, CostPeriod


logger = structlog.get_logger()
router = APIRouter()


class RecordCostRequest(BaseModel):
    regulation: str
    category: str
    amount: float
    description: str
    code_module: str
    period: str


class CostEntrySchema(BaseModel):
    id: str
    regulation: str
    category: str
    amount: float
    currency: str
    description: str
    code_module: str
    period: str
    recorded_at: str | None


class CostSummarySchema(BaseModel):
    regulation: str
    total_cost: float
    cost_by_category: dict[str, float]
    trend_pct: float
    top_modules: list[dict]
    period: str


class ROISchema(BaseModel):
    id: str
    regulation: str
    investment: float
    savings: float
    roi_pct: float
    payback_months: int
    assumptions: list[str]
    analyzed_at: str | None


class MarketExitSchema(BaseModel):
    id: str
    jurisdiction: str
    current_cost: float
    exit_cost: float
    revenue_at_risk: float
    recommendation: str
    breakeven_months: int


class DashboardSchema(BaseModel):
    total_compliance_cost: float
    cost_by_regulation: dict[str, float]
    cost_by_category: dict[str, float]
    month_over_month_change: float
    top_cost_drivers: list[dict]
    roi_summary: dict
    generated_at: str | None


def _parse_category(cat: str) -> CostCategory:
    try:
        return CostCategory(cat)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category: {cat}. Use: {[c.value for c in CostCategory]}",
        )


def _parse_period(p: str) -> CostPeriod:
    try:
        return CostPeriod(p)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"Invalid period: {p}. Use: {[v.value for v in CostPeriod]}"
        )


@router.post("/costs", response_model=CostEntrySchema, summary="Record compliance cost")
async def record_cost(req: RecordCostRequest, db: DB, copilot: CopilotDep) -> CostEntrySchema:
    category = _parse_category(req.category)
    period = _parse_period(req.period)
    service = CostAttributionService(db=db, copilot_client=copilot)
    entry = await service.record_cost(
        req.regulation,
        category,
        req.amount,
        req.description,
        req.code_module,
        period,
    )
    return CostEntrySchema(
        id=str(entry.id),
        regulation=entry.regulation,
        category=entry.category.value,
        amount=entry.amount,
        currency=entry.currency,
        description=entry.description,
        code_module=entry.code_module,
        period=entry.period.value,
        recorded_at=entry.recorded_at.isoformat() if entry.recorded_at else None,
    )


@router.get("/costs", response_model=list[CostEntrySchema], summary="List compliance costs")
async def list_costs(
    db: DB,
    copilot: CopilotDep,
    regulation: str | None = None,
    category: str | None = None,
) -> list[CostEntrySchema]:
    cat = _parse_category(category) if category else None
    service = CostAttributionService(db=db, copilot_client=copilot)
    costs = await service.list_costs(regulation, cat)
    return [
        CostEntrySchema(
            id=str(c.id),
            regulation=c.regulation,
            category=c.category.value,
            amount=c.amount,
            currency=c.currency,
            description=c.description,
            code_module=c.code_module,
            period=c.period.value,
            recorded_at=c.recorded_at.isoformat() if c.recorded_at else None,
        )
        for c in costs
    ]


@router.get(
    "/summary/{regulation}", response_model=CostSummarySchema, summary="Get regulation cost summary"
)
async def get_regulation_summary(regulation: str, db: DB, copilot: CopilotDep) -> CostSummarySchema:
    service = CostAttributionService(db=db, copilot_client=copilot)
    summary = await service.get_regulation_summary(regulation)
    return CostSummarySchema(
        regulation=summary.regulation,
        total_cost=summary.total_cost,
        cost_by_category=summary.cost_by_category,
        trend_pct=summary.trend_pct,
        top_modules=summary.top_modules,
        period=summary.period,
    )


@router.post("/roi/{regulation}", response_model=ROISchema, summary="Analyze ROI")
async def analyze_roi(regulation: str, db: DB, copilot: CopilotDep) -> ROISchema:
    service = CostAttributionService(db=db, copilot_client=copilot)
    analysis = await service.analyze_roi(regulation)
    return ROISchema(
        id=str(analysis.id),
        regulation=analysis.regulation,
        investment=analysis.investment,
        savings=analysis.savings,
        roi_pct=analysis.roi_pct,
        payback_months=analysis.payback_months,
        assumptions=analysis.assumptions,
        analyzed_at=analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
    )


@router.post(
    "/market-exit/{jurisdiction}", response_model=MarketExitSchema, summary="Model market exit"
)
async def model_market_exit(jurisdiction: str, db: DB, copilot: CopilotDep) -> MarketExitSchema:
    service = CostAttributionService(db=db, copilot_client=copilot)
    scenario = await service.model_market_exit(jurisdiction)
    return MarketExitSchema(
        id=str(scenario.id),
        jurisdiction=scenario.jurisdiction,
        current_cost=scenario.current_cost,
        exit_cost=scenario.exit_cost,
        revenue_at_risk=scenario.revenue_at_risk,
        recommendation=scenario.recommendation,
        breakeven_months=scenario.breakeven_months,
    )


@router.get("/dashboard", response_model=DashboardSchema, summary="Get cost dashboard")
async def get_dashboard(db: DB, copilot: CopilotDep) -> DashboardSchema:
    service = CostAttributionService(db=db, copilot_client=copilot)
    dashboard = await service.get_dashboard()
    return DashboardSchema(
        total_compliance_cost=dashboard.total_compliance_cost,
        cost_by_regulation=dashboard.cost_by_regulation,
        cost_by_category=dashboard.cost_by_category,
        month_over_month_change=dashboard.month_over_month_change,
        top_cost_drivers=dashboard.top_cost_drivers,
        roi_summary=dashboard.roi_summary,
        generated_at=dashboard.generated_at.isoformat() if dashboard.generated_at else None,
    )


@router.get("/summaries", response_model=list[CostSummarySchema], summary="List cost summaries")
async def list_summaries(db: DB, copilot: CopilotDep) -> list[CostSummarySchema]:
    service = CostAttributionService(db=db, copilot_client=copilot)
    summaries = await service.list_summaries()
    return [
        CostSummarySchema(
            regulation=s.regulation,
            total_cost=s.total_cost,
            cost_by_category=s.cost_by_category,
            trend_pct=s.trend_pct,
            top_modules=s.top_modules,
            period=s.period,
        )
        for s in summaries
    ]
