"""API endpoints for Self-Healing Compliance Mesh."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.self_healing_mesh import (
    EventType,
    HealingEvent,
    PipelineStage,
    SelfHealingMeshService,
)


logger = structlog.get_logger()
router = APIRouter()


class IngestEventRequest(BaseModel):
    event_type: str = Field(default="violation_detected")
    source_service: str = Field(default="")
    repo: str = Field(default="")
    severity: str = Field(default="medium")
    description: str = Field(default="")
    payload: dict[str, Any] = Field(default_factory=dict)


class PipelineSchema(BaseModel):
    id: str
    repo: str
    stage: str
    risk_tier: str
    stages_completed: list[str]
    fix_description: str
    files_changed: list[str]
    test_passed: bool
    pr_url: str
    time_to_heal_seconds: float
    created_at: str | None


class MeshStatsSchema(BaseModel):
    total_events: int
    total_pipelines: int
    completed_pipelines: int
    auto_merged: int
    escalated: int
    avg_heal_time_seconds: float
    by_stage: dict[str, int]
    by_event_type: dict[str, int]


@router.post("/events", response_model=PipelineSchema, status_code=status.HTTP_201_CREATED, summary="Ingest healing event")
async def ingest_event(request: IngestEventRequest, db: DB) -> PipelineSchema:
    service = SelfHealingMeshService(db=db)
    event = HealingEvent(event_type=EventType(request.event_type), source_service=request.source_service, repo=request.repo, severity=request.severity, description=request.description, payload=request.payload)
    p = await service.ingest_event(event)
    return PipelineSchema(id=str(p.id), repo=p.repo, stage=p.stage.value, risk_tier=p.risk_tier.value, stages_completed=p.stages_completed, fix_description=p.fix_description, files_changed=p.files_changed, test_passed=p.test_passed, pr_url=p.pr_url, time_to_heal_seconds=p.time_to_heal_seconds, created_at=p.created_at.isoformat() if p.created_at else None)


@router.get("/pipelines", response_model=list[PipelineSchema], summary="List pipelines")
async def list_pipelines(db: DB, stage: str | None = None, repo: str | None = None) -> list[PipelineSchema]:
    service = SelfHealingMeshService(db=db)
    s = PipelineStage(stage) if stage else None
    pipelines = service.list_pipelines(stage=s, repo=repo)
    return [PipelineSchema(id=str(p.id), repo=p.repo, stage=p.stage.value, risk_tier=p.risk_tier.value, stages_completed=p.stages_completed, fix_description=p.fix_description, files_changed=p.files_changed, test_passed=p.test_passed, pr_url=p.pr_url, time_to_heal_seconds=p.time_to_heal_seconds, created_at=p.created_at.isoformat() if p.created_at else None) for p in pipelines]


@router.post("/pipelines/{pipeline_id}/approve", summary="Approve pipeline")
async def approve_pipeline(pipeline_id: str, db: DB) -> dict:
    service = SelfHealingMeshService(db=db)
    p = await service.approve_pipeline(pipeline_id)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found or not awaiting approval")
    return {"status": "approved", "pipeline_id": pipeline_id}


@router.get("/stats", response_model=MeshStatsSchema, summary="Get mesh stats")
async def get_stats(db: DB) -> MeshStatsSchema:
    service = SelfHealingMeshService(db=db)
    s = service.get_stats()
    return MeshStatsSchema(total_events=s.total_events, total_pipelines=s.total_pipelines, completed_pipelines=s.completed_pipelines, auto_merged=s.auto_merged, escalated=s.escalated, avg_heal_time_seconds=s.avg_heal_time_seconds, by_stage=s.by_stage, by_event_type=s.by_event_type)
