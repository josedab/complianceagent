"""Compliance Knowledge Graph service.

Interactive graph of relationships: Regulation → Requirement → Code → Control → Evidence.
Supports natural language queries for navigating compliance relationships.
"""

from typing import Any
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.compliance_knowledge_graph.models import (
    EdgeType,
    GraphEdge,
    GraphNode,
    GraphQueryResult,
    GraphStats,
    NodeType,
)


logger = structlog.get_logger()

# Seed graph data covering GDPR, HIPAA, SOC 2
_SEED_NODES: list[dict[str, Any]] = [
    {"type": NodeType.FRAMEWORK, "label": "GDPR", "props": {"jurisdiction": "EU", "articles": 99}},
    {"type": NodeType.FRAMEWORK, "label": "HIPAA", "props": {"jurisdiction": "US", "sections": 12}},
    {"type": NodeType.FRAMEWORK, "label": "SOC 2", "props": {"jurisdiction": "Global", "categories": 5}},
    {"type": NodeType.REQUIREMENT, "label": "GDPR Art.17 Right to Erasure", "props": {"framework": "GDPR", "article": "17"}},
    {"type": NodeType.REQUIREMENT, "label": "GDPR Art.7 Consent", "props": {"framework": "GDPR", "article": "7"}},
    {"type": NodeType.REQUIREMENT, "label": "GDPR Art.32 Security", "props": {"framework": "GDPR", "article": "32"}},
    {"type": NodeType.REQUIREMENT, "label": "HIPAA §164.312 Technical Safeguards", "props": {"framework": "HIPAA"}},
    {"type": NodeType.REQUIREMENT, "label": "HIPAA §164.502 Minimum Necessary", "props": {"framework": "HIPAA"}},
    {"type": NodeType.REQUIREMENT, "label": "SOC 2 CC6.1 Access Controls", "props": {"framework": "SOC 2"}},
    {"type": NodeType.REQUIREMENT, "label": "SOC 2 CC7.2 Monitoring", "props": {"framework": "SOC 2"}},
    {"type": NodeType.CODE_FILE, "label": "src/api/users.py", "props": {"language": "python", "pii": True}},
    {"type": NodeType.CODE_FILE, "label": "src/auth/login.py", "props": {"language": "python", "auth": True}},
    {"type": NodeType.CODE_FILE, "label": "src/db/models.py", "props": {"language": "python", "storage": True}},
    {"type": NodeType.CONTROL, "label": "Encryption at Rest", "props": {"status": "implemented"}},
    {"type": NodeType.CONTROL, "label": "MFA Authentication", "props": {"status": "implemented"}},
    {"type": NodeType.CONTROL, "label": "Audit Logging", "props": {"status": "implemented"}},
    {"type": NodeType.CONTROL, "label": "Data Deletion API", "props": {"status": "partial"}},
    {"type": NodeType.EVIDENCE, "label": "Encryption config audit", "props": {"collected": "2025-01-15"}},
    {"type": NodeType.EVIDENCE, "label": "Access review Q4 2024", "props": {"collected": "2024-12-20"}},
]


