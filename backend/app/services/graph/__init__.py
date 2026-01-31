"""Compliance knowledge graph for relationship visualization."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog


logger = structlog.get_logger()


class NodeType(str, Enum):
    """Types of nodes in the compliance graph."""

    REGULATION = "regulation"
    REQUIREMENT = "requirement"
    CODE_FILE = "code_file"
    CODE_FUNCTION = "code_function"
    DATA_TYPE = "data_type"
    TEAM = "team"
    ACTION = "action"
    EVIDENCE = "evidence"


class EdgeType(str, Enum):
    """Types of edges in the compliance graph."""

    REQUIRES = "requires"  # Regulation -> Requirement
    IMPLEMENTS = "implements"  # Code -> Requirement
    HANDLES = "handles"  # Code -> Data Type
    OWNED_BY = "owned_by"  # Code -> Team
    ADDRESSES = "addresses"  # Action -> Requirement
    PROVES = "proves"  # Evidence -> Requirement
    DEPENDS_ON = "depends_on"  # Requirement -> Requirement
    SUPERSEDES = "supersedes"  # Requirement -> Requirement


@dataclass
class GraphNode:
    """A node in the compliance graph."""

    id: UUID = field(default_factory=uuid4)
    type: NodeType = NodeType.REGULATION
    name: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GraphEdge:
    """An edge in the compliance graph."""

    id: UUID = field(default_factory=uuid4)
    type: EdgeType = EdgeType.REQUIRES
    source_id: UUID = field(default_factory=uuid4)
    target_id: UUID = field(default_factory=uuid4)
    properties: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)


class ComplianceKnowledgeGraph:
    """Knowledge graph for compliance relationships.

    Provides graph-based queries and visualizations for:
    - Regulation -> Requirement relationships
    - Requirement -> Code mappings
    - Data flow tracking
    - Team ownership
    - Compliance evidence chains
    """

    def __init__(self):
        self._nodes: dict[UUID, GraphNode] = {}
        self._edges: dict[UUID, GraphEdge] = {}
        self._index_by_type: dict[NodeType, set[UUID]] = {t: set() for t in NodeType}
        self._adjacency: dict[UUID, set[UUID]] = {}  # source -> target edges
        self._reverse_adjacency: dict[UUID, set[UUID]] = {}  # target -> source edges

    def add_node(self, node: GraphNode) -> GraphNode:
        """Add a node to the graph."""
        self._nodes[node.id] = node
        self._index_by_type[node.type].add(node.id)
        if node.id not in self._adjacency:
            self._adjacency[node.id] = set()
            self._reverse_adjacency[node.id] = set()
        return node

    def add_edge(self, edge: GraphEdge) -> GraphEdge:
        """Add an edge to the graph."""
        self._edges[edge.id] = edge
        self._adjacency[edge.source_id].add(edge.id)
        self._reverse_adjacency[edge.target_id].add(edge.id)
        return edge

    def get_node(self, node_id: UUID) -> GraphNode | None:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def get_nodes_by_type(self, node_type: NodeType) -> list[GraphNode]:
        """Get all nodes of a specific type."""
        return [self._nodes[nid] for nid in self._index_by_type.get(node_type, set())]

    def get_outgoing_edges(self, node_id: UUID) -> list[GraphEdge]:
        """Get all edges originating from a node."""
        return [self._edges[eid] for eid in self._adjacency.get(node_id, set())]

    def get_incoming_edges(self, node_id: UUID) -> list[GraphEdge]:
        """Get all edges pointing to a node."""
        return [self._edges[eid] for eid in self._reverse_adjacency.get(node_id, set())]

    def find_path(
        self,
        source_id: UUID,
        target_id: UUID,
        max_depth: int = 10,
    ) -> list[list[UUID]] | None:
        """Find paths between two nodes using BFS."""
        if source_id == target_id:
            return [[source_id]]

        visited = set()
        queue = [[source_id]]
        paths = []

        while queue and len(paths) < 10:
            path = queue.pop(0)
            node = path[-1]

            if len(path) > max_depth:
                continue

            if node in visited:
                continue
            visited.add(node)

            for edge_id in self._adjacency.get(node, set()):
                edge = self._edges[edge_id]
                new_path = path + [edge.target_id]

                if edge.target_id == target_id:
                    paths.append(new_path)
                else:
                    queue.append(new_path)

        return paths if paths else None

    def get_subgraph(
        self,
        center_node_id: UUID,
        depth: int = 2,
        edge_types: list[EdgeType] | None = None,
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        """Get a subgraph centered on a node."""
        nodes = set()
        edges = set()
        queue = [(center_node_id, 0)]

        while queue:
            node_id, current_depth = queue.pop(0)

            if node_id in nodes or current_depth > depth:
                continue

            nodes.add(node_id)

            for edge_id in self._adjacency.get(node_id, set()) | self._reverse_adjacency.get(node_id, set()):
                edge = self._edges.get(edge_id)
                if edge and (edge_types is None or edge.type in edge_types):
                    edges.add(edge_id)
                    next_node = edge.target_id if edge.source_id == node_id else edge.source_id
                    queue.append((next_node, current_depth + 1))

        return (
            [self._nodes[nid] for nid in nodes if nid in self._nodes],
            [self._edges[eid] for eid in edges],
        )

    def query_natural_language(self, query: str) -> dict[str, Any]:
        """Query the graph using natural language.

        Example queries:
        - "What code handles GDPR consent?"
        - "Which teams own code affected by HIPAA?"
        - "Show requirements for EU AI Act"
        """
        query_lower = query.lower()
        results = {"nodes": [], "edges": [], "summary": ""}

        # Simple keyword matching for demonstration
        # In production, would use NLP/LLM for query understanding

        if "gdpr" in query_lower:
            # Find GDPR-related nodes
            for node in self._nodes.values():
                if "gdpr" in node.name.lower() or node.properties.get("regulation") == "GDPR":
                    results["nodes"].append(node)

        if "consent" in query_lower:
            for node in self._nodes.values():
                if "consent" in node.name.lower():
                    results["nodes"].append(node)

        if "code" in query_lower or "handles" in query_lower:
            # Find code files
            for node in self.get_nodes_by_type(NodeType.CODE_FILE):
                results["nodes"].append(node)

        if "team" in query_lower or "owns" in query_lower:
            for node in self.get_nodes_by_type(NodeType.TEAM):
                results["nodes"].append(node)

        results["summary"] = f"Found {len(results['nodes'])} relevant nodes"
        return results

    def export_for_visualization(self) -> dict[str, Any]:
        """Export graph data for visualization (D3.js, Cytoscape, etc.)."""
        return {
            "nodes": [
                {
                    "id": str(n.id),
                    "type": n.type.value,
                    "label": n.name,
                    "properties": n.properties,
                }
                for n in self._nodes.values()
            ],
            "edges": [
                {
                    "id": str(e.id),
                    "type": e.type.value,
                    "source": str(e.source_id),
                    "target": str(e.target_id),
                    "weight": e.weight,
                    "properties": e.properties,
                }
                for e in self._edges.values()
            ],
        }

    def get_compliance_coverage(
        self,
        regulation: str,
    ) -> dict[str, Any]:
        """Calculate compliance coverage for a regulation."""
        # Find regulation node
        reg_nodes = [
            n for n in self.get_nodes_by_type(NodeType.REGULATION)
            if regulation.lower() in n.name.lower()
        ]

        if not reg_nodes:
            return {"coverage": 0, "requirements": 0, "implemented": 0}

        # Find all requirements
        requirements = set()
        for reg_node in reg_nodes:
            for edge in self.get_outgoing_edges(reg_node.id):
                if edge.type == EdgeType.REQUIRES:
                    requirements.add(edge.target_id)

        # Find implemented requirements
        implemented = set()
        for req_id in requirements:
            for edge in self.get_incoming_edges(req_id):
                if edge.type == EdgeType.IMPLEMENTS:
                    implemented.add(req_id)
                    break

        coverage = len(implemented) / len(requirements) * 100 if requirements else 0

        return {
            "coverage": round(coverage, 1),
            "requirements": len(requirements),
            "implemented": len(implemented),
            "gaps": len(requirements) - len(implemented),
        }


# Global graph instance
_graph: ComplianceKnowledgeGraph | None = None


def get_knowledge_graph() -> ComplianceKnowledgeGraph:
    """Get or create the global knowledge graph."""
    global _graph
    if _graph is None:
        _graph = ComplianceKnowledgeGraph()
    return _graph
