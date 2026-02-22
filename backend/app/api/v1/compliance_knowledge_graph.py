"""Compliance Knowledge Graph API endpoints."""

from uuid import UUID

import structlog
from fastapi import APIRouter
from pydantic import BaseModel

from app.api.v1.deps import DB
from app.services.compliance_knowledge_graph import ComplianceKnowledgeGraphService


logger = structlog.get_logger()
router = APIRouter()


class GraphQueryRequest(BaseModel):
    query: str


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
