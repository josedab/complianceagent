"""API endpoints for Automated Compliance Remediation Workflows."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.remediation_workflow import RemediationWorkflowService, RemediationPriority, WorkflowState

logger = structlog.get_logger()
router = APIRouter()


class CreateWorkflowRequest(BaseModel):
    title: str = Field(..., min_length=1)
    violation_id: str = Field(...)
    framework: str = Field(...)
    repository: str = Field(...)
    priority: str = Field(default="medium")
    description: str = Field(default="")


class ApproveRequest(BaseModel):
    approver: str = Field(...)


class WorkflowSchema(BaseModel):
    id: str
    title: str
    description: str
    state: str
    priority: str
    violation_id: str
    framework: str
    repository: str
    fixes_count: int
    pr_number: int | None
    pr_url: str | None
    rollback_available: bool
    created_at: str | None


class FixSchema(BaseModel):
    id: str
    file_path: str
    description: str
    confidence: float


def _wf_to_schema(wf) -> WorkflowSchema:
    return WorkflowSchema(
        id=str(wf.id), title=wf.title, description=wf.description,
        state=wf.state.value, priority=wf.priority.value,
        violation_id=wf.violation_id, framework=wf.framework,
        repository=wf.repository, fixes_count=len(wf.fixes),
        pr_number=wf.pr_number, pr_url=wf.pr_url,
        rollback_available=wf.rollback_available,
        created_at=wf.created_at.isoformat() if wf.created_at else None,
    )


@router.post("/workflows", response_model=WorkflowSchema, status_code=status.HTTP_201_CREATED,
             summary="Create remediation workflow")
async def create_workflow(request: CreateWorkflowRequest, db: DB, copilot: CopilotDep) -> WorkflowSchema:
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    priority = RemediationPriority(request.priority) if request.priority in [p.value for p in RemediationPriority] else RemediationPriority.MEDIUM
    wf = await service.create_workflow(
        title=request.title, violation_id=request.violation_id,
        framework=request.framework, repository=request.repository,
        priority=priority, description=request.description,
    )
    return _wf_to_schema(wf)


@router.get("/workflows", response_model=list[WorkflowSchema], summary="List workflows")
async def list_workflows(db: DB, copilot: CopilotDep, state: str | None = None) -> list[WorkflowSchema]:
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    ws = WorkflowState(state) if state else None
    workflows = await service.list_workflows(state=ws)
    return [_wf_to_schema(wf) for wf in workflows]


@router.post("/workflows/{workflow_id}/generate", response_model=WorkflowSchema, summary="Generate fixes")
async def generate_fixes(workflow_id: str, db: DB, copilot: CopilotDep) -> WorkflowSchema:
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    try:
        wf = await service.generate_fixes(UUID(workflow_id))
        return _wf_to_schema(wf)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/workflows/{workflow_id}/approve", response_model=WorkflowSchema, summary="Approve workflow")
async def approve_workflow(workflow_id: str, request: ApproveRequest, db: DB, copilot: CopilotDep) -> WorkflowSchema:
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    try:
        wf = await service.approve_workflow(UUID(workflow_id), request.approver)
        return _wf_to_schema(wf)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workflows/{workflow_id}/merge", response_model=WorkflowSchema, summary="Merge workflow")
async def merge_workflow(workflow_id: str, db: DB, copilot: CopilotDep) -> WorkflowSchema:
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    try:
        wf = await service.merge_workflow(UUID(workflow_id))
        return _wf_to_schema(wf)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workflows/{workflow_id}/rollback", response_model=WorkflowSchema, summary="Rollback workflow")
async def rollback_workflow(workflow_id: str, db: DB, copilot: CopilotDep) -> WorkflowSchema:
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    try:
        wf = await service.rollback_workflow(UUID(workflow_id))
        return _wf_to_schema(wf)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/config", summary="Get workflow configuration")
async def get_config(db: DB, copilot: CopilotDep) -> dict:
    service = RemediationWorkflowService(db=db, copilot_client=copilot)
    cfg = await service.get_config()
    return {
        "auto_merge_low_risk": cfg.auto_merge_low_risk, "require_ci_pass": cfg.require_ci_pass,
        "require_review": cfg.require_review, "max_auto_fixes_per_day": cfg.max_auto_fixes_per_day,
    }
