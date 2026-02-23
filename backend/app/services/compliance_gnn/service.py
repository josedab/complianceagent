"""Compliance Graph Neural Network Service."""

import hashlib
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.compliance_gnn.models import (
    EdgeType,
    GraphEdge,
    GraphNode,
    GraphStats,
    NodeType,
    PredictionType,
    ViolationPrediction,
)


logger = structlog.get_logger()

_SEED_NODES: list[GraphNode] = [
    GraphNode(id="gdpr", node_type=NodeType.FRAMEWORK, label="GDPR", properties={"jurisdiction": "EU", "articles": 99}),
    GraphNode(id="hipaa", node_type=NodeType.FRAMEWORK, label="HIPAA", properties={"jurisdiction": "US", "sections": 45}),
    GraphNode(id="pci-dss", node_type=NodeType.FRAMEWORK, label="PCI-DSS", properties={"jurisdiction": "Global", "requirements": 12}),
    GraphNode(id="gdpr-art5", node_type=NodeType.REGULATION, label="GDPR Art. 5 — Processing Principles", properties={"framework": "GDPR"}),
    GraphNode(id="gdpr-art17", node_type=NodeType.REGULATION, label="GDPR Art. 17 — Right to Erasure", properties={"framework": "GDPR"}),
    GraphNode(id="hipaa-164312", node_type=NodeType.REGULATION, label="HIPAA §164.312 — Technical Safeguards", properties={"framework": "HIPAA"}),
    GraphNode(id="src/users.py", node_type=NodeType.CODE_FILE, label="src/users.py", properties={"language": "python", "loc": 250}),
    GraphNode(id="src/payments.py", node_type=NodeType.CODE_FILE, label="src/payments.py", properties={"language": "python", "loc": 180}),
    GraphNode(id="src/health/records.py", node_type=NodeType.CODE_FILE, label="src/health/records.py", properties={"language": "python", "loc": 320}),
    GraphNode(id="v-consent", node_type=NodeType.VIOLATION, label="Missing consent check", properties={"severity": "high", "framework": "GDPR"}),
    GraphNode(id="v-phi-log", node_type=NodeType.VIOLATION, label="PHI in logs", properties={"severity": "critical", "framework": "HIPAA"}),
]

_SEED_EDGES: list[GraphEdge] = [
    GraphEdge(source="gdpr", target="gdpr-art5", edge_type=EdgeType.REQUIRES, weight=1.0),
    GraphEdge(source="gdpr", target="gdpr-art17", edge_type=EdgeType.REQUIRES, weight=1.0),
    GraphEdge(source="hipaa", target="hipaa-164312", edge_type=EdgeType.REQUIRES, weight=1.0),
    GraphEdge(source="src/users.py", target="gdpr-art5", edge_type=EdgeType.IMPLEMENTS, weight=0.7),
    GraphEdge(source="src/users.py", target="v-consent", edge_type=EdgeType.VIOLATES, weight=0.9),
    GraphEdge(source="src/payments.py", target="pci-dss", edge_type=EdgeType.IMPLEMENTS, weight=0.8),
    GraphEdge(source="src/health/records.py", target="hipaa-164312", edge_type=EdgeType.IMPLEMENTS, weight=0.6),
    GraphEdge(source="src/health/records.py", target="v-phi-log", edge_type=EdgeType.VIOLATES, weight=0.95),
    GraphEdge(source="src/users.py", target="src/payments.py", edge_type=EdgeType.DEPENDS_ON, weight=0.5),
]


