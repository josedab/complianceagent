"""Multi-Entity Compliance Rollup service.

Extends org_hierarchy with policy inheritance and aggregated compliance
scoring across parent → subsidiary → team hierarchies.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession


logger = structlog.get_logger()


class PolicyMode(str, Enum):
    INHERIT = "inherit"
    OVERRIDE = "override"
    MERGE = "merge"


@dataclass
class EntityNode:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    parent_id: UUID | None = None
    level: int = 0  # 0=root, 1=business_unit, 2=department, 3=team, 4=project
    policy_mode: PolicyMode = PolicyMode.INHERIT
    compliance_score: float = 0.0
    frameworks: list[str] = field(default_factory=list)
    member_count: int = 0
    children_ids: list[UUID] = field(default_factory=list)


@dataclass
class RollupScore:
    entity_id: UUID | None = None
    entity_name: str = ""
    own_score: float = 0.0
    aggregated_score: float = 0.0
    child_scores: list[dict[str, Any]] = field(default_factory=list)
    total_members: int = 0
    weakest_area: str = ""
    computed_at: datetime | None = None


@dataclass
class PolicyInheritanceResult:
    entity_id: UUID | None = None
    effective_frameworks: list[str] = field(default_factory=list)
    effective_policies: dict[str, Any] = field(default_factory=dict)
    inherited_from: list[str] = field(default_factory=list)
    overrides: list[str] = field(default_factory=list)


class EntityRollupService:
    """Aggregated compliance scoring across organizational hierarchy."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._entities: dict[UUID, EntityNode] = {}
        self._init_demo_hierarchy()

    def _init_demo_hierarchy(self) -> None:
        root = EntityNode(name="Acme Corp", level=0, compliance_score=85.0, frameworks=["GDPR", "SOC 2", "HIPAA"], member_count=500)
        eng = EntityNode(name="Engineering", parent_id=root.id, level=1, compliance_score=88.0, frameworks=["GDPR", "SOC 2"], member_count=200)
        finance = EntityNode(name="Finance", parent_id=root.id, level=1, compliance_score=82.0, frameworks=["SOX", "PCI-DSS"], member_count=50)
        platform = EntityNode(name="Platform Team", parent_id=eng.id, level=2, compliance_score=92.0, frameworks=["GDPR", "SOC 2"], member_count=30)
        data = EntityNode(name="Data Team", parent_id=eng.id, level=2, compliance_score=78.0, frameworks=["GDPR", "HIPAA"], member_count=15)

        root.children_ids = [eng.id, finance.id]
        eng.children_ids = [platform.id, data.id]

        for e in [root, eng, finance, platform, data]:
            self._entities[e.id] = e

    async def get_hierarchy(self) -> list[EntityNode]:
        """Get the full organizational hierarchy."""
        return list(self._entities.values())

    async def get_entity(self, entity_id: UUID) -> EntityNode | None:
        return self._entities.get(entity_id)

    async def compute_rollup(self, entity_id: UUID) -> RollupScore:
        """Compute aggregated compliance score for an entity including all children."""
        entity = self._entities.get(entity_id)
        if not entity:
            return RollupScore(entity_id=entity_id)

        child_scores: list[dict[str, Any]] = []
        total_members = entity.member_count
        weighted_sum = entity.compliance_score * entity.member_count
        weakest = entity.name
        weakest_score = entity.compliance_score

        for child_id in entity.children_ids:
            child = self._entities.get(child_id)
            if child:
                child_rollup = await self.compute_rollup(child_id)
                child_scores.append({
                    "id": str(child.id),
                    "name": child.name,
                    "score": child.compliance_score,
                    "aggregated": child_rollup.aggregated_score,
                    "members": child_rollup.total_members,
                })
                total_members += child_rollup.total_members
                weighted_sum += child_rollup.aggregated_score * child_rollup.total_members
                if child_rollup.aggregated_score < weakest_score:
                    weakest_score = child_rollup.aggregated_score
                    weakest = child.name

        aggregated = round(weighted_sum / total_members, 1) if total_members > 0 else 0.0

        return RollupScore(
            entity_id=entity_id,
            entity_name=entity.name,
            own_score=entity.compliance_score,
            aggregated_score=aggregated,
            child_scores=child_scores,
            total_members=total_members,
            weakest_area=weakest,
            computed_at=datetime.now(UTC),
        )

    async def resolve_policies(self, entity_id: UUID) -> PolicyInheritanceResult:
        """Resolve effective policies for an entity including inherited ones."""
        entity = self._entities.get(entity_id)
        if not entity:
            return PolicyInheritanceResult(entity_id=entity_id)

        effective_frameworks: list[str] = list(entity.frameworks)
        inherited_from: list[str] = []
        overrides: list[str] = []

        # Walk up the hierarchy
        current = entity
        while current.parent_id:
            parent = self._entities.get(current.parent_id)
            if not parent:
                break
            if current.policy_mode == PolicyMode.INHERIT:
                for fw in parent.frameworks:
                    if fw not in effective_frameworks:
                        effective_frameworks.append(fw)
                        inherited_from.append(f"{fw} (from {parent.name})")
            elif current.policy_mode == PolicyMode.OVERRIDE:
                overrides.append(f"{current.name} overrides {parent.name}")
            elif current.policy_mode == PolicyMode.MERGE:
                for fw in parent.frameworks:
                    if fw not in effective_frameworks:
                        effective_frameworks.append(fw)
                        inherited_from.append(f"{fw} (merged from {parent.name})")
            current = parent

        return PolicyInheritanceResult(
            entity_id=entity_id,
            effective_frameworks=effective_frameworks,
            inherited_from=inherited_from,
            overrides=overrides,
        )
