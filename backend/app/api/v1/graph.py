"""Knowledge Graph API endpoints."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.v1.deps import DB, CurrentOrganization, OrgMember


router = APIRouter()


class GraphNodeResponse(BaseModel):
    """A node in the compliance graph."""

    id: str
    type: str
    name: str
    properties: dict[str, Any]


class GraphEdgeResponse(BaseModel):
    """An edge in the compliance graph."""

    id: str
    type: str
    source: str
    target: str
    weight: float


class GraphQueryResponse(BaseModel):
    """Response from graph query."""

    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]
    summary: str


@router.get("/export")
async def export_knowledge_graph(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Export the compliance knowledge graph for visualization."""
    from app.services.graph import get_knowledge_graph

    graph = get_knowledge_graph()
    return graph.export_for_visualization()


@router.get("/query", response_model=GraphQueryResponse)
async def query_knowledge_graph(
    query: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> GraphQueryResponse:
    """Query the knowledge graph using natural language."""
    from app.services.graph import get_knowledge_graph

    graph = get_knowledge_graph()
    result = graph.query_natural_language(query)

    return GraphQueryResponse(
        nodes=[
            GraphNodeResponse(
                id=str(n.id),
                type=n.type.value,
                name=n.name,
                properties=n.properties,
            )
            for n in result.get("nodes", [])
        ],
        edges=[
            GraphEdgeResponse(
                id=str(e.id),
                type=e.type.value,
                source=str(e.source_id),
                target=str(e.target_id),
                weight=e.weight,
            )
            for e in result.get("edges", [])
        ],
        summary=result.get("summary", ""),
    )


@router.get("/coverage/{regulation}")
async def get_compliance_coverage(
    regulation: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> dict[str, Any]:
    """Get compliance coverage for a regulation."""
    from app.services.graph import get_knowledge_graph

    graph = get_knowledge_graph()
    return graph.get_compliance_coverage(regulation)
