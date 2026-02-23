"""API endpoints for Compliance Auto-Remediation."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.auto_remediation import AutoRemediationService, RemediationStatus


logger = structlog.get_logger()
router = APIRouter()


class TriggerPipelineRequest(BaseModel):
    repo: str = Field(...)
    branch: str = Field(default="main")
    trigger_event: str = Field(default="push")
    violations: list[dict[str, Any]] = Field(default_factory=list)

class PipelineSchema(BaseModel):
    id: str
    repo: str
    branch: str
    trigger_event: str
    status: str
    risk_level: str
    approval_policy: str
    violations_detected: int
    fixes_generated: int
    pr_url: str
    created_at: str | None

class ApproveRequest(BaseModel):
    approver: str = Field(...)
    comment: str = Field(default="")

class RemediationConfigSchema(BaseModel):
    enabled: bool
    auto_merge_low_risk: bool
    scan_on_push: bool
    scan_on_schedule: bool
    schedule_cron: str
    target_frameworks: list[str]
    max_auto_fixes_per_run: int

class RemediationStatsSchema(BaseModel):
    total_pipelines: int
    by_status: dict[str, int]
    total_fixes_generated: int
    total_fixes_merged: int
    auto_merge_rate: float


@router.post("/pipelines", response_model=PipelineSchema, status_code=status.HTTP_201_CREATED, summary="Trigger remediation pipeline")
async def trigger_pipeline(request: TriggerPipelineRequest, db: DB) -> PipelineSchema:
    service = AutoRemediationService(db=db)
    pipeline = await service.trigger_pipeline(
        repo=request.repo, branch=request.branch,
        trigger_event=request.trigger_event, violations=request.violations,
    )
    return PipelineSchema(
        id=str(pipeline.id), repo=pipeline.repo, branch=pipeline.branch,
        trigger_event=pipeline.trigger_event, status=pipeline.status.value,
        risk_level=pipeline.risk_level.value, approval_policy=pipeline.approval_policy.value,
        violations_detected=pipeline.violations_detected, fixes_generated=pipeline.fixes_generated,
        pr_url=pipeline.pr_url,
        created_at=pipeline.created_at.isoformat() if pipeline.created_at else None,
    )

@router.get("/pipelines", response_model=list[PipelineSchema], summary="List pipelines")
async def list_pipelines(db: DB, repo: str | None = None, pipeline_status: str | None = None, limit: int = 50) -> list[PipelineSchema]:
    service = AutoRemediationService(db=db)
    s = RemediationStatus(pipeline_status) if pipeline_status else None
    pipelines = service.list_pipelines(repo=repo, status=s, limit=limit)
    return [
        PipelineSchema(
            id=str(p.id), repo=p.repo, branch=p.branch,
            trigger_event=p.trigger_event, status=p.status.value,
            risk_level=p.risk_level.value, approval_policy=p.approval_policy.value,
            violations_detected=p.violations_detected, fixes_generated=p.fixes_generated,
            pr_url=p.pr_url,
            created_at=p.created_at.isoformat() if p.created_at else None,
        ) for p in pipelines
    ]

@router.post("/pipelines/{pipeline_id}/approve", summary="Approve pipeline")
async def approve_pipeline(pipeline_id: UUID, request: ApproveRequest, db: DB) -> dict:
    service = AutoRemediationService(db=db)
    pipeline = await service.approve_pipeline(pipeline_id, request.approver, request.comment)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return {"status": "approved", "pipeline_id": str(pipeline_id), "pr_url": pipeline.pr_url}

@router.post("/pipelines/{pipeline_id}/reject", summary="Reject pipeline")
async def reject_pipeline(pipeline_id: UUID, request: ApproveRequest, db: DB) -> dict:
    service = AutoRemediationService(db=db)
    pipeline = await service.reject_pipeline(pipeline_id, request.approver, request.comment)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return {"status": "rejected", "pipeline_id": str(pipeline_id)}

@router.post("/pipelines/{pipeline_id}/rollback", summary="Rollback pipeline")
async def rollback_pipeline(pipeline_id: UUID, db: DB) -> dict:
    service = AutoRemediationService(db=db)
    pipeline = await service.rollback_pipeline(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return {"status": "rolled_back", "pipeline_id": str(pipeline_id)}

@router.get("/config", response_model=RemediationConfigSchema, summary="Get config")
async def get_config(db: DB) -> RemediationConfigSchema:
    service = AutoRemediationService(db=db)
    c = service.get_config()
    return RemediationConfigSchema(
        enabled=c.enabled, auto_merge_low_risk=c.auto_merge_low_risk,
        scan_on_push=c.scan_on_push, scan_on_schedule=c.scan_on_schedule,
        schedule_cron=c.schedule_cron, target_frameworks=c.target_frameworks,
        max_auto_fixes_per_run=c.max_auto_fixes_per_run,
    )

@router.get("/stats", response_model=RemediationStatsSchema, summary="Get stats")
async def get_stats(db: DB) -> RemediationStatsSchema:
    service = AutoRemediationService(db=db)
    s = service.get_stats()
    return RemediationStatsSchema(
        total_pipelines=s.total_pipelines, by_status=s.by_status,
        total_fixes_generated=s.total_fixes_generated, total_fixes_merged=s.total_fixes_merged,
        auto_merge_rate=s.auto_merge_rate,
    )
