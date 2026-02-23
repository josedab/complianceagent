"""API endpoints for Multi-Org Orchestrator."""

from uuid import UUID

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.multi_org_orchestrator import MultiOrgOrchestratorService


logger = structlog.get_logger()
router = APIRouter()


class EntityCreateRequest(BaseModel):
    name: str = Field(...)
    parent_id: UUID | None = Field(default=None)
    relation: str = Field(default="subsidiary")
    frameworks: list[str] | None = Field(default=None)


class PolicyPropagateRequest(BaseModel):
    source_id: UUID = Field(...)
    target_id: UUID = Field(...)
    policy_name: str = Field(...)
    inheritance: str = Field(default="inherit")


@router.post("/entities", status_code=status.HTTP_201_CREATED, summary="Create entity")
async def create_entity(request: EntityCreateRequest, db: DB) -> dict:
    """Create a new organization entity."""
    service = MultiOrgOrchestratorService(db=db)
    result = await service.create_entity(
        name=request.name,
        parent_id=request.parent_id,
        relation=request.relation,
        frameworks=request.frameworks,
    )
    return {
        "id": str(result.id),
        "name": result.name,
        "parent_id": str(result.parent_id) if result.parent_id else None,
        "relation": result.relation.value,
        "compliance_score": result.compliance_score,
        "frameworks": result.frameworks,
        "policies": result.policies,
        "created_at": result.created_at.isoformat() if result.created_at else None,
    }


@router.get("/hierarchy/{root_id}", summary="Get hierarchy")
async def get_hierarchy(root_id: UUID, db: DB) -> dict:
    """Get the full hierarchy starting from a root entity."""
    service = MultiOrgOrchestratorService(db=db)
    result = await service.get_hierarchy(root_id=root_id)
    return {
        "root_id": str(result.root_id),
        "entities": [
            {
                "id": str(e.id),
                "name": e.name,
                "parent_id": str(e.parent_id) if e.parent_id else None,
                "relation": e.relation.value,
                "compliance_score": e.compliance_score,
                "frameworks": e.frameworks,
            }
            for e in result.entities
        ],
        "total_entities": result.total_entities,
        "avg_score": result.avg_score,
        "lowest_score": result.lowest_score,
    }


@router.post("/policies/propagate", summary="Propagate policy")
async def propagate_policy(request: PolicyPropagateRequest, db: DB) -> dict:
    """Propagate a policy from one entity to another."""
    service = MultiOrgOrchestratorService(db=db)
    result = await service.propagate_policy(
        source_id=request.source_id,
        target_id=request.target_id,
        policy_name=request.policy_name,
        inheritance=request.inheritance,
    )
    return {
        "source_entity_id": str(result.source_entity_id),
        "target_entity_id": str(result.target_entity_id),
        "policy_name": result.policy_name,
        "inheritance": result.inheritance.value,
        "applied": result.applied,
    }


@router.post("/reports/{root_id}", summary="Generate consolidated report")
async def generate_report(root_id: UUID, db: DB) -> dict:
    """Generate a consolidated compliance report for a hierarchy."""
    service = MultiOrgOrchestratorService(db=db)
    result = await service.generate_consolidated_report(root_id=root_id)
    return {
        "id": str(result.id),
        "hierarchy_name": result.hierarchy_name,
        "entities": result.entities,
        "overall_score": result.overall_score,
        "gaps": result.gaps,
        "recommendations": result.recommendations,
        "generated_at": result.generated_at.isoformat() if result.generated_at else None,
    }


@router.get("/entities", summary="List entities")
async def list_entities(db: DB) -> list[dict]:
    """List all organization entities."""
    service = MultiOrgOrchestratorService(db=db)
    entities = await service.list_entities()
    return [
        {
            "id": str(e.id),
            "name": e.name,
            "parent_id": str(e.parent_id) if e.parent_id else None,
            "relation": e.relation.value,
            "compliance_score": e.compliance_score,
            "frameworks": e.frameworks,
            "policies": e.policies,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entities
    ]


@router.get("/stats", summary="Get stats")
async def get_stats(db: DB) -> dict:
    """Get multi-org orchestrator statistics."""
    service = MultiOrgOrchestratorService(db=db)
    stats = await service.get_stats()
    return {
        "total_entities": stats.total_entities,
        "hierarchies": stats.hierarchies,
        "policies_propagated": stats.policies_propagated,
        "avg_score": stats.avg_score,
        "compliance_gaps": stats.compliance_gaps,
    }
