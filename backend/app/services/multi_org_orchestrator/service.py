"""Multi-organization orchestrator service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    ConsolidatedReport,
    MultiOrgStats,
    OrgEntity,
    OrgHierarchy,
    OrgRelation,
    PolicyInheritance,
    PolicyPropagation,
)


logger = structlog.get_logger(__name__)


class MultiOrgOrchestratorService:
    """Service for orchestrating compliance across multiple organizations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._entities: list[OrgEntity] = []
        self._propagations: list[PolicyPropagation] = []
        self._reports: list[ConsolidatedReport] = []
        self._seed_entities()

    def _seed_entities(self) -> None:
        """Seed initial organization hierarchy."""
        root_id = uuid.uuid4()
        root = OrgEntity(
            id=root_id,
            name="GlobalCorp Holdings",
            parent_id=None,
            relation=OrgRelation.parent,
            compliance_score=88.0,
            frameworks=["SOC2", "GDPR", "ISO27001"],
            policies=["data-retention", "access-control", "encryption"],
            created_at=datetime.now(UTC),
        )

        sub1_id = uuid.uuid4()
        sub1 = OrgEntity(
            id=sub1_id,
            name="North America Division",
            parent_id=root_id,
            relation=OrgRelation.division,
            compliance_score=91.0,
            frameworks=["SOC2", "HIPAA"],
            policies=["data-retention", "access-control"],
            created_at=datetime.now(UTC),
        )

        sub2_id = uuid.uuid4()
        sub2 = OrgEntity(
            id=sub2_id,
            name="EU Subsidiary",
            parent_id=root_id,
            relation=OrgRelation.subsidiary,
            compliance_score=85.0,
            frameworks=["GDPR", "ISO27001"],
            policies=["data-retention", "privacy-shield"],
            created_at=datetime.now(UTC),
        )

        sub3 = OrgEntity(
            id=uuid.uuid4(),
            name="APAC Joint Venture",
            parent_id=root_id,
            relation=OrgRelation.joint_venture,
            compliance_score=72.0,
            frameworks=["ISO27001"],
            policies=["access-control"],
            created_at=datetime.now(UTC),
        )

        sub4 = OrgEntity(
            id=uuid.uuid4(),
            name="FinTech Acquisition",
            parent_id=sub1_id,
            relation=OrgRelation.acquisition,
            compliance_score=65.0,
            frameworks=["PCI-DSS", "SOC2"],
            policies=["encryption"],
            created_at=datetime.now(UTC),
        )

        self._entities = [root, sub1, sub2, sub3, sub4]

    async def create_entity(
        self,
        name: str,
        parent_id: uuid.UUID | None = None,
        relation: str = "subsidiary",
        frameworks: list[str] | None = None,
    ) -> OrgEntity:
        """Create a new organization entity."""
        entity = OrgEntity(
            id=uuid.uuid4(),
            name=name,
            parent_id=parent_id,
            relation=OrgRelation(relation),
            compliance_score=0.0,
            frameworks=frameworks or [],
            policies=[],
            created_at=datetime.now(UTC),
        )
        self._entities.append(entity)

        await logger.ainfo("entity_created", name=name, relation=relation)
        return entity

    async def get_hierarchy(self, root_id: uuid.UUID) -> OrgHierarchy:
        """Get the full hierarchy starting from a root entity."""
        collected: list[OrgEntity] = []

        def _traverse(parent_id: uuid.UUID) -> None:
            for entity in self._entities:
                if entity.id == parent_id:
                    collected.append(entity)
                if entity.parent_id == parent_id and entity.id != parent_id:
                    collected.append(entity)
                    _traverse(entity.id)

        _traverse(root_id)
        # Deduplicate while preserving order
        seen: set[uuid.UUID] = set()
        unique: list[OrgEntity] = []
        for entity in collected:
            if entity.id not in seen:
                seen.add(entity.id)
                unique.append(entity)

        scores = [e.compliance_score for e in unique] if unique else [0.0]

        return OrgHierarchy(
            root_id=root_id,
            entities=unique,
            total_entities=len(unique),
            avg_score=sum(scores) / len(scores),
            lowest_score=min(scores),
        )

    async def propagate_policy(
        self,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        policy_name: str,
        inheritance: str = "inherit",
    ) -> PolicyPropagation:
        """Propagate a policy from one entity to another."""
        propagation = PolicyPropagation(
            source_entity_id=source_id,
            target_entity_id=target_id,
            policy_name=policy_name,
            inheritance=PolicyInheritance(inheritance),
            applied=True,
        )
        self._propagations.append(propagation)

        # Apply the policy to the target entity
        for entity in self._entities:
            if entity.id == target_id and policy_name not in entity.policies:
                entity.policies.append(policy_name)

        await logger.ainfo(
            "policy_propagated",
            policy=policy_name,
            inheritance=inheritance,
        )
        return propagation

    async def generate_consolidated_report(
        self,
        root_id: uuid.UUID,
    ) -> ConsolidatedReport:
        """Generate a consolidated compliance report for a hierarchy."""
        hierarchy = await self.get_hierarchy(root_id)

        entity_data = [
            {
                "name": e.name,
                "score": e.compliance_score,
                "frameworks": e.frameworks,
            }
            for e in hierarchy.entities
        ]

        gaps: list[dict] = []
        recommendations: list[str] = []

        for entity in hierarchy.entities:
            if entity.compliance_score < 80.0:
                gaps.append(
                    {
                        "entity": entity.name,
                        "score": entity.compliance_score,
                        "missing_frameworks": [
                            f
                            for f in ["SOC2", "GDPR", "ISO27001"]
                            if f not in entity.frameworks
                        ],
                    }
                )
                recommendations.append(
                    f"Improve compliance for {entity.name} "
                    f"(current score: {entity.compliance_score}%)"
                )

        report = ConsolidatedReport(
            id=uuid.uuid4(),
            hierarchy_name=hierarchy.entities[0].name
            if hierarchy.entities
            else "Unknown",
            entities=entity_data,
            overall_score=hierarchy.avg_score,
            gaps=gaps,
            recommendations=recommendations,
            generated_at=datetime.now(UTC),
        )
        self._reports.append(report)

        await logger.ainfo(
            "consolidated_report_generated",
            entities=hierarchy.total_entities,
            overall_score=hierarchy.avg_score,
        )
        return report

    async def list_entities(self) -> list[OrgEntity]:
        """List all organization entities."""
        return list(self._entities)

    async def get_stats(self) -> MultiOrgStats:
        """Get aggregate multi-org statistics."""
        scores = [e.compliance_score for e in self._entities]
        avg = sum(scores) / len(scores) if scores else 0.0

        root_ids = {
            e.id for e in self._entities if e.parent_id is None
        }
        gap_count = sum(
            1 for e in self._entities if e.compliance_score < 80.0
        )

        return MultiOrgStats(
            total_entities=len(self._entities),
            hierarchies=len(root_ids),
            policies_propagated=len(self._propagations),
            avg_score=avg,
            compliance_gaps=gap_count,
        )
