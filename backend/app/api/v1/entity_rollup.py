"""Multi-Entity Compliance Rollup API endpoints."""

from uuid import UUID

import structlog
from fastapi import APIRouter

from app.api.v1.deps import DB
from app.services.entity_rollup import EntityRollupService


logger = structlog.get_logger()
router = APIRouter()


@router.get("/hierarchy")
async def get_hierarchy(db: DB) -> list[dict]:
    """Get the full organizational entity hierarchy."""
    svc = EntityRollupService(db)
    entities = await svc.get_hierarchy()
    return [
        {
            "id": str(e.id),
            "name": e.name,
            "parent_id": str(e.parent_id) if e.parent_id else None,
            "level": e.level,
            "compliance_score": e.compliance_score,
            "frameworks": e.frameworks,
            "member_count": e.member_count,
        }
        for e in entities
    ]


@router.get("/rollup/{entity_id}")
async def compute_rollup(entity_id: UUID, db: DB) -> dict:
    """Compute aggregated compliance score for an entity and its children."""
    svc = EntityRollupService(db)
    rollup = await svc.compute_rollup(entity_id)
    return {
        "entity_name": rollup.entity_name,
        "own_score": rollup.own_score,
        "aggregated_score": rollup.aggregated_score,
        "child_scores": rollup.child_scores,
        "total_members": rollup.total_members,
        "weakest_area": rollup.weakest_area,
        "computed_at": rollup.computed_at.isoformat() if rollup.computed_at else None,
    }


@router.get("/policies/{entity_id}")
async def resolve_policies(entity_id: UUID, db: DB) -> dict:
    """Resolve effective policies for an entity including inherited ones."""
    svc = EntityRollupService(db)
    result = await svc.resolve_policies(entity_id)
    return {
        "effective_frameworks": result.effective_frameworks,
        "inherited_from": result.inherited_from,
        "overrides": result.overrides,
    }
