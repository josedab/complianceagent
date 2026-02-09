"""API endpoints for Compliance Health Score Benchmarking Dashboard."""


import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep, CurrentOrganization, OrgMember


logger = structlog.get_logger()
router = APIRouter()


# --- Pydantic response schemas ---

class HealthScoreSchema(BaseModel):
    id: str = Field(..., description="Health score ID")
    org_id: str = Field(..., description="Organization ID")
    overall_score: float = Field(..., description="Overall compliance health score (0-100)")
    grade: str = Field(..., description="Letter grade (A+ to F)")
    dimensions: dict[str, float] = Field(..., description="Per-dimension scores")
    framework_scores: dict[str, float] = Field(..., description="Per-framework scores")
    percentile: float = Field(..., description="Percentile rank among peers")
    peer_group: str = Field(..., description="Peer group identifier")
    computed_at: str | None = Field(None, description="ISO timestamp of computation")


class PeerBenchmarkSchema(BaseModel):
    peer_group: str = Field(..., description="Peer group identifier")
    company_size: str = Field(..., description="Company size category")
    industry: str = Field(..., description="Industry vertical")
    sample_size: int = Field(..., description="Number of organizations in benchmark")
    avg_score: float = Field(..., description="Average score in peer group")
    median_score: float = Field(..., description="Median score in peer group")
    p25: float = Field(..., description="25th percentile score")
    p50: float = Field(..., description="50th percentile score")
    p75: float = Field(..., description="75th percentile score")
    p90: float = Field(..., description="90th percentile score")
    grade_distribution: dict[str, int] = Field(..., description="Grade distribution counts")
    top_gaps: list[str] = Field(..., description="Most common compliance gaps")


class ImprovementSuggestionSchema(BaseModel):
    dimension: str = Field(..., description="Compliance dimension")
    current_score: float = Field(..., description="Current dimension score")
    target_score: float = Field(..., description="Target dimension score")
    impact_on_grade: str = Field(..., description="Estimated impact on overall grade")
    effort: str = Field(..., description="Effort level: low, medium, high")
    actions: list[str] = Field(..., description="Specific improvement actions")


class BenchmarkComparisonSchema(BaseModel):
    org_score: HealthScoreSchema = Field(..., description="Organization health score")
    benchmark: PeerBenchmarkSchema = Field(..., description="Peer benchmark data")
    rank_position: int = Field(..., description="Rank position in peer group")
    total_in_group: int = Field(..., description="Total organizations in peer group")
    gap_to_median: float = Field(..., description="Score gap to peer median")
    gap_to_p75: float = Field(..., description="Score gap to 75th percentile")
    improvement_suggestions: list[ImprovementSuggestionSchema] = Field(
        ..., description="Top improvement suggestions"
    )


class ScoreHistorySchema(BaseModel):
    scores: list[HealthScoreSchema] = Field(..., description="Historical scores")
    trend_direction: str = Field(..., description="Trend direction: up, down, stable")
    trend_pct: float = Field(..., description="Trend percentage change")
    period_days: int = Field(..., description="History period in days")


class LeaderboardEntrySchema(BaseModel):
    rank: int = Field(..., description="Leaderboard rank")
    org_name_anonymized: str = Field(..., description="Anonymized organization name")
    industry: str = Field(..., description="Industry vertical")
    score: float = Field(..., description="Health score")
    grade: str = Field(..., description="Letter grade")
    trend: str = Field(..., description="Score trend: up, down, stable")


class BoardReportSchema(BaseModel):
    id: str = Field(..., description="Report ID")
    title: str = Field(..., description="Report title")
    overall_score: float = Field(..., description="Overall health score")
    grade: str = Field(..., description="Letter grade")
    percentile: float = Field(..., description="Percentile rank")
    highlights: list[str] = Field(..., description="Key highlights")
    risks: list[str] = Field(..., description="Identified risks")
    action_items: list[str] = Field(..., description="Recommended actions")
    generated_at: str | None = Field(None, description="ISO timestamp of generation")
    format: str = Field(..., description="Report format (pdf, html, json)")