class ComplianceKnowledgeGraphService:
    """Navigable knowledge graph of compliance relationships."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._nodes: dict[UUID, GraphNode] = {}
        self._edges: list[GraphEdge] = []
        self._init_seed_graph()

    def _init_seed_graph(self) -> None:
        node_ids: dict[str, UUID] = {}
        for item in _SEED_NODES:
            node = GraphNode(node_type=item["type"], label=item["label"], properties=item.get("props", {}))
            self._nodes[node.id] = node
            node_ids[item["label"]] = node.id

        # Build edges
        edge_defs = [
            ("GDPR", "GDPR Art.17 Right to Erasure", EdgeType.REQUIRES),
            ("GDPR", "GDPR Art.7 Consent", EdgeType.REQUIRES),
            ("GDPR", "GDPR Art.32 Security", EdgeType.REQUIRES),
            ("HIPAA", "HIPAA §164.312 Technical Safeguards", EdgeType.REQUIRES),
            ("HIPAA", "HIPAA §164.502 Minimum Necessary", EdgeType.REQUIRES),
            ("SOC 2", "SOC 2 CC6.1 Access Controls", EdgeType.REQUIRES),
            ("SOC 2", "SOC 2 CC7.2 Monitoring", EdgeType.REQUIRES),
            ("GDPR Art.17 Right to Erasure", "Data Deletion API", EdgeType.MAPS_TO),
            ("GDPR Art.32 Security", "Encryption at Rest", EdgeType.MAPS_TO),
            ("HIPAA §164.312 Technical Safeguards", "Encryption at Rest", EdgeType.MAPS_TO),
            ("SOC 2 CC6.1 Access Controls", "MFA Authentication", EdgeType.MAPS_TO),
            ("SOC 2 CC7.2 Monitoring", "Audit Logging", EdgeType.MAPS_TO),
            ("Data Deletion API", "src/api/users.py", EdgeType.IMPLEMENTS),
            ("MFA Authentication", "src/auth/login.py", EdgeType.IMPLEMENTS),
            ("Encryption at Rest", "src/db/models.py", EdgeType.IMPLEMENTS),
            ("Encryption at Rest", "Encryption config audit", EdgeType.EVIDENCES),
            ("MFA Authentication", "Access review Q4 2024", EdgeType.EVIDENCES),
        ]
        for src_label, tgt_label, edge_type in edge_defs:
            src_id = node_ids.get(src_label)
            tgt_id = node_ids.get(tgt_label)
            if src_id and tgt_id:
                self._edges.append(GraphEdge(source_id=src_id, target_id=tgt_id, edge_type=edge_type))

    async def query(self, natural_language: str) -> GraphQueryResult:
        """Natural language query over the compliance graph."""
        nl = natural_language.lower()

        matched_nodes: list[GraphNode] = []
        for node in self._nodes.values():
            if any(term in node.label.lower() for term in nl.split() if len(term) > 2):
                matched_nodes.append(node)

        matched_ids = {n.id for n in matched_nodes}
        matched_edges = [
            e for e in self._edges
            if e.source_id in matched_ids or e.target_id in matched_ids
        ]

        # Expand to connected nodes
        for edge in matched_edges:
            for nid in (edge.source_id, edge.target_id):
                if nid and nid not in matched_ids:
                    node = self._nodes.get(nid)
                    if node:
                        matched_nodes.append(node)
                        matched_ids.add(nid)

        interpretation = f"Found {len(matched_nodes)} nodes and {len(matched_edges)} relationships matching '{natural_language}'"

        return GraphQueryResult(
            query=natural_language,
            nodes=matched_nodes,
            edges=matched_edges,
            total_nodes=len(matched_nodes),
            total_edges=len(matched_edges),
            interpretation=interpretation,
        )

    async def get_stats(self) -> GraphStats:
        nodes_by_type: dict[str, int] = {}
        for n in self._nodes.values():
            nodes_by_type[n.node_type.value] = nodes_by_type.get(n.node_type.value, 0) + 1

        edges_by_type: dict[str, int] = {}
        for e in self._edges:
            edges_by_type[e.edge_type.value] = edges_by_type.get(e.edge_type.value, 0) + 1

        frameworks = [n.label for n in self._nodes.values() if n.node_type == NodeType.FRAMEWORK]

        return GraphStats(
            total_nodes=len(self._nodes),
            total_edges=len(self._edges),
            nodes_by_type=nodes_by_type,
            edges_by_type=edges_by_type,
            frameworks_covered=frameworks,
        )

    async def get_node(self, node_id: UUID) -> GraphNode | None:
        return self._nodes.get(node_id)

    async def get_neighbors(self, node_id: UUID) -> GraphQueryResult:
        """Get all nodes connected to a given node."""
        neighbors: list[GraphNode] = []
        related_edges: list[GraphEdge] = []

        for edge in self._edges:
            if edge.source_id == node_id:
                related_edges.append(edge)
                n = self._nodes.get(edge.target_id) if edge.target_id else None
                if n:
                    neighbors.append(n)
            elif edge.target_id == node_id:
                related_edges.append(edge)
                n = self._nodes.get(edge.source_id) if edge.source_id else None
                if n:
                    neighbors.append(n)

        return GraphQueryResult(
            nodes=neighbors,
            edges=related_edges,
            total_nodes=len(neighbors),
            total_edges=len(related_edges),
        )
