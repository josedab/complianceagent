"""API endpoints for Compliance Agents Marketplace."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.agents_marketplace import AgentCategory, AgentsMarketplaceService


logger = structlog.get_logger()
router = APIRouter()


class AgentSchema(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    category: str
    author: str
    version: str
    status: str
    downloads: int
    rating: float
    rating_count: int
    tags: list[str]
    frameworks: list[str]
    published_at: str | None


class PublishRequest(BaseModel):
    name: str = Field(...)
    slug: str = Field(...)
    description: str = Field(...)
    category: str = Field(default="checker")
    author: str = Field(...)
    mcp_tool_name: str = Field(default="")
    frameworks: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class InstallRequest(BaseModel):
    slug: str = Field(...)
    organization_id: str = Field(...)
    config: dict[str, Any] = Field(default_factory=dict)


class InstallSchema(BaseModel):
    id: str
    agent_id: str
    organization_id: str
    status: str
    installed_at: str | None


class RateRequest(BaseModel):
    slug: str = Field(...)
    reviewer: str = Field(...)
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="")


class ReviewSchema(BaseModel):
    id: str
    reviewer: str
    rating: int
    comment: str
    created_at: str | None


class StatsSchema(BaseModel):
    total_agents: int
    published_agents: int
    total_installations: int
    total_executions: int
    by_category: dict[str, int]
    top_agents: list[dict[str, Any]]


def _agent_to_schema(a: Any) -> AgentSchema:
    return AgentSchema(
        id=str(a.id),
        name=a.name,
        slug=a.slug,
        description=a.description,
        category=a.category.value,
        author=a.author,
        version=a.version,
        status=a.status.value,
        downloads=a.downloads,
        rating=a.rating,
        rating_count=a.rating_count,
        tags=a.tags,
        frameworks=a.frameworks,
        published_at=a.published_at.isoformat() if a.published_at else None,
    )


@router.get("/agents", response_model=list[AgentSchema], summary="Search marketplace agents")
async def search_agents(
    db: DB,
    query: str = "",
    category: str | None = None,
    framework: str | None = None,
    limit: int = 20,
) -> list[AgentSchema]:
    service = AgentsMarketplaceService(db=db)
    cat = AgentCategory(category) if category else None
    agents = service.search_agents(query=query, category=cat, framework=framework, limit=limit)
    return [_agent_to_schema(a) for a in agents]


@router.get("/agents/{slug}", response_model=AgentSchema, summary="Get agent details")
async def get_agent(slug: str, db: DB) -> AgentSchema:
    service = AgentsMarketplaceService(db=db)
    a = service.get_agent(slug)
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return _agent_to_schema(a)


@router.post(
    "/agents",
    response_model=AgentSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Publish agent",
)
async def publish_agent(request: PublishRequest, db: DB) -> AgentSchema:
    service = AgentsMarketplaceService(db=db)
    a = await service.publish_agent(
        name=request.name,
        slug=request.slug,
        description=request.description,
        category=request.category,
        author=request.author,
        mcp_tool_name=request.mcp_tool_name,
        frameworks=request.frameworks,
        tags=request.tags,
    )
    return _agent_to_schema(a)


@router.post("/agents/{slug}/approve", summary="Approve agent")
async def approve_agent(slug: str, db: DB) -> dict:
    service = AgentsMarketplaceService(db=db)
    a = await service.approve_agent(slug)
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return {"status": "approved", "slug": slug}


@router.post(
    "/install",
    response_model=InstallSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Install agent",
)
async def install_agent(request: InstallRequest, db: DB) -> InstallSchema:
    service = AgentsMarketplaceService(db=db)
    inst = await service.install_agent(
        slug=request.slug,
        organization_id=request.organization_id,
        config=request.config,
    )
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found or not published",
        )
    return InstallSchema(
        id=str(inst.id),
        agent_id=str(inst.agent_id),
        organization_id=inst.organization_id,
        status=inst.status.value,
        installed_at=inst.installed_at.isoformat() if inst.installed_at else None,
    )


@router.post(
    "/rate",
    response_model=ReviewSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Rate agent",
)
async def rate_agent(request: RateRequest, db: DB) -> ReviewSchema:
    service = AgentsMarketplaceService(db=db)
    r = await service.rate_agent(
        slug=request.slug,
        reviewer=request.reviewer,
        rating=request.rating,
        comment=request.comment,
    )
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return ReviewSchema(
        id=str(r.id),
        reviewer=r.reviewer,
        rating=r.rating,
        comment=r.comment,
        created_at=r.created_at.isoformat() if r.created_at else None,
    )


@router.get("/stats", response_model=StatsSchema, summary="Get marketplace stats")
async def get_stats(db: DB) -> StatsSchema:
    service = AgentsMarketplaceService(db=db)
    s = service.get_stats()
    return StatsSchema(
        total_agents=s.total_agents,
        published_agents=s.published_agents,
        total_installations=s.total_installations,
        total_executions=s.total_executions,
        by_category=s.by_category,
        top_agents=s.top_agents,
    )
