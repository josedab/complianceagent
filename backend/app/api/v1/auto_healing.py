"""API endpoints for Auto-Healing Pipeline."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB


logger = structlog.get_logger()
router = APIRouter()


def _serialize(obj):
    """Convert a dataclass to a JSON-serializable dict."""
    from dataclasses import fields, is_dataclass

    if not is_dataclass(obj):
        return obj

    result = {}
    for f in fields(obj):
        v = getattr(obj, f.name)
        result[f.name] = _ser_val(v)
    return result


def _ser_val(v):
    from dataclasses import is_dataclass
    from datetime import datetime
    from enum import Enum
    from uuid import UUID

    if v is None:
        return None
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, UUID):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, list):
        return [_ser_val(item) for item in v]
    if isinstance(v, dict):
        return {k: _ser_val(val) for k, val in v.items()}
    if is_dataclass(v):
        return _serialize(v)
    return v


# --- Schemas ---


class TriggerPipelineRequest(BaseModel):
    trigger_type: str = Field(
        ..., description="Type of trigger (e.g. 'manual', 'scheduled', 'webhook')"
    )
    repository: str = Field(..., description="Repository to run pipeline against")
    regulation: str = Field(..., description="Regulation framework to check")
    branch: str = Field("main", description="Branch to target")


class PipelineRunResponse(BaseModel):
    model_config = {"extra": "ignore"}
    id: str = ""
    trigger_type: str = ""
    trigger_source: str = ""
    state: str = ""
    repository: str = ""
    branch: str = ""
    regulation: str = ""
    violations_detected: int = 0
    fixes_generated: int = 0
    fixes_applied: int = 0
    tests_passed: bool = False
    pr_number: int | None = None
    pr_url: str | None = None
    approval_policy: str = ""
    approved_by: str | None = None
    error_message: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


class PipelineRunListResponse(BaseModel):
    model_config = {"extra": "ignore"}
    runs: list[PipelineRunResponse] = Field(default_factory=list)


class ApproveRunRequest(BaseModel):
    approver: str = Field(..., description="Name of the approver")


class RejectRunRequest(BaseModel):
    reason: str = Field(..., description="Reason for rejection")


class PipelineConfigResponse(BaseModel):
    model_config = {"extra": "ignore"}
    enabled: bool = True
    auto_merge_low_risk: bool = False
    require_tests_pass: bool = True
    max_fixes_per_run: int = 20
    approval_policy: str = ""
    notify_channels: list[str] = Field(default_factory=list)
    excluded_paths: list[str] = Field(default_factory=list)
    cooldown_minutes: int = 30


class UpdatePipelineConfigRequest(BaseModel):
    auto_approve: bool | None = None
    max_concurrent_runs: int | None = None
    default_branch: str | None = None
    notifications_enabled: bool | None = None
    config: dict[str, Any] | None = None


class PipelineMetricsResponse(BaseModel):
    model_config = {"extra": "ignore"}
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    rejected_runs: int = 0
    avg_time_to_fix_hours: float = 0.0
    auto_merge_rate: float = 0.0
    fix_acceptance_rate: float = 0.0
    violations_resolved: int = 0


# --- Endpoints ---


@router.post(
    "/trigger",
    response_model=PipelineRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger auto-healing pipeline",
)
async def trigger_pipeline(request: TriggerPipelineRequest, db: DB) -> PipelineRunResponse:
    """Trigger an auto-healing pipeline run for a repository."""
    from app.services.auto_healing import AutoHealingService, TriggerType

    service = AutoHealingService(db=db)
    run = await service.trigger_pipeline(
        trigger_type=TriggerType(request.trigger_type)
        if isinstance(request.trigger_type, str)
        else request.trigger_type,
        repository=request.repository,
        regulation=request.regulation,
        branch=request.branch,
    )
    return PipelineRunResponse(**_serialize(run))


@router.get("/runs", response_model=PipelineRunListResponse, summary="List pipeline runs")
async def list_pipeline_runs(
    db: DB,
    state: str | None = None,
    limit: int = 50,
) -> PipelineRunListResponse:
    """List auto-healing pipeline runs with optional state filter."""
    from app.services.auto_healing import AutoHealingService

    service = AutoHealingService(db=db)
    runs = await service.list_runs(state=state, limit=limit)
    return PipelineRunListResponse(
        runs=[PipelineRunResponse(**_serialize(r)) for r in runs],
        total=len(runs),
    )


@router.get(
    "/runs/{run_id}", response_model=PipelineRunResponse, summary="Get pipeline run details"
)
async def get_pipeline_run(run_id: UUID, db: DB) -> PipelineRunResponse:
    """Get details of a specific pipeline run."""
    from app.services.auto_healing import AutoHealingService

    service = AutoHealingService(db=db)
    run = await service.get_run(run_id=run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline run not found")
    return PipelineRunResponse(**_serialize(run))


@router.post(
    "/runs/{run_id}/approve", response_model=PipelineRunResponse, summary="Approve a pipeline run"
)
async def approve_run(run_id: UUID, request: ApproveRunRequest, db: DB) -> PipelineRunResponse:
    """Approve a pipeline run that is pending approval."""
    from app.services.auto_healing import AutoHealingService

    service = AutoHealingService(db=db)
    run = await service.approve_run(run_id=run_id, approver=request.approver)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline run not found")
    return PipelineRunResponse(**_serialize(run))


@router.post(
    "/runs/{run_id}/reject", response_model=PipelineRunResponse, summary="Reject a pipeline run"
)
async def reject_run(run_id: UUID, request: RejectRunRequest, db: DB) -> PipelineRunResponse:
    """Reject a pipeline run with a reason."""
    from app.services.auto_healing import AutoHealingService

    service = AutoHealingService(db=db)
    run = await service.reject_run(run_id=run_id, reason=request.reason)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline run not found")
    return PipelineRunResponse(**_serialize(run))


@router.get("/config", response_model=PipelineConfigResponse, summary="Get pipeline configuration")
async def get_pipeline_config(db: DB) -> PipelineConfigResponse:
    """Get the current auto-healing pipeline configuration."""
    from app.services.auto_healing import AutoHealingService

    service = AutoHealingService(db=db)
    config = await service.get_config()
    return PipelineConfigResponse(**_serialize(config))


@router.put(
    "/config", response_model=PipelineConfigResponse, summary="Update pipeline configuration"
)
async def update_pipeline_config(
    request: UpdatePipelineConfigRequest, db: DB
) -> PipelineConfigResponse:
    """Update the auto-healing pipeline configuration."""
    from app.services.auto_healing import AutoHealingService

    service = AutoHealingService(db=db)
    config = await service.update_config(**request.model_dump(exclude_none=True))
    return PipelineConfigResponse(**_serialize(config))


@router.get("/metrics", response_model=PipelineMetricsResponse, summary="Get pipeline metrics")
async def get_pipeline_metrics(db: DB) -> PipelineMetricsResponse:
    """Get metrics for auto-healing pipeline runs."""
    from app.services.auto_healing import AutoHealingService

    service = AutoHealingService(db=db)
    metrics = await service.get_metrics()
    return PipelineMetricsResponse(**_serialize(metrics))
