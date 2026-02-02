"""Knowledge graph explorer API endpoints."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep, CurrentOrganization, OrgMember
from app.services.knowledge_graph import (
    KnowledgeGraphService,
    NodeType,
    RelationType,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---

class BuildGraphRequest(BaseModel):
    """Request to build a knowledge graph."""
    name: str = "Compliance Knowledge Graph"
    include_regulations: bool = True
    include_code: bool = True
    include_vendors: bool = True


class GraphNodeSchema(BaseModel):
    """Node in the graph."""
    id: str
    type: str
    name: str
    description: str
    group: str
    x: float
    y: float
    size: float
    color: str
    properties: dict = Field(default_factory=dict)


class GraphEdgeSchema(BaseModel):
    """Edge in the graph."""
    id: str
    source: str
    target: str
    type: str
    weight: float


class GraphSummarySchema(BaseModel):
    """Summary of a knowledge graph."""
    id: UUID
    name: str
    node_count: int
    edge_count: int
    node_types: dict[str, int]


class GraphVisualizationSchema(BaseModel):
    """Graph data for visualization."""
    nodes: list[GraphNodeSchema] = Field(default_factory=list)
    edges: list[GraphEdgeSchema] = Field(default_factory=list)
    statistics: dict = Field(default_factory=dict)


class QueryRequest(BaseModel):
    """Request to query the graph."""
    natural_query: str = ""
    node_types: list[str] = Field(default_factory=list)
    relation_types: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    max_depth: int = 3
    max_results: int = 100
    start_node_ids: list[str] = Field(default_factory=list)


class QueryResultSchema(BaseModel):
    """Query result response."""
    query_id: str
    natural_answer: str
    total_nodes: int
    total_edges: int
    execution_time_ms: float
    nodes: list[GraphNodeSchema] = Field(default_factory=list)
    edges: list[GraphEdgeSchema] = Field(default_factory=list)


class PathRequest(BaseModel):
    """Request to find path between nodes."""
    source_id: str
    target_id: str
    max_depth: int = 5


class NodeDetailsSchema(BaseModel):
    """Detailed node information."""
    node: GraphNodeSchema
    neighbors: list[GraphNodeSchema] = Field(default_factory=list)
    edges: list[GraphEdgeSchema] = Field(default_factory=list)
    neighbor_count: int


# --- Helper Functions ---

def _node_to_schema(node) -> GraphNodeSchema:
    """Convert GraphNode to schema."""
    return GraphNodeSchema(
        id=str(node.id),
        type=node.node_type.value,
        name=node.name,
        description=node.description,
        group=node.group,
        x=node.x,
        y=node.y,
        size=node.size,
        color=node.color,
        properties=node.properties,
    )


def _edge_to_schema(edge) -> GraphEdgeSchema:
    """Convert GraphEdge to schema."""
    return GraphEdgeSchema(
        id=str(edge.id),
        source=str(edge.source_id),
        target=str(edge.target_id),
        type=edge.relation_type.value,
        weight=edge.weight,
    )


# --- Endpoints ---

@router.post(
    "/build",
    response_model=GraphSummarySchema,
    summary="Build knowledge graph",
    description="Build a compliance knowledge graph from organizational data",
)
async def build_knowledge_graph(
    request: BuildGraphRequest,
    organization: CurrentOrganization,
    db: DB,
    copilot: CopilotDep,
) -> GraphSummarySchema:
    """Build a new knowledge graph."""
    service = KnowledgeGraphService(db=db, copilot=copilot)
    
    graph = await service.build_graph(
        organization_id=organization.id,
        name=request.name,
        include_regulations=request.include_regulations,
        include_code=request.include_code,
        include_vendors=request.include_vendors,
    )
    
    return GraphSummarySchema(
        id=graph.id,
        name=graph.name,
        node_count=graph.node_count,
        edge_count=graph.edge_count,
        node_types={
            nt.value: len(nodes)
            for nt, nodes in graph.nodes_by_type.items()
        },
    )


@router.get(
    "/{graph_id}",
    response_model=GraphVisualizationSchema,
    summary="Get graph visualization",
    description="Get graph data formatted for visualization",
)
async def get_graph_visualization(
    graph_id: UUID,
    organization: CurrentOrganization,
    db: DB,
    copilot: CopilotDep,
) -> GraphVisualizationSchema:
    """Get graph visualization data."""
    service = KnowledgeGraphService(db=db, copilot=copilot)
    
    try:
        data = await service.export_for_visualization(graph_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Graph not found",
        )
    
    return GraphVisualizationSchema(
        nodes=[
            GraphNodeSchema(
                id=n["id"],
                type=n["type"],
                name=n["label"],
                description="",
                group=n["group"],
                x=n["x"],
                y=n["y"],
                size=n["size"],
                color=n["color"],
                properties=n["properties"],
            )
            for n in data["nodes"]
        ],
        edges=[
            GraphEdgeSchema(
                id=e["id"],
                source=e["source"],
                target=e["target"],
                type=e["type"],
                weight=e["weight"],
            )
            for e in data["edges"]
        ],
        statistics=data["statistics"],
    )


@router.post(
    "/{graph_id}/query",
    response_model=QueryResultSchema,
    summary="Query knowledge graph",
    description="Query the graph using natural language or structured filters",
)
async def query_graph(
    graph_id: UUID,
    request: QueryRequest,
    organization: CurrentOrganization,
    db: DB,
    copilot: CopilotDep,
) -> QueryResultSchema:
    """Query the knowledge graph."""
    service = KnowledgeGraphService(db=db, copilot=copilot)
    
    from app.services.knowledge_graph.models import GraphQuery
    
    query = GraphQuery(
        natural_query=request.natural_query,
        node_types=[NodeType(t) for t in request.node_types if t],
        relation_types=[RelationType(t) for t in request.relation_types if t],
        keywords=request.keywords,
        max_depth=request.max_depth,
        max_results=request.max_results,
        start_nodes=[UUID(nid) for nid in request.start_node_ids if nid],
    )
    
    try:
        result = await service.query(graph_id, query)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    
    return QueryResultSchema(
        query_id=str(result.query_id),
        natural_answer=result.natural_answer,
        total_nodes=result.total_nodes,
        total_edges=result.total_edges,
        execution_time_ms=result.execution_time_ms,
        nodes=[_node_to_schema(n) for n in result.nodes],
        edges=[_edge_to_schema(e) for e in result.edges],
    )


@router.get(
    "/{graph_id}/nodes/{node_id}",
    response_model=NodeDetailsSchema,
    summary="Get node details",
    description="Get detailed information about a specific node",
)
async def get_node_details(
    graph_id: UUID,
    node_id: UUID,
    organization: CurrentOrganization,
    db: DB,
    copilot: CopilotDep,
) -> NodeDetailsSchema:
    """Get node details with neighbors."""
    service = KnowledgeGraphService(db=db, copilot=copilot)
    
    details = await service.get_node_details(graph_id, node_id)
    
    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )
    
    return NodeDetailsSchema(
        node=_node_to_schema(details["node"]),
        neighbors=[_node_to_schema(n) for n in details["neighbors"]],
        edges=[_edge_to_schema(e) for e in details["edges"]],
        neighbor_count=details["neighbor_count"],
    )


@router.post(
    "/{graph_id}/path",
    summary="Find path between nodes",
    description="Find paths connecting two nodes in the graph",
)
async def find_path(
    graph_id: UUID,
    request: PathRequest,
    organization: CurrentOrganization,
    db: DB,
    copilot: CopilotDep,
) -> dict:
    """Find paths between nodes."""
    service = KnowledgeGraphService(db=db, copilot=copilot)
    
    paths = await service.find_path(
        graph_id=graph_id,
        source_id=UUID(request.source_id),
        target_id=UUID(request.target_id),
        max_depth=request.max_depth,
    )
    
    return {
        "paths": [[str(nid) for nid in path] for path in paths],
        "path_count": len(paths),
    }


@router.get(
    "/templates",
    summary="Get query templates",
    description="Get pre-defined query templates",
)
async def get_query_templates(
    db: DB,
    copilot: CopilotDep,
) -> dict:
    """Get available query templates."""
    service = KnowledgeGraphService(db=db, copilot=copilot)
    templates = await service.get_query_templates()
    return {"templates": templates}


@router.get(
    "/node-types",
    summary="Get node types",
    description="Get available node types for filtering",
)
async def get_node_types() -> dict:
    """Get available node types."""
    return {
        "node_types": [
            {"value": nt.value, "name": nt.value.replace("_", " ").title()}
            for nt in NodeType
        ]
    }


@router.get(
    "/relation-types",
    summary="Get relation types",
    description="Get available relationship types",
)
async def get_relation_types() -> dict:
    """Get available relation types."""
    return {
        "relation_types": [
            {"value": rt.value, "name": rt.value.replace("_", " ").title()}
            for rt in RelationType
        ]
    }
