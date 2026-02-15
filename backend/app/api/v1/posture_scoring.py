"""API endpoints for Compliance Posture Scoring & Benchmarking."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.posture_scoring import PostureScoringService

logger = structlog.get_logger()
router = APIRouter()


class DimensionSchema(BaseModel):
    dimension: str
    score: float
    weight: float
    findings: int
    recommendations: list[str]


class PostureScoreSchema(BaseModel):
    id: str
    overall_score: float
    grade: str
    dimensions: list[DimensionSchema]
    framework_scores: dict[str, float]
    trend_7d: float
    trend_30d: float
    percentile: float
    tier: str
    industry: str
    computed_at: str | None


class BenchmarkSchema(BaseModel):
    industry: str
    sample_size: int
    average_score: float
    median_score: float
    p25_score: float
    p75_score: float
    p90_score: float
    top_dimensions: list[str]


class ReportSchema(BaseModel):
    id: str
    title: str
    overall_score: float
    grade: str
    percentile: float
    highlights: list[str]
    action_items: list[str]
    format: str


@router.get("/score", response_model=PostureScoreSchema, summary="Compute compliance posture score")
async def compute_score(db: DB, copilot: CopilotDep, industry: str = "saas") -> PostureScoreSchema:
    service = PostureScoringService(db=db, copilot_client=copilot)
    score = await service.compute_score(industry=industry)
    return PostureScoreSchema(
        id=str(score.id), overall_score=score.overall_score, grade=score.grade,
        dimensions=[DimensionSchema(
            dimension=d.dimension.value, score=d.score, weight=d.weight,
            findings=d.findings, recommendations=d.recommendations,
        ) for d in score.dimensions],
        framework_scores=score.framework_scores, trend_7d=score.trend_7d,
        trend_30d=score.trend_30d, percentile=score.percentile,
        tier=score.tier.value, industry=score.industry,
        computed_at=score.computed_at.isoformat() if score.computed_at else None,
    )


@router.get("/benchmark/{industry}", response_model=BenchmarkSchema, summary="Get industry benchmark")
async def get_benchmark(industry: str, db: DB, copilot: CopilotDep) -> BenchmarkSchema:
    service = PostureScoringService(db=db, copilot_client=copilot)
    benchmark = await service.get_benchmark(industry)
    if not benchmark:
        raise HTTPException(status_code=404, detail=f"No benchmark data for industry: {industry}")
    return BenchmarkSchema(
        industry=benchmark.industry, sample_size=benchmark.sample_size,
        average_score=benchmark.average_score, median_score=benchmark.median_score,
        p25_score=benchmark.p25_score, p75_score=benchmark.p75_score,
        p90_score=benchmark.p90_score, top_dimensions=benchmark.top_dimensions,
    )


@router.get("/industries", summary="List available industries for benchmarking")
async def list_industries(db: DB, copilot: CopilotDep) -> list[str]:
    service = PostureScoringService(db=db, copilot_client=copilot)
    return await service.list_industries()


@router.post("/report", response_model=ReportSchema, summary="Generate executive posture report")
async def generate_report(db: DB, copilot: CopilotDep, industry: str = "saas", format: str = "html") -> ReportSchema:
    service = PostureScoringService(db=db, copilot_client=copilot)
    report = await service.generate_report(industry=industry, report_format=format)
    return ReportSchema(
        id=str(report.id), title=report.title, overall_score=report.posture.overall_score,
        grade=report.posture.grade, percentile=report.posture.percentile,
        highlights=report.highlights, action_items=report.action_items, format=report.format,
    )


@router.get("/history", summary="Get posture score history")
async def get_history(db: DB, copilot: CopilotDep, limit: int = 30) -> list[dict]:
    service = PostureScoringService(db=db, copilot_client=copilot)
    history = await service.get_history(limit=limit)
    return [{"score": s.overall_score, "grade": s.grade, "computed_at": s.computed_at.isoformat() if s.computed_at else None}
            for s in history]


# ── Dynamic Posture Scoring Dashboard ────────────────────────────────


class DimensionDetailSchema(BaseModel):
    dimension: str
    score: float
    max_score: float
    grade: str
    findings_count: int
    critical_findings: int
    drivers: list[dict[str, Any]]
    trend: str


class DynamicPostureScoreSchema(BaseModel):
    overall_score: float
    overall_grade: str
    dimensions: list[DimensionDetailSchema]
    calculated_at: str
    repo: str
    recommendations: list[str]


class DynamicIndustryBenchmarkSchema(BaseModel):
    industry: str
    your_score: float
    industry_avg: float
    industry_median: float
    industry_p75: float
    industry_p90: float
    percentile: float
    peer_count: int
    dimension_comparison: list[dict[str, Any]]


class ScoreHistorySchema(BaseModel):
    repo: str
    history: list[dict[str, Any]]
    trend: str
    improvement_rate: float


@router.get("/dynamic-score", response_model=DynamicPostureScoreSchema, summary="Compute dynamic compliance posture score")
async def compute_dynamic_score(db: DB, copilot: CopilotDep, repo: str = "default") -> DynamicPostureScoreSchema:
    """Compute dynamic compliance posture score with detailed dimension breakdowns."""
    service = PostureScoringService(db=db, copilot_client=copilot)
    score = service.compute_dynamic_score(repo)
    return DynamicPostureScoreSchema(**score.to_dict())


@router.get("/dynamic-benchmark/{industry}", response_model=DynamicIndustryBenchmarkSchema, summary="Get dynamic industry benchmark")
async def get_dynamic_benchmark(industry: str, db: DB, copilot: CopilotDep, repo: str = "default") -> DynamicIndustryBenchmarkSchema:
    """Get benchmark comparison against industry peers."""
    service = PostureScoringService(db=db, copilot_client=copilot)
    benchmark = service.get_dynamic_benchmark(industry, repo)
    return DynamicIndustryBenchmarkSchema(**benchmark.to_dict())


@router.get("/dynamic-history", response_model=ScoreHistorySchema, summary="Get dynamic score history")
async def get_dynamic_history(db: DB, copilot: CopilotDep, repo: str = "default") -> ScoreHistorySchema:
    """Get historical posture scores for trend tracking."""
    service = PostureScoringService(db=db, copilot_client=copilot)
    history = service.get_score_history(repo)
    return ScoreHistorySchema(**history.to_dict())
