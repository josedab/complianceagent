"""API endpoints for Regulatory Change Impact Heat Maps."""

from datetime import datetime

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep, CurrentOrganization, OrgMember
from app.services.impact_heatmap import (
    ExportFormat,
    HeatmapFilter,
    ImpactHeatmapService,
    RiskLevel,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Request Models ---


class ExportRequest(BaseModel):
    format: str = Field(default="pdf", description="Export format: png, pdf, svg, json")
    title: str | None = Field(default=None, description="Custom title for the export")


# --- Response Models ---


class HeatmapCellSchema(BaseModel):
    path: str
    module: str
    risk_level: str
    compliance_score: float
    violation_count: int
    regulations_affected: list[str]
    last_changed: str
    color_hex: str


class HeatmapSnapshotSchema(BaseModel):
    id: str
    org_id: str
    timestamp: str
    cells: list[HeatmapCellSchema]
    overall_score: float
    total_violations: int
    framework_overlay: str | None = None


class HeatmapChangeSchema(BaseModel):
    path: str
    old_risk: str
    new_risk: str
    old_score: float
    new_score: float
    change_reason: str


class TimeTravelSchema(BaseModel):
    current: HeatmapSnapshotSchema
    historical: HeatmapSnapshotSchema
    changes: list[HeatmapChangeSchema]
    improvements: int
    regressions: int


class HeatmapTimeSeriesSchema(BaseModel):
    snapshots: list[HeatmapSnapshotSchema]
    period_start: str
    period_end: str
    granularity: str
    trend: str
    score_change: float


class RiskForecastSchema(BaseModel):
    id: str
    org_id: str
    forecast_date: str
    predicted_violations: int
    predicted_score: float
    confidence_pct: float
    risk_factors: list[str]
    recommended_actions: list[str]


class HeatmapExportSchema(BaseModel):
    id: str
    format: str
    content_url: str
    generated_at: str
    title: str
    description: str


class ModuleRiskTrendSchema(BaseModel):
    module: str
    scores: list[float]
    timestamps: list[str]
    trend: str
    prediction_30d: float


# --- Helpers ---


def _snapshot_to_schema(s) -> HeatmapSnapshotSchema:
    """Convert a HeatmapSnapshot dataclass to the response schema."""
    return HeatmapSnapshotSchema(
        id=str(s.id),
        org_id=s.org_id,
        timestamp=s.timestamp.isoformat(),
        cells=[
            HeatmapCellSchema(
                path=c.path,
                module=c.module,
                risk_level=c.risk_level.value,
                compliance_score=c.compliance_score,
                violation_count=c.violation_count,
                regulations_affected=c.regulations_affected,
                last_changed=c.last_changed.isoformat(),
                color_hex=c.color_hex,
            )
            for c in s.cells
        ],
        overall_score=s.overall_score,
        total_violations=s.total_violations,
        framework_overlay=s.framework_overlay,
    )


# --- Endpoints ---


@router.get(
    "/current",
    response_model=HeatmapSnapshotSchema,
    summary="Get current heatmap",
    description="Get the current compliance risk heatmap for the organization",
)
async def get_current_heatmap(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
    regulations: str | None = Query(default=None, description="Comma-separated regulation filter"),
    modules: str | None = Query(default=None, description="Comma-separated module filter"),
    min_risk: str | None = Query(default=None, description="Minimum risk level filter"),
    framework: str | None = Query(default=None, description="Framework filter"),
) -> HeatmapSnapshotSchema:
    filters = None
    if any([regulations, modules, min_risk, framework]):
        filters = HeatmapFilter(
            regulations=regulations.split(",") if regulations else None,
            modules=modules.split(",") if modules else None,
            min_risk=RiskLevel(min_risk) if min_risk else None,
            framework=framework,
        )

    service = ImpactHeatmapService(db=db, copilot_client=copilot)
    snapshot = await service.get_current_heatmap(
        org_id=str(organization.id),
        filters=filters,
    )
    return _snapshot_to_schema(snapshot)


@router.get(
    "/at/{timestamp}",
    response_model=HeatmapSnapshotSchema,
    summary="Get heatmap at specific time",
    description="Get the compliance heatmap at a specific historical point in time",
)
async def get_heatmap_at(
    timestamp: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> HeatmapSnapshotSchema:
    try:
        ts = datetime.fromisoformat(timestamp)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO 8601.")

    service = ImpactHeatmapService(db=db, copilot_client=copilot)
    snapshot = await service.get_heatmap_at(
        org_id=str(organization.id),
        timestamp=ts,
    )
    return _snapshot_to_schema(snapshot)


@router.get(
    "/time-series",
    response_model=HeatmapTimeSeriesSchema,
    summary="Get time series data",
    description="Get time-series heatmap data for the time-travel slider visualization",
)
async def get_time_series(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
    period_days: int = Query(default=90, ge=1, le=365, description="Number of days to include"),
    granularity: str = Query(default="daily", description="Granularity: daily, weekly, monthly"),
) -> HeatmapTimeSeriesSchema:
    service = ImpactHeatmapService(db=db, copilot_client=copilot)
    ts = await service.get_time_series(
        org_id=str(organization.id),
        period_days=period_days,
        granularity=granularity,
    )
    return HeatmapTimeSeriesSchema(
        snapshots=[_snapshot_to_schema(s) for s in ts.snapshots],
        period_start=ts.period_start.isoformat(),
        period_end=ts.period_end.isoformat(),
        granularity=ts.granularity,
        trend=ts.trend.value,
        score_change=ts.score_change,
    )


@router.get(
    "/compare",
    response_model=TimeTravelSchema,
    summary="Compare two timepoints (time-travel)",
    description="Compare heatmaps at two points in time to see compliance drift",
)
async def compare_timepoints(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
    from_date: str = Query(..., description="Start date (ISO 8601)"),
    to_date: str = Query(..., description="End date (ISO 8601)"),
) -> TimeTravelSchema:
    try:
        fd = datetime.fromisoformat(from_date)
        td = datetime.fromisoformat(to_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO 8601.")

    service = ImpactHeatmapService(db=db, copilot_client=copilot)
    result = await service.compare_timepoints(
        org_id=str(organization.id),
        from_date=fd,
        to_date=td,
    )
    return TimeTravelSchema(
        current=_snapshot_to_schema(result.current),
        historical=_snapshot_to_schema(result.historical),
        changes=[
            HeatmapChangeSchema(
                path=ch.path,
                old_risk=ch.old_risk.value,
                new_risk=ch.new_risk.value,
                old_score=ch.old_score,
                new_score=ch.new_score,
                change_reason=ch.change_reason,
            )
            for ch in result.changes
        ],
        improvements=result.improvements,
        regressions=result.regressions,
    )


@router.get(
    "/forecast",
    response_model=RiskForecastSchema,
    summary="Get risk forecast",
    description="Forecast future compliance risk using trend analysis and predictive modelling",
)
async def get_forecast(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
    forecast_days: int = Query(default=90, ge=1, le=365, description="Days to forecast"),
) -> RiskForecastSchema:
    service = ImpactHeatmapService(db=db, copilot_client=copilot)
    forecast = await service.forecast_risk(
        org_id=str(organization.id),
        forecast_days=forecast_days,
    )
    return RiskForecastSchema(
        id=str(forecast.id),
        org_id=forecast.org_id,
        forecast_date=forecast.forecast_date.isoformat(),
        predicted_violations=forecast.predicted_violations,
        predicted_score=forecast.predicted_score,
        confidence_pct=forecast.confidence_pct,
        risk_factors=forecast.risk_factors,
        recommended_actions=forecast.recommended_actions,
    )


@router.get(
    "/trends",
    response_model=list[ModuleRiskTrendSchema],
    summary="Get module risk trends",
    description="Get per-module risk trends over time for trend analysis",
)
async def get_trends(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
    limit: int = Query(default=20, ge=1, le=50, description="Max modules to return"),
) -> list[ModuleRiskTrendSchema]:
    service = ImpactHeatmapService(db=db, copilot_client=copilot)
    trends = await service.get_module_trends(
        org_id=str(organization.id),
        limit=limit,
    )
    return [
        ModuleRiskTrendSchema(
            module=t.module,
            scores=t.scores,
            timestamps=[ts.isoformat() for ts in t.timestamps],
            trend=t.trend.value,
            prediction_30d=t.prediction_30d,
        )
        for t in trends
    ]


@router.post(
    "/export",
    response_model=HeatmapExportSchema,
    summary="Export heatmap",
    description="Export the current heatmap as PNG, PDF, SVG, or JSON",
)
async def export_heatmap(
    request: ExportRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> HeatmapExportSchema:
    try:
        ExportFormat(request.format.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{request.format}'. Use: png, pdf, svg, json",
        )

    service = ImpactHeatmapService(db=db, copilot_client=copilot)
    export = await service.export_heatmap(
        org_id=str(organization.id),
        format=request.format,
        title=request.title,
    )
    return HeatmapExportSchema(
        id=str(export.id),
        format=export.format.value,
        content_url=export.content_url,
        generated_at=export.generated_at.isoformat(),
        title=export.title,
        description=export.description,
    )


@router.get(
    "/overlay/{framework}",
    response_model=HeatmapSnapshotSchema,
    summary="Get framework-specific overlay",
    description="Get a heatmap filtered to a specific compliance framework",
)
async def get_framework_overlay(
    framework: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> HeatmapSnapshotSchema:
    service = ImpactHeatmapService(db=db, copilot_client=copilot)
    snapshot = await service.get_framework_overlay(
        org_id=str(organization.id),
        framework=framework,
    )
    return _snapshot_to_schema(snapshot)


@router.get(
    "/hotspots",
    response_model=list[HeatmapCellSchema],
    summary="Get top risk hotspots",
    description="Get the top risk hotspots across the codebase sorted by severity",
)
async def get_hotspots(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
    limit: int = Query(default=10, ge=1, le=50, description="Max hotspots to return"),
) -> list[HeatmapCellSchema]:
    service = ImpactHeatmapService(db=db, copilot_client=copilot)
    hotspots = await service.get_hotspots(
        org_id=str(organization.id),
        limit=limit,
    )
    return [
        HeatmapCellSchema(
            path=c.path,
            module=c.module,
            risk_level=c.risk_level.value,
            compliance_score=c.compliance_score,
            violation_count=c.violation_count,
            regulations_affected=c.regulations_affected,
            last_changed=c.last_changed.isoformat(),
            color_hex=c.color_hex,
        )
        for c in hotspots
    ]


@router.get(
    "/share/{export_id}",
    response_model=HeatmapExportSchema,
    summary="Get shareable link",
    description="Get a shareable link for a previously exported heatmap",
)
async def get_shareable_link(
    export_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> HeatmapExportSchema:
    return HeatmapExportSchema(
        id=export_id,
        format="pdf",
        content_url=f"/api/v1/impact-heatmap/exports/{export_id}.pdf",
        generated_at=datetime.utcnow().isoformat(),
        title="Shared Compliance Heatmap",
        description=f"Shareable heatmap export for organization {organization.id}",
    )