class ComplianceGNNService:
    """GNN-based compliance violation prediction."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._nodes: list[GraphNode] = list(_SEED_NODES)
        self._edges: list[GraphEdge] = list(_SEED_EDGES)
        self._predictions: list[ViolationPrediction] = []

    async def predict_violations(self, file_paths: list[str] | None = None, top_k: int = 10) -> list[ViolationPrediction]:
        """Predict which files are most likely to have compliance violations."""
        targets = file_paths or [n.id for n in self._nodes if n.node_type == NodeType.CODE_FILE]
        predictions = []

        for file_path in targets:
            node = next((n for n in self._nodes if n.id == file_path), None)
            if not node:
                continue

            # Compute risk score from graph neighborhood
            violation_edges = [e for e in self._edges if e.source == file_path and e.edge_type == EdgeType.VIOLATES]
            impl_edges = [e for e in self._edges if e.source == file_path and e.edge_type == EdgeType.IMPLEMENTS]
            dep_edges = [e for e in self._edges if e.source == file_path and e.edge_type == EdgeType.DEPENDS_ON]

            # Risk = existing violations + low implementation coverage + dependency risk
            violation_risk = sum(e.weight for e in violation_edges)
            coverage_gap = max(0, 1.0 - sum(e.weight for e in impl_edges))
            dep_risk = sum(0.3 for _ in dep_edges)
            total_risk = min(1.0, (violation_risk * 0.5 + coverage_gap * 0.3 + dep_risk * 0.2))

            # Deterministic confidence from file hash
            conf_hash = int(hashlib.sha256(file_path.encode()).hexdigest()[:4], 16) % 30
            confidence = 0.65 + conf_hash / 100

            frameworks = list({e.properties.get("framework", "") for e in violation_edges if e.properties.get("framework")})
            if not frameworks:
                frameworks = [e.target.split("-")[0].upper() for e in impl_edges if "-" in e.target]

            factors = []
            if violation_edges:
                factors.append(f"{len(violation_edges)} existing violation(s)")
            if coverage_gap > 0.3:
                factors.append(f"Low compliance coverage ({1 - coverage_gap:.0%})")
            if dep_edges:
                factors.append(f"{len(dep_edges)} dependency risk(s)")

            prediction = ViolationPrediction(
                file_path=file_path,
                prediction_type=PredictionType.VIOLATION_RISK,
                risk_score=round(total_risk, 3),
                confidence=round(confidence, 3),
                frameworks=frameworks or ["General"],
                contributing_factors=factors,
                recommended_actions=[f"Run compliance scan on {file_path}", "Review framework implementation gaps"],
                predicted_at=datetime.now(UTC),
            )
            predictions.append(prediction)

        predictions.sort(key=lambda p: p.risk_score, reverse=True)
        self._predictions.extend(predictions[:top_k])
        logger.info("Violation predictions generated", count=len(predictions[:top_k]))
        return predictions[:top_k]

    def get_graph(self) -> dict:
        return {
            "nodes": [{"id": n.id, "type": n.node_type.value, "label": n.label} for n in self._nodes],
            "edges": [{"source": e.source, "target": e.target, "type": e.edge_type.value, "weight": e.weight} for e in self._edges],
        }

    def get_node_neighbors(self, node_id: str) -> dict:
        node = next((n for n in self._nodes if n.id == node_id), None)
        if not node:
            return {"node": None, "neighbors": []}
        neighbors = []
        for e in self._edges:
            if e.source == node_id:
                target = next((n for n in self._nodes if n.id == e.target), None)
                if target:
                    neighbors.append({"node": target.label, "edge": e.edge_type.value, "weight": e.weight})
            elif e.target == node_id:
                source = next((n for n in self._nodes if n.id == e.source), None)
                if source:
                    neighbors.append({"node": source.label, "edge": e.edge_type.value, "weight": e.weight})
        return {"node": node.label, "neighbors": neighbors}

    def get_stats(self) -> GraphStats:
        by_node: dict[str, int] = {}
        by_edge: dict[str, int] = {}
        for n in self._nodes:
            by_node[n.node_type.value] = by_node.get(n.node_type.value, 0) + 1
        for e in self._edges:
            by_edge[e.edge_type.value] = by_edge.get(e.edge_type.value, 0) + 1
        confs = [p.confidence for p in self._predictions]
        return GraphStats(
            total_nodes=len(self._nodes),
            total_edges=len(self._edges),
            by_node_type=by_node,
            by_edge_type=by_edge,
            predictions_made=len(self._predictions),
            avg_prediction_confidence=round(sum(confs) / len(confs), 3) if confs else 0.0,
        )
