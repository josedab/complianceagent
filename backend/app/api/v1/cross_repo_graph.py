"""API endpoints for Cross-Repository Compliance Graph."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB


logger = structlog.get_logger()
router = APIRouter()


def _serialize(obj: Any) -> dict[str, Any]:
    """Convert a dataclass to a JSON-serializable dict."""
    from dataclasses import fields, is_dataclass

    if not is_dataclass(obj):
        return obj

    result = {}
    for f in fields(obj):
        v = getattr(obj, f.name)
        result[f.name] = _ser_val(v)
    return result


def _ser_val(v: Any) -> Any:
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


class BuildGraphRequest(BaseModel):
    organization_id: UUID = Field(..., description="Organization to build the graph for")


class RepoNodeResponse(BaseModel):
    model_config = {"extra": "ignore"}
    id: str = ""
    name: str = ""
    full_name: str = ""
    score: float = 0.0
    grade: str = ""
    violations: int = 0
    frameworks: list[str] = Field(default_factory=list)


class DependencyEdgeResponse(BaseModel):
    model_config = {"extra": "ignore"}
    source_repo: str = ""
    target_repo: str = ""
    dependency_type: str = ""
    shared_violations: list[str] = Field(default_factory=list)


class HotspotResponse(BaseModel):
    model_config = {"extra": "ignore"}
    component: str = ""
    repos_affected: list[str] = Field(default_factory=list)
    severity: str = ""
    framework: str = ""


class GraphResponse(BaseModel):
    model_config = {"extra": "ignore"}
    organization_id: str = ""
    nodes: list[RepoNodeResponse] = Field(default_factory=list)
    edges: list[DependencyEdgeResponse] = Field(default_factory=list)
    overall_score: float = 0.0
    hotspots: list[HotspotResponse] = Field(default_factory=list)


class OrgScoreResponse(BaseModel):
    model_config = {"extra": "ignore"}
    overall_score: float = 0.0
    repo_count: int = 0
    avg_violations: float = 0.0


# --- Endpoints ---


@router.post(
    "/build",
    response_model=GraphResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Build organization compliance graph",
)
async def build_graph(request: BuildGraphRequest, db: DB) -> GraphResponse:
    """Build the cross-repository compliance graph for an organization."""
    from app.services.cross_repo_graph import CrossRepoGraphService

    service = CrossRepoGraphService(db=db)
    graph = await service.build_org_graph(organization_id=request.organization_id)
    return GraphResponse(**_serialize(graph))


@router.get("/graph", response_model=GraphResponse, summary="Get organization compliance graph")
async def get_graph(db: DB) -> GraphResponse:
    """Get the full organization compliance graph."""
    from app.services.cross_repo_graph import CrossRepoGraphService

    service = CrossRepoGraphService(db=db)
    graph = await service.build_org_graph(organization_id="default")
    if not graph:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph not built yet")
    return GraphResponse(**_serialize(graph))


@router.get(
    "/repos/{repo_name}", response_model=RepoNodeResponse, summary="Get single repository node"
)
async def get_repo_node(repo_name: str, db: DB) -> RepoNodeResponse:
    """Get compliance details for a single repository in the graph."""
    from app.services.cross_repo_graph import CrossRepoGraphService

    service = CrossRepoGraphService(db=db)
    node = await service.get_repo_node(repo_name=repo_name)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found in graph"
        )
    return RepoNodeResponse(**_serialize(node))


@router.get(
    "/dependencies", response_model=list[DependencyEdgeResponse], summary="List cross-repo dependencies"
)
async def list_dependencies(db: DB) -> list[DependencyEdgeResponse]:
    """List all cross-repository compliance dependencies."""
    from app.services.cross_repo_graph import CrossRepoGraphService

    service = CrossRepoGraphService(db=db)
    deps = await service.list_dependencies(repo_full_name="acme/api")
    return [DependencyEdgeResponse(**_serialize(d)) for d in deps]


@router.get("/hotspots", response_model=list[HotspotResponse], summary="Find compliance hotspots")
async def find_hotspots(db: DB) -> list[HotspotResponse]:
    """Find compliance hotspots across the organization's repositories."""
    from app.services.cross_repo_graph import CrossRepoGraphService

    service = CrossRepoGraphService(db=db)
    hotspots = await service.find_hotspots()
    return [HotspotResponse(**_serialize(h)) for h in hotspots]


@router.get(
    "/shared-violations",
    response_model=list[dict],
    summary="Get shared violations across repos",
)
async def get_shared_violations(db: DB) -> list[dict]:
    """Get compliance violations shared across multiple repositories."""
    from app.services.cross_repo_graph import CrossRepoGraphService

    service = CrossRepoGraphService(db=db)
    violations = await service.get_shared_violations(repo_a="acme/api", repo_b="acme/web")
    return [_serialize(v) for v in violations]


@router.get("/score", response_model=OrgScoreResponse, summary="Get aggregated organization score")
async def get_org_score(db: DB) -> OrgScoreResponse:
    """Get the aggregated compliance score for the organization."""
    from app.services.cross_repo_graph import CrossRepoGraphService

    service = CrossRepoGraphService(db=db)
    score = await service.get_aggregated_score(organization_id="default")
    return OrgScoreResponse(**_serialize(score))
