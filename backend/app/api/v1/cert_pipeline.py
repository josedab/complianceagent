"""API endpoints for Certification Pipeline."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.cert_pipeline import CertPipelineService


logger = structlog.get_logger()
router = APIRouter()


class CertifyRequest(BaseModel):
    repo: str = Field(...)
    framework: str = Field(...)
    owner: str = Field(default="")
    evidence_sources: list[str] = Field(default_factory=list)
    auto_advance: bool = Field(default=False)


class GapResolveRequest(BaseModel):
    resolution: str = Field(...)
    evidence_url: str = Field(default="")
    notes: str = Field(default="")


class CertRunSchema(BaseModel):
    id: str
    repo: str
    framework: str
    owner: str
    stage: str
    progress_pct: float
    gaps: list[dict[str, Any]]
    evidence_collected: int
    started_at: str | None
    completed_at: str | None


class GapSchema(BaseModel):
    id: str
    run_id: str
    control_id: str
    description: str
    severity: str
    status: str
    resolution: str
    evidence_url: str


class ReportSchema(BaseModel):
    run_id: str
    repo: str
    framework: str
    overall_status: str
    controls_passed: int
    controls_failed: int
    gaps_resolved: int
    gaps_open: int
    evidence_summary: list[dict[str, Any]]
    generated_at: str | None


class CertStatsSchema(BaseModel):
    total_runs: int
    completed_runs: int
    in_progress_runs: int
    total_gaps: int
    resolved_gaps: int
    by_framework: dict[str, int]
    avg_completion_days: float


@router.post("/certify", response_model=CertRunSchema, status_code=status.HTTP_201_CREATED, summary="Start certification run")
async def certify(request: CertifyRequest, db: DB) -> CertRunSchema:
    service = CertPipelineService(db=db)
    r = await service.certify(
        repo=request.repo, framework=request.framework, owner=request.owner,
        evidence_sources=request.evidence_sources, auto_advance=request.auto_advance,
    )
    return CertRunSchema(
        id=str(r.id), repo=r.repo, framework=r.framework, owner=r.owner,
        stage=r.stage, progress_pct=r.progress_pct, gaps=r.gaps,
        evidence_collected=r.evidence_collected,
        started_at=r.started_at.isoformat() if r.started_at else None,
        completed_at=r.completed_at.isoformat() if r.completed_at else None,
    )


@router.post("/certify/{run_id}/advance", summary="Advance certification stage")
async def advance(run_id: str, db: DB) -> dict:
    service = CertPipelineService(db=db)
    r = await service.advance(run_id)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found or cannot advance")
    return {"status": "advanced", "run_id": run_id, "new_stage": r.stage}


@router.post("/gaps/{gap_id}/resolve", response_model=GapSchema, summary="Resolve gap")
async def resolve_gap(gap_id: str, request: GapResolveRequest, db: DB) -> GapSchema:
    service = CertPipelineService(db=db)
    g = await service.resolve_gap(
        gap_id=gap_id, resolution=request.resolution,
        evidence_url=request.evidence_url, notes=request.notes,
    )
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gap not found")
    return GapSchema(
        id=str(g.id), run_id=str(g.run_id), control_id=g.control_id,
        description=g.description, severity=g.severity, status=g.status,
        resolution=g.resolution, evidence_url=g.evidence_url,
    )


@router.get("/runs", response_model=list[CertRunSchema], summary="List certification runs")
async def list_runs(db: DB, framework: str | None = None, repo: str | None = None) -> list[CertRunSchema]:
    service = CertPipelineService(db=db)
    runs = service.list_runs(framework=framework, repo=repo)
    return [
        CertRunSchema(
            id=str(r.id), repo=r.repo, framework=r.framework, owner=r.owner,
            stage=r.stage, progress_pct=r.progress_pct, gaps=r.gaps,
            evidence_collected=r.evidence_collected,
            started_at=r.started_at.isoformat() if r.started_at else None,
            completed_at=r.completed_at.isoformat() if r.completed_at else None,
        )
        for r in runs
    ]


@router.get("/runs/{run_id}/report", response_model=ReportSchema, summary="Get certification report")
async def get_report(run_id: str, db: DB) -> ReportSchema:
    service = CertPipelineService(db=db)
    rpt = service.get_report(run_id)
    if not rpt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return ReportSchema(
        run_id=str(rpt.run_id), repo=rpt.repo, framework=rpt.framework,
        overall_status=rpt.overall_status, controls_passed=rpt.controls_passed,
        controls_failed=rpt.controls_failed, gaps_resolved=rpt.gaps_resolved,
        gaps_open=rpt.gaps_open, evidence_summary=rpt.evidence_summary,
        generated_at=rpt.generated_at.isoformat() if rpt.generated_at else None,
    )


@router.get("/stats", response_model=CertStatsSchema, summary="Get certification stats")
async def get_stats(db: DB) -> CertStatsSchema:
    service = CertPipelineService(db=db)
    s = service.get_stats()
    return CertStatsSchema(
        total_runs=s.total_runs, completed_runs=s.completed_runs,
        in_progress_runs=s.in_progress_runs, total_gaps=s.total_gaps,
        resolved_gaps=s.resolved_gaps, by_framework=s.by_framework,
        avg_completion_days=s.avg_completion_days,
    )
