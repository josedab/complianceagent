"""API endpoints for Compliance Graph Neural Network."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.compliance_gnn import ComplianceGNNService


logger = structlog.get_logger()
router = APIRouter()


class PredictRequest(BaseModel):
    repo: str = Field(...)
    framework: str = Field(default="")
    include_neighbors: bool = Field(default=True)
    threshold: float = Field(default=0.5)


class PredictionSchema(BaseModel):
    id: str
    repo: str
    framework: str
    risk_score: float
    predicted_violations: list[dict[str, Any]]
    contributing_factors: list[str]
    confidence: float
    model_version: str


class GraphNodeSchema(BaseModel):
    id: str
    node_type: str
    label: str
    properties: dict[str, Any]
    edges_count: int


class GraphSchema(BaseModel):
    total_nodes: int
    total_edges: int
    node_types: dict[str, int]
    edge_types: dict[str, int]


class NeighborSchema(BaseModel):
    node: GraphNodeSchema
    edge_type: str
    weight: float


class GNNStatsSchema(BaseModel):
    total_predictions: int
    total_nodes: int
    total_edges: int
    model_version: str
    accuracy: float
    by_framework: dict[str, int]


@router.post("/predict", response_model=PredictionSchema, summary="Predict violations")
async def predict(request: PredictRequest, db: DB) -> PredictionSchema:
    service = ComplianceGNNService(db=db)
    p = await service.predict(
        repo=request.repo, framework=request.framework,
        include_neighbors=request.include_neighbors, threshold=request.threshold,
    )
    return PredictionSchema(
        id=str(p.id), repo=p.repo, framework=p.framework, risk_score=p.risk_score,
        predicted_violations=p.predicted_violations, contributing_factors=p.contributing_factors,
        confidence=p.confidence, model_version=p.model_version,
    )


@router.get("/graph", response_model=GraphSchema, summary="Get graph overview")
async def get_graph(db: DB) -> GraphSchema:
    service = ComplianceGNNService(db=db)
    g = service.get_graph()
    return GraphSchema(
        total_nodes=g.total_nodes, total_edges=g.total_edges,
        node_types=g.node_types, edge_types=g.edge_types,
    )


@router.get("/graph/{node_id}/neighbors", response_model=list[NeighborSchema], summary="Get node neighbors")
async def get_neighbors(node_id: str, db: DB, edge_type: str | None = None, limit: int = 20) -> list[NeighborSchema]:
    service = ComplianceGNNService(db=db)
    neighbors = service.get_neighbors(node_id=node_id, edge_type=edge_type, limit=limit)
    if neighbors is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    return [
        NeighborSchema(
            node=GraphNodeSchema(
                id=str(n.node.id), node_type=n.node.node_type, label=n.node.label,
                properties=n.node.properties, edges_count=n.node.edges_count,
            ),
            edge_type=n.edge_type,
            weight=n.weight,
        )
        for n in neighbors
    ]


@router.get("/stats", response_model=GNNStatsSchema, summary="Get GNN stats")
async def get_stats(db: DB) -> GNNStatsSchema:
    service = ComplianceGNNService(db=db)
    s = service.get_stats()
    return GNNStatsSchema(
        total_predictions=s.total_predictions, total_nodes=s.total_nodes,
        total_edges=s.total_edges, model_version=s.model_version,
        accuracy=s.accuracy, by_framework=s.by_framework,
    )
