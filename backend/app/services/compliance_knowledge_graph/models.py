"""Compliance Knowledge Graph models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class NodeType(str, Enum):
    REGULATION = "regulation"
    REQUIREMENT = "requirement"
    CODE_FILE = "code_file"
    CONTROL = "control"
    EVIDENCE = "evidence"
    TEAM = "team"
    FRAMEWORK = "framework"


class EdgeType(str, Enum):
    REQUIRES = "requires"
    IMPLEMENTS = "implements"
    EVIDENCES = "evidences"
    OWNED_BY = "owned_by"
    MAPS_TO = "maps_to"
    DERIVED_FROM = "derived_from"


@dataclass
class GraphNode:
    id: UUID = field(default_factory=uuid4)
    node_type: NodeType = NodeType.REGULATION
    label: str = ""
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    id: UUID = field(default_factory=uuid4)
    source_id: UUID | None = None
    target_id: UUID | None = None
    edge_type: EdgeType = EdgeType.REQUIRES
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphQueryResult:
    query: str = ""
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0
    interpretation: str = ""


@dataclass
class GraphStats:
    total_nodes: int = 0
    total_edges: int = 0
    nodes_by_type: dict[str, int] = field(default_factory=dict)
    edges_by_type: dict[str, int] = field(default_factory=dict)
    frameworks_covered: list[str] = field(default_factory=list)
