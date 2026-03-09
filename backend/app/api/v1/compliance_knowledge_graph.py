"""Compliance Knowledge Graph API endpoints."""

from uuid import UUID

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.compliance_knowledge_graph import ComplianceKnowledgeGraphService


logger = structlog.get_logger()
router = APIRouter()


class GraphQueryRequest(BaseModel):
    query: str


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., description="Natural language search query")
    top_k: int = Field(default=10, description="Number of results to return")
    similarity_threshold: float = Field(default=0.3, description="Minimum similarity score")
    node_types: list[str] = Field(default_factory=list, description="Filter by node types")


@router.post("/query")
async def query_graph(request: GraphQueryRequest, db: DB) -> dict:
    """Natural language query over the compliance knowledge graph."""
    svc = ComplianceKnowledgeGraphService(db)
    result = await svc.query(request.query)
    return {
        "query": result.query,
        "interpretation": result.interpretation,
        "total_nodes": result.total_nodes,
        "total_edges": result.total_edges,
        "nodes": [
            {
                "id": str(n.id),
                "type": n.node_type.value,
                "label": n.label,
                "properties": n.properties,
            }
            for n in result.nodes
        ],
        "edges": [
            {"source": str(e.source_id), "target": str(e.target_id), "type": e.edge_type.value}
            for e in result.edges
        ],
    }


@router.post("/semantic-search")
async def semantic_search(request: SemanticSearchRequest, db: DB) -> dict:
    """Search the knowledge graph using pgvector cosine similarity."""
    from app.services.knowledge_graph import KnowledgeGraphService
    from app.services.knowledge_graph.models import NodeType

    kg_svc = KnowledgeGraphService(db)
    # Build graph if not already built
    graphs = list(kg_svc._graphs.values())
    if not graphs:
        return {"results": [], "message": "No graph built yet. Build a graph first via the knowledge graph service."}

    graph = graphs[0]
    node_types = [NodeType(nt) for nt in request.node_types] if request.node_types else None
    results = await kg_svc.semantic_search(
        graph_id=graph.id,
        query_text=request.query,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
        node_types=node_types,
    )
    return {
        "query": request.query,
        "total_results": len(results),
        "results": [
            {
                "node_id": str(r.node.id) if r.node else None,
                "node_name": r.node.name if r.node else "",
                "node_type": r.node.node_type.value if r.node else "",
                "similarity": round(r.similarity, 4),
                "matched_text": r.matched_text[:200],
            }
            for r in results
        ],
    }


@router.get("/query-templates")
async def get_query_templates(db: DB) -> dict:
    """Get available query templates for common compliance queries."""
    from app.services.knowledge_graph import KnowledgeGraphService

    kg_svc = KnowledgeGraphService(db)
    templates = await kg_svc.get_query_templates()
    return {"templates": {k: {"description": v["description"]} for k, v in templates.items()}}


@router.get("/stats")
async def get_graph_stats(db: DB) -> dict:
    """Get knowledge graph statistics."""
    svc = ComplianceKnowledgeGraphService(db)
    stats = await svc.get_stats()
    return {
        "total_nodes": stats.total_nodes,
        "total_edges": stats.total_edges,
        "nodes_by_type": stats.nodes_by_type,
        "edges_by_type": stats.edges_by_type,
        "frameworks_covered": stats.frameworks_covered,
    }


@router.get("/node/{node_id}/neighbors")
async def get_node_neighbors(node_id: UUID, db: DB) -> dict:
    """Get all nodes connected to a given node."""
    svc = ComplianceKnowledgeGraphService(db)
    result = await svc.get_neighbors(node_id)
    return {
        "total_nodes": result.total_nodes,
        "total_edges": result.total_edges,
        "nodes": [
            {"id": str(n.id), "type": n.node_type.value, "label": n.label} for n in result.nodes
        ],
        "edges": [
            {"source": str(e.source_id), "target": str(e.target_id), "type": e.edge_type.value}
            for e in result.edges
        ],
    }
