"""API endpoints for Regulatory Harmonization Engine."""


import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.harmonization_engine import HarmonizationEngineService


logger = structlog.get_logger()
router = APIRouter()


class AnalyzeRequest(BaseModel):
    frameworks: list[str] = Field(...)


class OverlapSchema(BaseModel):
    control_a_framework: str
    control_a_id: str
    control_b_framework: str
    control_b_id: str
    overlap_strength: str
    effort_savings_pct: float


class HarmonizationResultSchema(BaseModel):
    id: str
    frameworks: list[str]
    total_controls: int
    unique_controls: int
    overlapping_controls: int
    deduplication_pct: float
    recommendations: list[str]


class ControlSchema(BaseModel):
    framework: str
    control_id: str
    control_name: str
    category: str


class HarmonizationStatsSchema(BaseModel):
    analyses_run: int
    frameworks_analyzed: int
    total_overlaps_found: int
    avg_deduplication_pct: float


@router.post("/analyze", response_model=HarmonizationResultSchema, summary="Analyze framework overlap")
async def analyze_overlap(request: AnalyzeRequest, db: DB) -> HarmonizationResultSchema:
    service = HarmonizationEngineService(db=db)
    result = await service.analyze_overlap(request.frameworks)
    return HarmonizationResultSchema(
        id=str(result.id),
        frameworks=result.frameworks,
        total_controls=result.total_controls,
        unique_controls=result.unique_controls,
        overlapping_controls=result.overlapping_controls,
        deduplication_pct=result.deduplication_pct,
        recommendations=result.recommendations,
    )


@router.get("/controls/{framework}", response_model=list[ControlSchema], summary="List framework controls")
async def list_controls(framework: str, db: DB) -> list[ControlSchema]:
    service = HarmonizationEngineService(db=db)
    controls = await service.list_controls(framework)
    return [
        ControlSchema(
            framework=c.framework,
            control_id=c.control_id,
            control_name=c.control_name,
            category=c.category.value,
        )
        for c in controls
    ]


@router.get("/stats", response_model=HarmonizationStatsSchema, summary="Get harmonization stats")
async def get_stats(db: DB) -> HarmonizationStatsSchema:
    service = HarmonizationEngineService(db=db)
    s = await service.get_stats()
    return HarmonizationStatsSchema(
        analyses_run=s.analyses_run,
        frameworks_analyzed=s.frameworks_analyzed,
        total_overlaps_found=s.total_overlaps_found,
        avg_deduplication_pct=s.avg_deduplication_pct,
    )