class BoardReportRequest(BaseModel):
    industry: str = Field("saas", description="Industry for benchmarking")
    format: str = Field("pdf", description="Report format: pdf, html, json")


class IndustryStatsSchema(BaseModel):
    industry: str = Field(..., description="Industry identifier")
    sample_size: int = Field(..., description="Number of organizations")
    avg_score: float = Field(..., description="Average health score")
    median_score: float = Field(..., description="Median health score")


# --- Helper functions ---

def _score_to_schema(score) -> HealthScoreSchema:
    return HealthScoreSchema(
        id=str(score.id),
        org_id=score.org_id,
        overall_score=score.overall_score,
        grade=score.grade.value if hasattr(score.grade, "value") else str(score.grade),
        dimensions=score.dimensions,
        framework_scores=score.framework_scores,
        percentile=score.percentile,
        peer_group=score.peer_group,
        computed_at=score.computed_at.isoformat() if score.computed_at else None,
    )


def _benchmark_to_schema(b) -> PeerBenchmarkSchema:
    return PeerBenchmarkSchema(
        peer_group=b.peer_group,
        company_size=b.company_size.value if hasattr(b.company_size, "value") else str(b.company_size),
        industry=b.industry,
        sample_size=b.sample_size,
        avg_score=b.avg_score,
        median_score=b.median_score,
        p25=b.p25, p50=b.p50, p75=b.p75, p90=b.p90,
        grade_distribution=b.grade_distribution,
        top_gaps=b.top_gaps,
    )


def _suggestion_to_schema(s) -> ImprovementSuggestionSchema:
    return ImprovementSuggestionSchema(
        dimension=s.dimension,
        current_score=s.current_score,
        target_score=s.target_score,
        impact_on_grade=s.impact_on_grade,
        effort=s.effort,
        actions=s.actions,
    )


def _get_service(db, copilot):
    from app.services.health_benchmarking import HealthBenchmarkingService
    return HealthBenchmarkingService(db=db, copilot_client=copilot)


# --- Endpoints ---

@router.get("/score", response_model=HealthScoreSchema, summary="Compute current health score")
async def compute_health_score(
    db: DB,
    copilot: CopilotDep,
    org: CurrentOrganization,
    member: OrgMember,
    industry: str = "saas",
    company_size: str = "medium",
) -> HealthScoreSchema:
    """Compute or retrieve the current compliance health score for the organization."""
    service = _get_service(db, copilot)
    score = await service.compute_health_score(str(org.id), industry, company_size)
    return _score_to_schema(score)


@router.get("/benchmark/{industry}", response_model=PeerBenchmarkSchema, summary="Get industry benchmark")
async def get_peer_benchmark(
    industry: str,
    db: DB,
    copilot: CopilotDep,
    member: OrgMember,
    company_size: str | None = None,
) -> PeerBenchmarkSchema:
    """Get aggregated benchmark data for a specific industry peer group."""
    service = _get_service(db, copilot)
    try:
        benchmark = await service.get_peer_benchmark(industry, company_size)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _benchmark_to_schema(benchmark)


@router.get("/compare", response_model=BenchmarkComparisonSchema, summary="Compare to peers")
async def compare_to_peers(
    db: DB,
    copilot: CopilotDep,
    org: CurrentOrganization,
    member: OrgMember,
    industry: str = "saas",
    company_size: str | None = None,
) -> BenchmarkComparisonSchema:
    """Compare the organization's health score against its industry peer group."""
    service = _get_service(db, copilot)
    try:
        comparison = await service.compare_to_peers(str(org.id), industry, company_size)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return BenchmarkComparisonSchema(
        org_score=_score_to_schema(comparison.org_score),
        benchmark=_benchmark_to_schema(comparison.benchmark),
        rank_position=comparison.rank_position,
        total_in_group=comparison.total_in_group,
        gap_to_median=comparison.gap_to_median,
        gap_to_p75=comparison.gap_to_p75,
        improvement_suggestions=[_suggestion_to_schema(s) for s in comparison.improvement_suggestions],
    )


