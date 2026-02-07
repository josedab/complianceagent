"""API endpoints for Regulatory Accuracy Benchmarking."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep

from app.services.benchmarking import BenchmarkingService


logger = structlog.get_logger()
router = APIRouter()


# --- Request/Response Schemas ---


class CorpusPassageSchema(BaseModel):
    """Annotated passage input."""

    framework: str
    article_ref: str
    text: str
    labels: list[str] = Field(default_factory=list)
    obligations: list[dict[str, Any]] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)


class CreateCorpusRequest(BaseModel):
    """Request to create a benchmark corpus."""

    name: str = Field(..., min_length=1, max_length=255)
    framework: str = Field(..., min_length=1)
    version: str = Field(default="1.0")
    passages: list[CorpusPassageSchema] = Field(default_factory=list)


class RunBenchmarkRequest(BaseModel):
    """Request to run a benchmark."""

    framework: str | None = Field(default=None, description="Filter by framework")
    model_version: str = Field(default="current", description="Model version label")


class MetricScoresSchema(BaseModel):
    """Metric scores response."""

    precision: float
    recall: float
    f1: float
    support: int


class BenchmarkResultSchema(BaseModel):
    """Benchmark result response."""

    id: str
    corpus_id: str
    model_version: str
    status: str
    label_scores: MetricScoresSchema
    obligation_scores: MetricScoresSchema
    entity_scores: MetricScoresSchema
    framework_scores: dict[str, MetricScoresSchema]
    overall_f1: float
    overall_precision: float
    overall_recall: float
    avg_latency_ms: float
    total_passages: int
    errors: int


class CorpusSummarySchema(BaseModel):
    """Corpus summary response."""

    name: str
    framework: str
    version: str
    total_passages: int


# --- Endpoints ---


@router.get(
    "/corpora",
    response_model=list[CorpusSummarySchema],
    summary="List benchmark corpora",
    description="List available benchmark corpora for accuracy evaluation",
)
async def list_corpora(
    db: DB,
    copilot: CopilotDep,
    framework: str | None = None,
) -> list[CorpusSummarySchema]:
    """List available benchmark corpora."""
    service = BenchmarkingService(db=db, copilot_client=copilot)
    corpora = await service.list_corpora(framework=framework)
    return [
        CorpusSummarySchema(
            name=c.name,
            framework=c.framework,
            version=c.version,
            total_passages=c.total_passages,
        )
        for c in corpora
    ]


@router.post(
    "/corpora",
    response_model=CorpusSummarySchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create benchmark corpus",
    description="Add a custom benchmark corpus with annotated passages",
)
async def create_corpus(
    request: CreateCorpusRequest,
    db: DB,
    copilot: CopilotDep,
) -> CorpusSummarySchema:
    """Create a custom benchmark corpus."""
    from app.services.benchmarking.models import (
        AnnotatedPassage,
        AnnotationLabel,
        BenchmarkCorpus,
    )

    passages = [
        AnnotatedPassage(
            framework=p.framework,
            article_ref=p.article_ref,
            text=p.text,
            labels=[AnnotationLabel(lbl) for lbl in p.labels if lbl in AnnotationLabel.__members__.values()],
            obligations=p.obligations,
            entities=p.entities,
        )
        for p in request.passages
    ]

    corpus = BenchmarkCorpus(
        name=request.name,
        framework=request.framework,
        version=request.version,
        passages=passages,
    )

    service = BenchmarkingService(db=db, copilot_client=copilot)
    result = await service.add_corpus(corpus)

    return CorpusSummarySchema(
        name=result.name,
        framework=result.framework,
        version=result.version,
        total_passages=result.total_passages,
    )


@router.post(
    "/run",
    response_model=BenchmarkResultSchema,
    summary="Run benchmark",
    description="Run accuracy benchmark against annotated corpus",
)
async def run_benchmark(
    request: RunBenchmarkRequest,
    db: DB,
    copilot: CopilotDep,
) -> BenchmarkResultSchema:
    """Run a benchmark evaluation."""
    service = BenchmarkingService(db=db, copilot_client=copilot)
    result = await service.run_benchmark(
        framework=request.framework,
        model_version=request.model_version,
    )

    return BenchmarkResultSchema(
        id=str(result.id),
        corpus_id=str(result.corpus_id),
        model_version=result.model_version,
        status=result.status.value,
        label_scores=MetricScoresSchema(**vars(result.label_scores)),
        obligation_scores=MetricScoresSchema(**vars(result.obligation_scores)),
        entity_scores=MetricScoresSchema(**vars(result.entity_scores)),
        framework_scores={
            fw: MetricScoresSchema(**vars(s)) for fw, s in result.framework_scores.items()
        },
        overall_f1=result.overall_f1,
        overall_precision=result.overall_precision,
        overall_recall=result.overall_recall,
        avg_latency_ms=result.avg_latency_ms,
        total_passages=result.total_passages,
        errors=result.errors,
    )


@router.get(
    "/results",
    response_model=list[BenchmarkResultSchema],
    summary="List benchmark results",
    description="List all previous benchmark run results",
)
async def list_results(
    db: DB,
    copilot: CopilotDep,
) -> list[BenchmarkResultSchema]:
    """List benchmark results."""
    service = BenchmarkingService(db=db, copilot_client=copilot)
    results = await service.list_results()
    return [
        BenchmarkResultSchema(
            id=str(r.id),
            corpus_id=str(r.corpus_id),
            model_version=r.model_version,
            status=r.status.value,
            label_scores=MetricScoresSchema(**vars(r.label_scores)),
            obligation_scores=MetricScoresSchema(**vars(r.obligation_scores)),
            entity_scores=MetricScoresSchema(**vars(r.entity_scores)),
            framework_scores={
                fw: MetricScoresSchema(**vars(s)) for fw, s in r.framework_scores.items()
            },
            overall_f1=r.overall_f1,
            overall_precision=r.overall_precision,
            overall_recall=r.overall_recall,
            avg_latency_ms=r.avg_latency_ms,
            total_passages=r.total_passages,
            errors=r.errors,
        )
        for r in results
    ]


@router.get(
    "/scorecard",
    summary="Get public scorecard",
    description="Get the public accuracy scorecard from the latest benchmark run",
)
async def get_scorecard(
    db: DB,
    copilot: CopilotDep,
    result_id: str | None = None,
) -> dict:
    """Get public accuracy scorecard."""
    service = BenchmarkingService(db=db, copilot_client=copilot)
    rid = UUID(result_id) if result_id else None
    scorecard = await service.get_scorecard(result_id=rid)

    if not scorecard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No benchmark results available. Run a benchmark first.",
        )

    return scorecard
