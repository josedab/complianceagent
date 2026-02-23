"""API endpoints for Pipeline Builder."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.pipeline_builder import PipelineBuilderService


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class StepSchema(BaseModel):
    name: str = Field(..., description="Step name")
    action: str = Field(..., description="Step action type")
    config: dict[str, Any] = Field(default_factory=dict, description="Step configuration")


class CreatePipelineRequest(BaseModel):
    name: str = Field(..., description="Pipeline name")
    target: str = Field(..., description="Target platform")
    repo: str = Field(..., description="Repository URL")
    steps: list[StepSchema] = Field(..., description="Pipeline steps")


class CreateFromTemplateRequest(BaseModel):
    template_id: str = Field(..., description="Template identifier")
    repo: str = Field(..., description="Repository URL")


class PipelineSchema(BaseModel):
    id: str
    name: str
    target: str
    repo: str
    steps: list[StepSchema]
    status: str
    config: str | None
    created_at: str | None


class TemplateSchema(BaseModel):
    id: str
    name: str
    description: str
    target: str
    steps: list[StepSchema]


class PipelineStatsSchema(BaseModel):
    total_pipelines: int
    active_pipelines: int
    total_deployments: int
    total_templates: int


# --- Endpoints ---


@router.post("/pipelines", response_model=PipelineSchema, status_code=status.HTTP_201_CREATED, summary="Create pipeline")
async def create_pipeline(request: CreatePipelineRequest, db: DB) -> PipelineSchema:
    service = PipelineBuilderService(db=db)
    pipeline = await service.create_pipeline(
        name=request.name,
        target=request.target,
        repo=request.repo,
        steps=[{"name": s.name, "action": s.action, "config": s.config} for s in request.steps],
    )
    logger.info("pipeline_created", name=request.name, target=request.target)
    return PipelineSchema(
        id=str(pipeline.id), name=pipeline.name, target=pipeline.target,
        repo=pipeline.repo,
        steps=[StepSchema(name=s.name, action=s.action, config=s.config) for s in pipeline.steps],
        status=pipeline.status, config=pipeline.config,
        created_at=pipeline.created_at.isoformat() if pipeline.created_at else None,
    )


@router.post("/pipelines/from-template", response_model=PipelineSchema, status_code=status.HTTP_201_CREATED, summary="Create from template")
async def create_from_template(request: CreateFromTemplateRequest, db: DB) -> PipelineSchema:
    service = PipelineBuilderService(db=db)
    pipeline = await service.create_from_template(
        template_id=request.template_id,
        repo=request.repo,
    )
    if not pipeline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    logger.info("pipeline_from_template", template_id=request.template_id, repo=request.repo)
    return PipelineSchema(
        id=str(pipeline.id), name=pipeline.name, target=pipeline.target,
        repo=pipeline.repo,
        steps=[StepSchema(name=s.name, action=s.action, config=s.config) for s in pipeline.steps],
        status=pipeline.status, config=pipeline.config,
        created_at=pipeline.created_at.isoformat() if pipeline.created_at else None,
    )


@router.post("/pipelines/{pipeline_id}/generate", summary="Generate pipeline config")
async def generate_config(pipeline_id: str, db: DB) -> dict:
    service = PipelineBuilderService(db=db)
    config = await service.generate_config(pipeline_id=pipeline_id)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    logger.info("pipeline_config_generated", pipeline_id=pipeline_id)
    return {"pipeline_id": pipeline_id, "config": config}


@router.post("/pipelines/{pipeline_id}/deploy", summary="Deploy pipeline")
async def deploy_pipeline(pipeline_id: str, db: DB) -> dict:
    service = PipelineBuilderService(db=db)
    result = await service.deploy_pipeline(pipeline_id=pipeline_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    logger.info("pipeline_deployed", pipeline_id=pipeline_id)
    return {"pipeline_id": pipeline_id, "status": "deployed"}


@router.get("/pipelines", response_model=list[PipelineSchema], summary="List pipelines")
async def list_pipelines(db: DB) -> list[PipelineSchema]:
    service = PipelineBuilderService(db=db)
    pipelines = await service.list_pipelines()
    return [
        PipelineSchema(
            id=str(p.id), name=p.name, target=p.target, repo=p.repo,
            steps=[StepSchema(name=s.name, action=s.action, config=s.config) for s in p.steps],
            status=p.status, config=p.config,
            created_at=p.created_at.isoformat() if p.created_at else None,
        )
        for p in pipelines
    ]


@router.get("/templates", response_model=list[TemplateSchema], summary="List templates")
async def list_templates(db: DB) -> list[TemplateSchema]:
    service = PipelineBuilderService(db=db)
    templates = await service.list_templates()
    return [
        TemplateSchema(
            id=str(t.id), name=t.name, description=t.description, target=t.target,
            steps=[StepSchema(name=s.name, action=s.action, config=s.config) for s in t.steps],
        )
        for t in templates
    ]


@router.get("/stats", response_model=PipelineStatsSchema, summary="Get pipeline stats")
async def get_stats(db: DB) -> PipelineStatsSchema:
    service = PipelineBuilderService(db=db)
    s = await service.get_stats()
    return PipelineStatsSchema(
        total_pipelines=s.total_pipelines,
        active_pipelines=s.active_pipelines,
        total_deployments=s.total_deployments,
        total_templates=s.total_templates,
    )
