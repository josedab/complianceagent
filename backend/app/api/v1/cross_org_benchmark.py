"""API endpoints for Cross-Organization Compliance Benchmarking."""

from typing import Any

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.cross_org_benchmark import CrossOrgBenchmarkService


logger = structlog.get_logger()
router = APIRouter()


class ContributeRequest(BaseModel):
    industry: str = Field(...)
    org_size: str = Field(default="medium")
    overall_score: float = Field(...)
    framework_scores: dict[str, float] = Field(default_factory=dict)
    privacy_level: str = Field(default="standard")


class BenchmarkRequest(BaseModel):
    your_score: float = Field(...)
    industry: str = Field(...)
    org_size: str = Field(default="medium")


class BenchmarkResultSchema(BaseModel):
    industry: str
    your_score: float
    percentile: float
    industry_avg: float
    industry_median: float
    top_quartile: float
    peer_count: int
    framework_comparisons: list[dict[str, Any]]
    improvement_suggestions: list[str]


class TrendSchema(BaseModel):
    period: str
    data_points: list[dict[str, Any]]
    your_trend: str
    industry_trend: str


class StatsSchema(BaseModel):
    total_participants: int
    by_industry: dict[str, int]
    global_avg_score: float
    data_freshness_hours: float


@router.post(
    "/contribute", status_code=status.HTTP_201_CREATED, summary="Contribute anonymized data"
)
async def contribute_data(request: ContributeRequest, db: DB) -> dict:
    service = CrossOrgBenchmarkService(db=db)
    p = await service.contribute_data(
        industry=request.industry,
        org_size=request.org_size,
        overall_score=request.overall_score,
        framework_scores=request.framework_scores,
        privacy_level=request.privacy_level,
    )
    return {"status": "contributed", "id": str(p.id)}


@router.post("/benchmark", response_model=BenchmarkResultSchema, summary="Get benchmark comparison")
async def get_benchmark(request: BenchmarkRequest, db: DB) -> BenchmarkResultSchema:
    service = CrossOrgBenchmarkService(db=db)
    r = await service.get_benchmark(
        your_score=request.your_score, industry=request.industry, org_size=request.org_size
    )
    return BenchmarkResultSchema(
        industry=r.industry.value,
        your_score=r.your_score,
        percentile=r.percentile,
        industry_avg=r.industry_avg,
        industry_median=r.industry_median,
        top_quartile=r.top_quartile,
        peer_count=r.peer_count,
        framework_comparisons=r.framework_comparisons,
        improvement_suggestions=r.improvement_suggestions,
    )


@router.get("/trend/{industry}", response_model=TrendSchema, summary="Get benchmark trend")
async def get_trend(industry: str, db: DB, period: str = "30d") -> TrendSchema:
    service = CrossOrgBenchmarkService(db=db)
    t = service.get_trend(industry=industry, period=period)
    return TrendSchema(
        period=t.period,
        data_points=t.data_points,
        your_trend=t.your_trend,
        industry_trend=t.industry_trend,
    )


@router.get("/industries", summary="List industries")
async def list_industries(db: DB) -> list[dict]:
    service = CrossOrgBenchmarkService(db=db)
    return service.list_industries()


@router.get("/stats", response_model=StatsSchema, summary="Get benchmark stats")
async def get_stats(db: DB) -> StatsSchema:
    service = CrossOrgBenchmarkService(db=db)
    s = service.get_stats()
    return StatsSchema(
        total_participants=s.total_participants,
        by_industry=s.by_industry,
        global_avg_score=s.global_avg_score,
        data_freshness_hours=s.data_freshness_hours,
    )