@router.get("/history", response_model=ScoreHistorySchema, summary="Get score history")
async def get_score_history(
    db: DB,
    copilot: CopilotDep,
    org: CurrentOrganization,
    member: OrgMember,
    days: int = 90,
) -> ScoreHistorySchema:
    """Get historical health scores with trend analysis."""
    service = _get_service(db, copilot)
    history = await service.get_score_history(str(org.id), days=days)
    return ScoreHistorySchema(
        scores=[_score_to_schema(s) for s in history.scores],
        trend_direction=history.trend_direction,
        trend_pct=history.trend_pct,
        period_days=history.period_days,
    )


@router.get(
    "/leaderboard/{industry}",
    response_model=list[LeaderboardEntrySchema],
    summary="Get industry leaderboard",
)
async def get_leaderboard(
    industry: str,
    db: DB,
    copilot: CopilotDep,
    member: OrgMember,
    limit: int = 20,
) -> list[LeaderboardEntrySchema]:
    """Get an anonymized industry leaderboard for gamification and peer comparison."""
    service = _get_service(db, copilot)
    try:
        entries = await service.get_leaderboard(industry, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return [
        LeaderboardEntrySchema(
            rank=e.rank,
            org_name_anonymized=e.org_name_anonymized,
            industry=e.industry,
            score=e.score,
            grade=e.grade.value if hasattr(e.grade, "value") else str(e.grade),
            trend=e.trend,
        )
        for e in entries
    ]


@router.post("/board-report", response_model=BoardReportSchema, summary="Generate board report")
async def generate_board_report(
    request: BoardReportRequest,
    db: DB,
    copilot: CopilotDep,
    org: CurrentOrganization,
    member: OrgMember,
) -> BoardReportSchema:
    """Generate an executive board-ready compliance health report."""
    service = _get_service(db, copilot)
    try:
        report = await service.generate_board_report(str(org.id), request.industry, request.format)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return BoardReportSchema(
        id=str(report.id),
        title=report.title,
        overall_score=report.org_score.overall_score,
        grade=report.org_score.grade.value if hasattr(report.org_score.grade, "value") else str(report.org_score.grade),
        percentile=report.org_score.percentile,
        highlights=report.highlights,
        risks=report.risks,
        action_items=report.action_items,
        generated_at=report.generated_at.isoformat() if report.generated_at else None,
        format=report.format,
    )


@router.get(
    "/improvement-plan",
    response_model=list[ImprovementSuggestionSchema],
    summary="Get improvement plan",
)
async def get_improvement_plan(
    db: DB,
    copilot: CopilotDep,
    org: CurrentOrganization,
    member: OrgMember,
    target_grade: str = "A",
) -> list[ImprovementSuggestionSchema]:
    """Get a personalized improvement plan to reach a target compliance grade."""
    service = _get_service(db, copilot)
    suggestions = await service.get_improvement_plan(str(org.id), target_grade=target_grade)
    return [_suggestion_to_schema(s) for s in suggestions]


@router.get(
    "/industries",
    response_model=list[IndustryStatsSchema],
    summary="List available industries",
)
async def list_industries(
    db: DB,
    copilot: CopilotDep,
    member: OrgMember,
) -> list[IndustryStatsSchema]:
    """List all available industries with benchmark statistics."""
    from app.services.health_benchmarking.service import _INDUSTRY_BENCHMARKS

    return [
        IndustryStatsSchema(
            industry=key,
            sample_size=b.sample_size,
            avg_score=b.avg_score,
            median_score=b.median_score,
        )
        for key, b in _INDUSTRY_BENCHMARKS.items()
    ]
