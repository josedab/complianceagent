"""API endpoints for Data Mesh Federation."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.data_mesh_federation import DataMeshFederationService


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class JoinFederationRequest(BaseModel):
    org_name: str = Field(..., description="Organization name")
    endpoint_url: str = Field(..., description="Endpoint URL for the node")
    role: str = Field(..., description="Role of the node in the federation")


class ShareInsightRequest(BaseModel):
    node_id: str = Field(..., description="Source node identifier")
    insight_type: str = Field(..., description="Type of insight being shared")
    data: dict[str, Any] = Field(..., description="Insight data payload")
    proof_type: str = Field(default="hash", description="Verification proof type")


class NodeSchema(BaseModel):
    id: str
    org_name: str
    endpoint_url: str
    role: str
    status: str
    joined_at: str | None


class InsightSchema(BaseModel):
    id: str
    node_id: str
    insight_type: str
    data: dict[str, Any]
    proof_type: str
    verified: bool
    created_at: str | None


class FederationStatsSchema(BaseModel):
    total_nodes: int
    total_insights: int
    verified_insights: int
    active_nodes: int


# --- Endpoints ---


@router.post("/nodes", response_model=NodeSchema, status_code=status.HTTP_201_CREATED, summary="Join federation")
async def join_federation(request: JoinFederationRequest, db: DB) -> NodeSchema:
    service = DataMeshFederationService(db=db)
    node = await service.join_federation(
        org_name=request.org_name,
        endpoint_url=request.endpoint_url,
        role=request.role,
    )
    logger.info("node_joined_federation", org_name=request.org_name, role=request.role)
    return NodeSchema(
        id=str(node.id), org_name=node.org_name, endpoint_url=node.endpoint_url,
        role=node.role, status=node.status,
        joined_at=node.joined_at.isoformat() if node.joined_at else None,
    )


@router.get("/nodes", response_model=list[NodeSchema], summary="List federation nodes")
async def list_nodes(db: DB) -> list[NodeSchema]:
    service = DataMeshFederationService(db=db)
    nodes = await service.list_nodes()
    return [
        NodeSchema(
            id=str(n.id), org_name=n.org_name, endpoint_url=n.endpoint_url,
            role=n.role, status=n.status,
            joined_at=n.joined_at.isoformat() if n.joined_at else None,
        )
        for n in nodes
    ]


@router.post("/insights", response_model=InsightSchema, status_code=status.HTTP_201_CREATED, summary="Share insight")
async def share_insight(request: ShareInsightRequest, db: DB) -> InsightSchema:
    service = DataMeshFederationService(db=db)
    insight = await service.share_insight(
        node_id=request.node_id,
        insight_type=request.insight_type,
        data=request.data,
        proof_type=request.proof_type,
    )
    logger.info("insight_shared", node_id=request.node_id, insight_type=request.insight_type)
    return InsightSchema(
        id=str(insight.id), node_id=insight.node_id, insight_type=insight.insight_type,
        data=insight.data, proof_type=insight.proof_type, verified=insight.verified,
        created_at=insight.created_at.isoformat() if insight.created_at else None,
    )


@router.get("/insights", response_model=list[InsightSchema], summary="Get network insights")
async def get_network_insights(db: DB) -> list[InsightSchema]:
    service = DataMeshFederationService(db=db)
    insights = await service.get_network_insights()
    return [
        InsightSchema(
            id=str(i.id), node_id=i.node_id, insight_type=i.insight_type,
            data=i.data, proof_type=i.proof_type, verified=i.verified,
            created_at=i.created_at.isoformat() if i.created_at else None,
        )
        for i in insights
    ]


@router.post("/insights/{insight_id}/verify", summary="Verify insight proof")
async def verify_proof(insight_id: str, db: DB) -> dict:
    service = DataMeshFederationService(db=db)
    result = await service.verify_proof(insight_id=insight_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
    logger.info("insight_verified", insight_id=insight_id)
    return {"insight_id": insight_id, "verified": True}


@router.delete("/nodes/{node_id}", summary="Leave federation")
async def leave_federation(node_id: str, db: DB) -> dict:
    service = DataMeshFederationService(db=db)
    ok = await service.leave_federation(node_id=node_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    logger.info("node_left_federation", node_id=node_id)
    return {"status": "removed", "node_id": node_id}


@router.get("/stats", response_model=FederationStatsSchema, summary="Get federation stats")
async def get_stats(db: DB) -> FederationStatsSchema:
    service = DataMeshFederationService(db=db)
    s = await service.get_stats()
    return FederationStatsSchema(
        total_nodes=s.total_nodes,
        total_insights=s.total_insights,
        verified_insights=s.verified_insights,
        active_nodes=s.active_nodes,
    )
