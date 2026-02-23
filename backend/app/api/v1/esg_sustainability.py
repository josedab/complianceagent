"""API endpoints for ESG Sustainability."""

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.esg_sustainability import ESGSustainabilityService


logger = structlog.get_logger()
router = APIRouter()


class RecordMetricRequest(BaseModel):
    category: str = Field(...)
    framework: str = Field(...)
    metric_name: str = Field(...)
    value: float = Field(...)
    unit: str = Field(...)
    period: str = Field(...)


class GenerateReportRequest(BaseModel):
    title: str = Field(...)
    frameworks: list[str] = Field(default_factory=list)


class MetricSchema(BaseModel):
    id: str
    category: str
    framework: str
    metric_name: str
    value: float
    unit: str
    period: str
    recorded_at: str | None


class CarbonFootprintSchema(BaseModel):
    period: str
    total_emissions_kg: float
    scope1: float
    scope2: float
    scope3: float
    offset_kg: float
    net_emissions_kg: float


class ReportSchema(BaseModel):
    id: str
    title: str
    frameworks: list[str]
    metrics_count: int
    esg_score: float
    sections: list[dict]
    generated_at: str | None


class StatsSchema(BaseModel):
    total_metrics: int
    total_reports: int
    frameworks_covered: int
    avg_esg_score: float
    total_emissions_kg: float


@router.post(
    "/metrics",
    response_model=MetricSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Record metric",
)
async def record_metric(request: RecordMetricRequest, db: DB) -> MetricSchema:
    """Record an ESG sustainability metric."""
    service = ESGSustainabilityService(db=db)
    metric = await service.record_metric(
        category=request.category,
        framework=request.framework,
        metric_name=request.metric_name,
        value=request.value,
        unit=request.unit,
        period=request.period,
    )
    return MetricSchema(
        id=str(metric.id),
        category=metric.category,
        framework=metric.framework,
        metric_name=metric.metric_name,
        value=metric.value,
        unit=metric.unit,
        period=metric.period,
        recorded_at=metric.recorded_at.isoformat() if metric.recorded_at else None,
    )


@router.get(
    "/carbon/{period}",
    response_model=CarbonFootprintSchema,
    summary="Get carbon footprint",
)
async def get_carbon_footprint(period: str, db: DB) -> CarbonFootprintSchema:
    """Get carbon footprint for a specific period."""
    service = ESGSustainabilityService(db=db)
    footprint = service.get_carbon_footprint(period=period)
    if not footprint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data for the specified period",
        )
    return CarbonFootprintSchema(
        period=footprint.period,
        total_emissions_kg=footprint.total_emissions_kg,
        scope1=footprint.scope1,
        scope2=footprint.scope2,
        scope3=footprint.scope3,
        offset_kg=footprint.offset_kg,
        net_emissions_kg=footprint.net_emissions_kg,
    )


@router.post(
    "/reports",
    response_model=ReportSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Generate report",
)
async def generate_report(request: GenerateReportRequest, db: DB) -> ReportSchema:
    """Generate an ESG sustainability report."""
    service = ESGSustainabilityService(db=db)
    report = await service.generate_report(
        title=request.title, frameworks=request.frameworks
    )
    return ReportSchema(
        id=str(report.id),
        title=report.title,
        frameworks=report.frameworks,
        metrics_count=report.metrics_count,
        esg_score=report.esg_score,
        sections=report.sections,
        generated_at=report.generated_at.isoformat()
        if report.generated_at
        else None,
    )


@router.get("/metrics", response_model=list[MetricSchema], summary="List metrics")
async def list_metrics(db: DB) -> list[MetricSchema]:
    """List all ESG metrics."""
    service = ESGSustainabilityService(db=db)
    metrics = service.list_metrics()
    return [
        MetricSchema(
            id=str(m.id),
            category=m.category,
            framework=m.framework,
            metric_name=m.metric_name,
            value=m.value,
            unit=m.unit,
            period=m.period,
            recorded_at=m.recorded_at.isoformat() if m.recorded_at else None,
        )
        for m in metrics
    ]


@router.get("/stats", response_model=StatsSchema, summary="Get stats")
async def get_stats(db: DB) -> StatsSchema:
    """Get ESG sustainability statistics."""
    service = ESGSustainabilityService(db=db)
    stats = service.get_stats()
    return StatsSchema(
        total_metrics=stats.total_metrics,
        total_reports=stats.total_reports,
        frameworks_covered=stats.frameworks_covered,
        avg_esg_score=stats.avg_esg_score,
        total_emissions_kg=stats.total_emissions_kg,
    )
