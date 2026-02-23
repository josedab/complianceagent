"""Graph Explorer Service."""

import hashlib
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.graph_explorer.models import (
    DrilldownResult,
    ExplorerEdge,
    ExplorerNode,
    ExplorerStats,
    ExplorerView,
    NodeFilter,
    VisualizationMode,
)


logger = structlog.get_logger()


def _deterministic_position(node_id: str, axis: str) -> float:
    """Generate a deterministic layout position using hashlib."""
    digest = hashlib.md5(f"{node_id}:{axis}".encode()).hexdigest()
    return (int(digest[:8], 16) % 1000) / 1000.0


class GraphExplorerService:
    """Service for exploring compliance relationships as interactive graphs."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._views: dict[UUID, ExplorerView] = {}
        self._visualizations_created: int = 0
        self._nodes, self._edges = self._build_seed_graph()

    def _build_seed_graph(self) -> tuple[list[ExplorerNode], list[ExplorerEdge]]:
        """Build a seed graph with frameworks, code files, and violations."""
        nodes: list[ExplorerNode] = []
        edges: list[ExplorerEdge] = []

        # Framework nodes
        frameworks = [
            ("gdpr", "GDPR", "#2196F3"),
            ("hipaa", "HIPAA", "#4CAF50"),
            ("pci-dss", "PCI-DSS", "#FF9800"),
            ("soc2", "SOC2", "#9C27B0"),
        ]
        for fid, label, color in frameworks:
            nodes.append(ExplorerNode(
                id=fid, label=label, node_type="framework",
                size=3.0, color=color,
                properties={"category": "regulation"},
            ))

        # Code file nodes
        code_files = [
            ("file-auth", "auth_service.py", "code"),
            ("file-payment", "payment_handler.py", "code"),
            ("file-patient", "patient_records.py", "code"),
            ("file-config", "app_config.yaml", "code"),
            ("file-api", "api_gateway.py", "code"),
        ]
        for fid, label, ntype in code_files:
            nodes.append(ExplorerNode(
                id=fid, label=label, node_type=ntype,
                size=1.5, color="#607D8B",
                properties={"language": "python"},
            ))

        # Violation nodes
        violations = [
            ("viol-1", "Unencrypted PII", "violation", "#F44336"),
            ("viol-2", "Missing Access Control", "violation", "#F44336"),
            ("viol-3", "Unmasked Card Data", "violation", "#FF5722"),
        ]
        for vid, label, ntype, color in violations:
            nodes.append(ExplorerNode(
                id=vid, label=label, node_type=ntype,
                size=2.0, color=color,
                properties={"severity": "high"},
            ))

        # Edges: frameworks → code files
        edges.extend([
            ExplorerEdge(source="gdpr", target="file-auth", edge_type="regulates", weight=0.9),
            ExplorerEdge(source="hipaa", target="file-patient", edge_type="regulates", weight=0.95),
            ExplorerEdge(source="pci-dss", target="file-payment", edge_type="regulates", weight=0.9),
            ExplorerEdge(source="soc2", target="file-config", edge_type="regulates", weight=0.8),
            ExplorerEdge(source="soc2", target="file-api", edge_type="regulates", weight=0.7),
        ])

        # Edges: code files → violations
        edges.extend([
            ExplorerEdge(source="file-auth", target="viol-1", edge_type="has_violation", weight=1.0, color="#F44336"),
            ExplorerEdge(source="file-api", target="viol-2", edge_type="has_violation", weight=0.8, color="#F44336"),
            ExplorerEdge(source="file-payment", target="viol-3", edge_type="has_violation", weight=0.9, color="#FF5722"),
        ])

        # Edges: violations → frameworks
        edges.extend([
            ExplorerEdge(source="viol-1", target="gdpr", edge_type="violates", weight=1.0),
            ExplorerEdge(source="viol-2", target="soc2", edge_type="violates", weight=0.8),
            ExplorerEdge(source="viol-3", target="pci-dss", edge_type="violates", weight=0.9),
        ])

        return nodes, edges

    def _apply_filters(
        self,
        nodes: list[ExplorerNode],
        edges: list[ExplorerEdge],
        filters: dict,
    ) -> tuple[list[ExplorerNode], list[ExplorerEdge]]:
        """Filter nodes and edges based on criteria."""
        node_type_filter = filters.get("node_type")
        if node_type_filter and node_type_filter != NodeFilter.ALL.value:
            type_map = {
                NodeFilter.REGULATIONS.value: "framework",
                NodeFilter.CODE.value: "code",
                NodeFilter.VIOLATIONS.value: "violation",
                NodeFilter.CONTROLS.value: "control",
                NodeFilter.FRAMEWORKS.value: "framework",
            }
            target_type = type_map.get(node_type_filter, node_type_filter)
            nodes = [n for n in nodes if n.node_type == target_type]
            node_ids = {n.id for n in nodes}
            edges = [e for e in edges if e.source in node_ids and e.target in node_ids]
        return nodes, edges

    async def create_view(
        self,
        mode: str = "force_directed",
        filters: dict | None = None,
    ) -> ExplorerView:
        """Create a new graph visualization view."""
        filters = filters or {}
        filtered_nodes, filtered_edges = self._apply_filters(
            list(self._nodes), list(self._edges), filters,
        )

        view = ExplorerView(
            mode=VisualizationMode(mode),
            nodes=filtered_nodes,
            edges=filtered_edges,
            filters=filters,
            center_x=_deterministic_position("center", "x"),
            center_y=_deterministic_position("center", "y"),
        )
        self._views[view.id] = view
        self._visualizations_created += 1
        logger.info(
            "Graph view created",
            mode=mode,
            nodes=len(filtered_nodes),
            edges=len(filtered_edges),
        )
        return view

    async def drilldown(self, node_id: str) -> DrilldownResult:
        """Drill down into a specific node to see neighbors and details."""
        node = next((n for n in self._nodes if n.id == node_id), None)
        if not node:
            return DrilldownResult(node_id=node_id, label="Unknown")

        # Find neighbors via edge traversal
        neighbor_ids: set[str] = set()
        for edge in self._edges:
            if edge.source == node_id:
                neighbor_ids.add(edge.target)
            elif edge.target == node_id:
                neighbor_ids.add(edge.source)

        neighbors = [
            {"id": n.id, "label": n.label, "node_type": n.node_type}
            for n in self._nodes if n.id in neighbor_ids
        ]

        related_violations = [
            {"id": n.id, "label": n.label, "properties": n.properties}
            for n in self._nodes
            if n.id in neighbor_ids and n.node_type == "violation"
        ]

        coverage: dict = {}
        if node.node_type == "framework":
            regulated = [n for n in neighbors if n.get("node_type") == "code"]
            coverage = {
                "files_regulated": len(regulated),
                "violations_linked": len(related_violations),
            }

        logger.info("Drilldown performed", node_id=node_id, neighbors=len(neighbors))
        return DrilldownResult(
            node_id=node_id,
            label=node.label,
            neighbors=neighbors,
            related_violations=related_violations,
            coverage=coverage,
        )

    async def search_nodes(self, query: str) -> list[ExplorerNode]:
        """Search nodes by label or properties."""
        query_lower = query.lower()
        results: list[ExplorerNode] = []
        for node in self._nodes:
            if query_lower in node.label.lower():
                results.append(node)
                continue
            for value in node.properties.values():
                if query_lower in str(value).lower():
                    results.append(node)
                    break
        return results

    async def export_view(self, view_id: UUID, format: str = "json") -> dict:
        """Export a graph view to a serializable format."""
        view = self._views.get(view_id)
        if not view:
            return {"error": "View not found"}

        return {
            "format": format,
            "view_id": str(view.id),
            "mode": view.mode.value,
            "nodes": [
                {"id": n.id, "label": n.label, "type": n.node_type, "size": n.size, "color": n.color}
                for n in view.nodes
            ],
            "edges": [
                {"source": e.source, "target": e.target, "type": e.edge_type, "weight": e.weight}
                for e in view.edges
            ],
            "metadata": {
                "total_nodes": len(view.nodes),
                "total_edges": len(view.edges),
                "zoom": view.zoom,
            },
        }

    async def get_stats(self) -> ExplorerStats:
        """Get graph explorer statistics."""
        by_node_type: dict[str, int] = {}
        for node in self._nodes:
            by_node_type[node.node_type] = by_node_type.get(node.node_type, 0) + 1

        return ExplorerStats(
            total_nodes=len(self._nodes),
            total_edges=len(self._edges),
            by_node_type=by_node_type,
            visualizations_created=self._visualizations_created,
        )
