"""API endpoints for Compliance Workflow Automation."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.workflow_automation import WorkflowAutomationService


logger = structlog.get_logger()
router = APIRouter()


class CreateWorkflowRequest(BaseModel):
    name: str = Field(...)
    description: str = Field(default="")
    trigger: str = Field(default="manual")
    steps: list[dict[str, Any]] = Field(default_factory=list)
    framework: str = Field(default="")
    owner: str = Field(default="")


class FromTemplateRequest(BaseModel):
    template_id: str = Field(...)
    name: str = Field(...)
    overrides: dict[str, Any] = Field(default_factory=dict)


class WorkflowSchema(BaseModel):
    id: str
    name: str
    description: str
    trigger: str
    steps: list[dict[str, Any]]
    framework: str
    owner: str
    status: str
    created_at: str | None


class TemplateSchema(BaseModel):
    id: str
    name: str
    description: str
    framework: str
    steps: list[dict[str, Any]]
    category: str


class ExecutionSchema(BaseModel):
    id: str
    workflow_id: str
    status: str
    current_step: int
    total_steps: int
    started_at: str | None
    completed_at: str | None
    output: dict[str, Any]


class WorkflowStatsSchema(BaseModel):
    total_workflows: int
    active_workflows: int
    total_executions: int
    completed_executions: int
    failed_executions: int
    by_trigger: dict[str, int]
    by_framework: dict[str, int]
    avg_execution_seconds: float


@router.post("/workflows", response_model=WorkflowSchema, status_code=status.HTTP_201_CREATED, summary="Create workflow")
async def create_workflow(request: CreateWorkflowRequest, db: DB) -> WorkflowSchema:
    service = WorkflowAutomationService(db=db)
    w = await service.create_workflow(
        name=request.name, description=request.description, trigger=request.trigger,
        steps=request.steps, framework=request.framework, owner=request.owner,
    )
    return WorkflowSchema(
        id=str(w.id), name=w.name, description=w.description, trigger=w.trigger,
        steps=w.steps, framework=w.framework, owner=w.owner, status=w.status,
        created_at=w.created_at.isoformat() if w.created_at else None,
    )


@router.get("/workflows", response_model=list[WorkflowSchema], summary="List workflows")
async def list_workflows(db: DB, framework: str | None = None, owner: str | None = None) -> list[WorkflowSchema]:
    service = WorkflowAutomationService(db=db)
    workflows = service.list_workflows(framework=framework, owner=owner)
    return [
        WorkflowSchema(
            id=str(w.id), name=w.name, description=w.description, trigger=w.trigger,
            steps=w.steps, framework=w.framework, owner=w.owner, status=w.status,
            created_at=w.created_at.isoformat() if w.created_at else None,
        )
        for w in workflows
    ]


@router.post("/workflows/from-template", response_model=WorkflowSchema, status_code=status.HTTP_201_CREATED, summary="Create workflow from template")
async def from_template(request: FromTemplateRequest, db: DB) -> WorkflowSchema:
    service = WorkflowAutomationService(db=db)
    w = await service.from_template(
        template_id=request.template_id, name=request.name, overrides=request.overrides,
    )
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return WorkflowSchema(
        id=str(w.id), name=w.name, description=w.description, trigger=w.trigger,
        steps=w.steps, framework=w.framework, owner=w.owner, status=w.status,
        created_at=w.created_at.isoformat() if w.created_at else None,
    )


@router.post("/workflows/{workflow_id}/execute", response_model=ExecutionSchema, summary="Execute workflow")
async def execute_workflow(workflow_id: str, db: DB) -> ExecutionSchema:
    service = WorkflowAutomationService(db=db)
    e = await service.execute(workflow_id)
    if not e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return ExecutionSchema(
        id=str(e.id), workflow_id=str(e.workflow_id), status=e.status,
        current_step=e.current_step, total_steps=e.total_steps,
        started_at=e.started_at.isoformat() if e.started_at else None,
        completed_at=e.completed_at.isoformat() if e.completed_at else None,
        output=e.output,
    )


@router.post("/workflows/{workflow_id}/pause", summary="Pause workflow")
async def pause_workflow(workflow_id: str, db: DB) -> dict:
    service = WorkflowAutomationService(db=db)
    ok = await service.pause(workflow_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found or not running")
    return {"status": "paused", "workflow_id": workflow_id}


@router.get("/templates", response_model=list[TemplateSchema], summary="List workflow templates")
async def list_templates(db: DB, framework: str | None = None) -> list[TemplateSchema]:
    service = WorkflowAutomationService(db=db)
    templates = service.list_templates(framework=framework)
    return [
        TemplateSchema(
            id=str(t.id), name=t.name, description=t.description,
            framework=t.framework, steps=t.steps, category=t.category,
        )
        for t in templates
    ]


@router.get("/executions", response_model=list[ExecutionSchema], summary="List executions")
async def list_executions(db: DB, workflow_id: str | None = None, execution_status: str | None = None) -> list[ExecutionSchema]:
    service = WorkflowAutomationService(db=db)
    executions = service.list_executions(workflow_id=workflow_id, status=execution_status)
    return [
        ExecutionSchema(
            id=str(e.id), workflow_id=str(e.workflow_id), status=e.status,
            current_step=e.current_step, total_steps=e.total_steps,
            started_at=e.started_at.isoformat() if e.started_at else None,
            completed_at=e.completed_at.isoformat() if e.completed_at else None,
            output=e.output,
        )
        for e in executions
    ]


@router.get("/stats", response_model=WorkflowStatsSchema, summary="Get workflow stats")
async def get_stats(db: DB) -> WorkflowStatsSchema:
    service = WorkflowAutomationService(db=db)
    s = service.get_stats()
    return WorkflowStatsSchema(
        total_workflows=s.total_workflows, active_workflows=s.active_workflows,
        total_executions=s.total_executions, completed_executions=s.completed_executions,
        failed_executions=s.failed_executions, by_trigger=s.by_trigger,
        by_framework=s.by_framework, avg_execution_seconds=s.avg_execution_seconds,
    )
