"""Data Mesh Federation Service."""

import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.data_mesh_federation.models import (
    DataSharingPolicy,
    FederationNetwork,
    FederationNode,
    FederationRole,
    FederationStats,
    ProofType,
    SharedInsight,
)


logger = structlog.get_logger()


class DataMeshFederationService:
    """Service for managing cross-organization data mesh federation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._network = FederationNetwork(
            name="Compliance Federation Network",
            description="Cross-organization compliance insight sharing",
            created_at=datetime.now(UTC),
        )
        self._insights: list[SharedInsight] = []
        self._proof_verifications: int = 0
        self._seed_nodes()

    def _seed_nodes(self) -> None:
        """Seed initial federation nodes."""
        seed_data = [
            ("Acme Corp", FederationRole.COORDINATOR, "https://acme.example.com/federation"),
            ("Globex Inc", FederationRole.PARTICIPANT, "https://globex.example.com/federation"),
            ("Initech LLC", FederationRole.PARTICIPANT, "https://initech.example.com/federation"),
            ("Umbrella Co", FederationRole.OBSERVER, "https://umbrella.example.com/federation"),
        ]
        for org_name, role, endpoint_url in seed_data:
            node = FederationNode(
                org_name=org_name,
                role=role,
                endpoint_url=endpoint_url,
                public_key=hashlib.sha256(org_name.encode()).hexdigest()[:64],
                data_policies=[DataSharingPolicy.SELECTIVE],
                joined_at=datetime.now(UTC),
            )
            self._network.nodes.append(node)

    async def join_federation(
        self,
        org_name: str,
        endpoint_url: str,
        role: str = "participant",
    ) -> FederationNode:
        """Add a new node to the federation network."""
        node = FederationNode(
            org_name=org_name,
            role=FederationRole(role),
            endpoint_url=endpoint_url,
            public_key=hashlib.sha256(org_name.encode()).hexdigest()[:64],
            data_policies=[DataSharingPolicy.SELECTIVE],
            joined_at=datetime.now(UTC),
        )
        self._network.nodes.append(node)
        logger.info("Node joined federation", org_name=org_name, role=role)
        return node

    async def share_insight(
        self,
        node_id: UUID,
        insight_type: str,
        data: dict,
        proof_type: str = "zero_knowledge",
    ) -> SharedInsight:
        """Share a compliance insight with the federation."""
        proof_payload = json.dumps(data, sort_keys=True, default=str)
        proof_hash = hashlib.sha256(proof_payload.encode()).hexdigest()

        insight = SharedInsight(
            source_node_id=node_id,
            insight_type=insight_type,
            data=data,
            proof_type=ProofType(proof_type),
            proof_hash=proof_hash,
            contributed_at=datetime.now(UTC),
        )
        self._insights.append(insight)
        self._network.insights_shared += 1
        logger.info(
            "Insight shared",
            insight_type=insight_type,
            proof_type=proof_type,
            node_id=str(node_id),
        )
        return insight

    async def get_network_insights(
        self,
        insight_type: str | None = None,
        limit: int = 50,
    ) -> list[SharedInsight]:
        """Retrieve insights shared across the federation."""
        results = self._insights
        if insight_type:
            results = [i for i in results if i.insight_type == insight_type]
        return results[:limit]

    async def verify_proof(self, insight_id: UUID) -> bool:
        """Verify the cryptographic proof of a shared insight."""
        insight = next((i for i in self._insights if i.id == insight_id), None)
        if not insight:
            logger.warning("Insight not found for verification", insight_id=str(insight_id))
            return False

        proof_payload = json.dumps(insight.data, sort_keys=True, default=str)
        expected_hash = hashlib.sha256(proof_payload.encode()).hexdigest()
        verified = insight.proof_hash == expected_hash
        self._proof_verifications += 1
        logger.info(
            "Proof verified",
            insight_id=str(insight_id),
            verified=verified,
        )
        return verified

    async def list_nodes(self, role: str | None = None) -> list[FederationNode]:
        """List federation nodes, optionally filtered by role."""
        nodes = self._network.nodes
        if role:
            nodes = [n for n in nodes if n.role == FederationRole(role)]
        return nodes

    async def leave_federation(self, node_id: UUID) -> bool:
        """Remove a node from the federation."""
        original_count = len(self._network.nodes)
        self._network.nodes = [n for n in self._network.nodes if n.id != node_id]
        removed = len(self._network.nodes) < original_count
        if removed:
            logger.info("Node left federation", node_id=str(node_id))
        return removed

    async def get_stats(self) -> FederationStats:
        """Get federation network statistics."""
        by_insight_type: dict[str, int] = {}
        for insight in self._insights:
            by_insight_type[insight.insight_type] = (
                by_insight_type.get(insight.insight_type, 0) + 1
            )
        return FederationStats(
            total_nodes=len(self._network.nodes),
            active_nodes=len(self._network.nodes),
            insights_shared=len(self._insights),
            by_insight_type=by_insight_type,
            proof_verifications=self._proof_verifications,
        )
