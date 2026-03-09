"""Compliance knowledge graph for relationship visualization.

.. deprecated::
    This module contains the original graph implementation. For the newer,
    more complete explorer, see :mod:`app.services.knowledge_graph`. This
    module is maintained for backward compatibility with ``/api/v1/graph``.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog


logger = structlog.get_logger()


class NodeType(str, Enum):
    """Types of nodes in the compliance graph."""

    REGULATION = "regulation"
    REQUIREMENT = "requirement"
    CODE_FILE = "code_file"
    CODE_MODULE = "code_module"
    CODE_FUNCTION = "code_function"
    DATA_TYPE = "data_type"
    TEAM = "team"
    ACTION = "action"
    EVIDENCE = "evidence"


class EdgeType(str, Enum):
    """Types of edges in the compliance graph."""

    REQUIRES = "requires"
    IMPLEMENTS = "implements"
    HANDLES = "handles"
    OWNED_BY = "owned_by"
    ADDRESSES = "addresses"
    PROVES = "proves"
    DEPENDS_ON = "depends_on"
    SUPERSEDES = "supersedes"
    ASSIGNED_TO = "assigned_to"
    REFERENCES = "references"


@dataclass
class GraphNode:
    """A node in the compliance graph."""

    node_id: str = ""
    node_type: NodeType = NodeType.REGULATION
    name: str = ""
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value
            if isinstance(self.node_type, NodeType)
            else str(self.node_type),
            "name": self.name,
            "properties": self.properties,
        }


@dataclass
class GraphEdge:
    """An edge in the compliance graph."""

    edge_id: str = ""
    edge_type: EdgeType = EdgeType.REQUIRES
    source_id: str = ""
    target_id: str = ""
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert edge to dictionary representation."""
        return {
            "edge_id": self.edge_id,
            "edge_type": self.edge_type.value
            if isinstance(self.edge_type, EdgeType)
            else str(self.edge_type),
            "source_id": self.source_id,
            "target_id": self.target_id,
            "properties": self.properties,
        }


@dataclass
class GraphQuery:
    """A structured query against the compliance graph."""

    node_types: list[NodeType] = field(default_factory=list)
    edge_types: list[EdgeType] = field(default_factory=list)
    filters: dict[str, Any] = field(default_factory=dict)
    limit: int = 100


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
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}

    async def add_node(self, node: GraphNode) -> bool:
        """Add a node to the graph."""
        self._nodes[node.node_id] = node
        return True

    async def add_edge(self, edge: GraphEdge) -> bool:
        """Add an edge to the graph."""
        self._edges[edge.edge_id] = edge
        return True

    async def get_node(self, node_id: str) -> GraphNode | None:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    async def get_nodes_by_type(self, node_type: NodeType) -> list[GraphNode]:
        """Get all nodes of a specific type."""
        return [n for n in self._nodes.values() if n.node_type == node_type]

    async def get_connected_nodes(
        self,
        node_id: str,
        edge_type: EdgeType | None = None,
        direction: str = "outgoing",
    ) -> list[GraphNode]:
        """Get nodes connected to a given node."""
        results: list[GraphNode] = []
        for edge in self._edges.values():
            if edge_type and edge.edge_type != edge_type:
                continue
            if direction == "incoming" and edge.target_id == node_id:
                node = self._nodes.get(edge.source_id)
                if node:
                    results.append(node)
            elif direction == "outgoing" and edge.source_id == node_id:
                node = self._nodes.get(edge.target_id)
                if node:
                    results.append(node)
        return results

    async def find_path(self, source_id: str, target_id: str) -> dict[str, Any]:
        """Find path between two nodes."""
        return await self._find_shortest_path(source_id, target_id)

    async def query_natural_language(self, query: str) -> dict[str, Any]:
        """Query the graph using natural language."""
        return await self._process_nl_query(query)

    async def query(self, graph_query: GraphQuery) -> dict[str, Any]:
        """Execute a structured graph query."""
        return await self._execute_query(graph_query)

    async def get_regulation_coverage(self, regulation: str) -> dict[str, Any]:
        """Get regulation coverage statistics."""
        return await self._calculate_coverage(regulation)

    async def export_subgraph(
        self,
        node_ids: list[str] | None = None,
        include_connected: bool = False,
        export_format: str = "json",
    ) -> dict[str, Any]:
        """Export a subgraph."""
        return await self._export_nodes_and_edges(node_ids, include_connected, export_format)

    async def get_impact_analysis(self, node_id: str) -> dict[str, Any]:
        """Get impact analysis for a node."""
        return await self._analyze_impact(node_id)

    def list_node_types(self) -> list[NodeType]:
        """List all available node types."""
        return list(NodeType)

    def list_edge_types(self) -> list[EdgeType]:
        """List all available edge types."""
        return list(EdgeType)

    # -- internal methods (tests mock these) --

    async def _process_nl_query(self, query: str) -> dict[str, Any]:
        return {"nodes": [], "edges": [], "query_interpretation": query}

    async def _execute_query(self, graph_query: GraphQuery) -> dict[str, Any]:
        return {"nodes": [], "edges": [], "total_count": 0}

    async def _calculate_coverage(self, regulation: str) -> dict[str, Any]:
        return {
            "regulation": regulation,
            "total_requirements": 0,
            "implemented_requirements": 0,
            "coverage_percentage": 0.0,
            "gaps": [],
        }

    async def _export_nodes_and_edges(
        self,
        node_ids: list[str] | None = None,
        include_connected: bool = False,
        export_format: str = "json",
    ) -> dict[str, Any]:
        return {"nodes": [], "edges": [], "format": export_format}

    async def _analyze_impact(self, node_id: str) -> dict[str, Any]:
        return {
            "source_node": node_id,
            "affected_nodes": [],
            "total_affected": 0,
        }

    async def _find_shortest_path(self, source_id: str, target_id: str) -> dict[str, Any]:
        return {"path": [], "edges": [], "length": 0}


# Global graph instance
_graph: ComplianceKnowledgeGraph | None = None


def get_knowledge_graph() -> ComplianceKnowledgeGraph:
    """Get or create the global knowledge graph."""
    global _graph
    if _graph is None:
        _graph = ComplianceKnowledgeGraph()
    return _graph
