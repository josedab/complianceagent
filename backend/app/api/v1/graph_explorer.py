"""API endpoints for Graph Explorer."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.graph_explorer import GraphExplorerService


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class CreateViewRequest(BaseModel):
    mode: str = Field(..., description="Visualization mode")
    filters: dict[str, Any] = Field(default_factory=dict, description="Filter criteria")


class NodeSchema(BaseModel):
    id: str
    label: str
    node_type: str
    properties: dict[str, Any]
    connections: int


class EdgeSchema(BaseModel):
    source: str
    target: str
    relationship: str
    weight: float


class GraphViewSchema(BaseModel):
    id: str
    mode: str
    filters: dict[str, Any]
    nodes: list[NodeSchema]
    edges: list[EdgeSchema]
    created_at: str | None


class DrilldownSchema(BaseModel):
    node: NodeSchema
    neighbors: list[NodeSchema]
    edges: list[EdgeSchema]
    depth: int


class GraphStatsSchema(BaseModel):
    total_nodes: int
    total_edges: int
    total_views: int
    node_types: dict[str, int]


# --- Endpoints ---


@router.post("/views", response_model=GraphViewSchema, status_code=status.HTTP_201_CREATED, summary="Create graph view")
async def create_view(request: CreateViewRequest, db: DB) -> GraphViewSchema:
    service = GraphExplorerService(db=db)
    view = await service.create_view(mode=request.mode, filters=request.filters)
    logger.info("graph_view_created", mode=request.mode)
    return GraphViewSchema(
        id=str(view.id), mode=view.mode, filters=view.filters,
        nodes=[
            NodeSchema(id=str(n.id), label=n.label, node_type=n.node_type, properties=n.properties, connections=n.connections)
            for n in view.nodes
        ],
        edges=[
            EdgeSchema(source=e.source, target=e.target, relationship=e.relationship, weight=e.weight)
            for e in view.edges
        ],
        created_at=view.created_at.isoformat() if view.created_at else None,
    )


@router.get("/views/{view_id}/drilldown/{node_id}", response_model=DrilldownSchema, summary="Drilldown into node")
async def drilldown(view_id: str, node_id: str, db: DB) -> DrilldownSchema:
    service = GraphExplorerService(db=db)
    result = await service.drilldown(view_id=view_id, node_id=node_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="View or node not found")
    return DrilldownSchema(
        node=NodeSchema(
            id=str(result.node.id), label=result.node.label, node_type=result.node.node_type,
            properties=result.node.properties, connections=result.node.connections,
        ),
        neighbors=[
            NodeSchema(id=str(n.id), label=n.label, node_type=n.node_type, properties=n.properties, connections=n.connections)
            for n in result.neighbors
        ],
        edges=[
            EdgeSchema(source=e.source, target=e.target, relationship=e.relationship, weight=e.weight)
            for e in result.edges
        ],
        depth=result.depth,
    )


@router.get("/search", response_model=list[NodeSchema], summary="Search graph nodes")
async def search_nodes(db: DB, query: str = Query(..., description="Search query")) -> list[NodeSchema]:
    service = GraphExplorerService(db=db)
    nodes = await service.search_nodes(query=query)
    return [
        NodeSchema(
            id=str(n.id), label=n.label, node_type=n.node_type,
            properties=n.properties, connections=n.connections,
        )
        for n in nodes
    ]


@router.get("/stats", response_model=GraphStatsSchema, summary="Get graph stats")
async def get_stats(db: DB) -> GraphStatsSchema:
    service = GraphExplorerService(db=db)
    s = await service.get_stats()
    return GraphStatsSchema(
        total_nodes=s.total_nodes,
        total_edges=s.total_edges,
        total_views=s.total_views,
        node_types=s.node_types,
    )
