"""Knowledge graph data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class NodeType(str, Enum):
    """Types of nodes in the knowledge graph."""
    REGULATION = "regulation"
    REQUIREMENT = "requirement"
    CONTROL = "control"
    CODE_FILE = "code_file"
    FUNCTION = "function"
    DATA_ELEMENT = "data_element"
    VENDOR = "vendor"
    RISK = "risk"
    EVIDENCE = "evidence"
    POLICY = "policy"
    TEAM = "team"
    OWNER = "owner"


class RelationType(str, Enum):
    """Types of relationships between nodes."""
    CONTAINS = "contains"
    IMPLEMENTS = "implements"
    REQUIRES = "requires"
    DEPENDS_ON = "depends_on"
    PROCESSES = "processes"
    STORES = "stores"
    OWNED_BY = "owned_by"
    REFERENCES = "references"
    MITIGATES = "mitigates"
    VIOLATES = "violates"
    COMPLIES_WITH = "complies_with"
    SUPERSEDES = "supersedes"
    RELATED_TO = "related_to"
    PROVIDES_EVIDENCE_FOR = "provides_evidence_for"


@dataclass
class GraphNode:
    """Node in the knowledge graph."""
    id: UUID = field(default_factory=uuid4)
    node_type: NodeType = NodeType.REQUIREMENT
    name: str = ""
    description: str = ""
    
    # External references
    external_id: str = ""
    source: str = ""
    
    # Properties
    properties: dict = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # For visualization
    x: float = 0.0
    y: float = 0.0
    group: str = ""
    size: float = 1.0
    color: str = ""


@dataclass
class GraphEdge:
    """Edge (relationship) in the knowledge graph."""
    id: UUID = field(default_factory=uuid4)
    source_id: UUID = field(default_factory=uuid4)
    target_id: UUID = field(default_factory=uuid4)
    relation_type: RelationType = RelationType.RELATED_TO
    
    # Edge properties
    weight: float = 1.0
    properties: dict = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KnowledgeGraph:
    """Complete knowledge graph structure."""
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    name: str = ""
    description: str = ""
    
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    
    # Index for fast lookup
    nodes_by_id: dict[UUID, GraphNode] = field(default_factory=dict)
    nodes_by_type: dict[NodeType, list[GraphNode]] = field(default_factory=dict)
    
    # Statistics
    node_count: int = 0
    edge_count: int = 0
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_node(self, node: GraphNode) -> None:
        """Add a node to the graph."""
        self.nodes.append(node)
        self.nodes_by_id[node.id] = node
        if node.node_type not in self.nodes_by_type:
            self.nodes_by_type[node.node_type] = []
        self.nodes_by_type[node.node_type].append(node)
        self.node_count += 1
        self.updated_at = datetime.utcnow()
    
    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)
        self.edge_count += 1
        self.updated_at = datetime.utcnow()
    
    def get_neighbors(self, node_id: UUID) -> list[GraphNode]:
        """Get all nodes connected to a given node."""
        neighbor_ids = set()
        for edge in self.edges:
            if edge.source_id == node_id:
                neighbor_ids.add(edge.target_id)
            elif edge.target_id == node_id:
                neighbor_ids.add(edge.source_id)
        return [self.nodes_by_id[nid] for nid in neighbor_ids if nid in self.nodes_by_id]


@dataclass
class GraphQuery:
    """Query for the knowledge graph."""
    id: UUID = field(default_factory=uuid4)
    
    # Natural language query
    natural_query: str = ""
    
    # Structured query components
    node_types: list[NodeType] = field(default_factory=list)
    relation_types: list[RelationType] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    filters: dict = field(default_factory=dict)
    
    # Traversal options
    max_depth: int = 3
    max_results: int = 100
    
    # Starting points
    start_nodes: list[UUID] = field(default_factory=list)


@dataclass
class GraphQueryResult:
    """Result of a graph query."""
    query_id: UUID = field(default_factory=uuid4)
    
    # Matched subgraph
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    
    # Answer from AI
    natural_answer: str = ""
    
    # Paths found (for path queries)
    paths: list[list[UUID]] = field(default_factory=list)
    
    # Statistics
    total_nodes: int = 0
    total_edges: int = 0
    execution_time_ms: float = 0.0


# Pre-defined query templates
QUERY_TEMPLATES = {
    "compliance_path": {
        "description": "Find path from regulation to code implementation",
        "start_types": [NodeType.REGULATION],
        "end_types": [NodeType.CODE_FILE, NodeType.FUNCTION],
        "relations": [
            RelationType.CONTAINS,
            RelationType.REQUIRES,
            RelationType.IMPLEMENTS,
        ],
    },
    "risk_analysis": {
        "description": "Find all risks related to a requirement",
        "start_types": [NodeType.REQUIREMENT],
        "end_types": [NodeType.RISK],
        "relations": [
            RelationType.RELATED_TO,
            RelationType.VIOLATES,
        ],
    },
    "data_flow": {
        "description": "Trace data elements through the system",
        "start_types": [NodeType.DATA_ELEMENT],
        "end_types": [NodeType.CODE_FILE, NodeType.VENDOR],
        "relations": [
            RelationType.PROCESSES,
            RelationType.STORES,
            RelationType.DEPENDS_ON,
        ],
    },
    "evidence_mapping": {
        "description": "Find evidence supporting a control",
        "start_types": [NodeType.CONTROL],
        "end_types": [NodeType.EVIDENCE, NodeType.CODE_FILE],
        "relations": [
            RelationType.PROVIDES_EVIDENCE_FOR,
            RelationType.IMPLEMENTS,
        ],
    },
}
