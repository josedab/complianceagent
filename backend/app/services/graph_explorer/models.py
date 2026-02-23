"""Data models for Graph Explorer Service."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class VisualizationMode(str, Enum):
    """Graph visualization layout modes."""

    FORCE_DIRECTED = "force_directed"
    HIERARCHICAL = "hierarchical"
    RADIAL = "radial"
    GEOGRAPHIC = "geographic"


class NodeFilter(str, Enum):
    """Filter categories for graph nodes."""

    ALL = "all"
    REGULATIONS = "regulations"
    CODE = "code"
    VIOLATIONS = "violations"
    CONTROLS = "controls"
    FRAMEWORKS = "frameworks"


@dataclass
class ExplorerNode:
    """A node in the compliance graph visualization."""

    id: str = ""
    label: str = ""
    node_type: str = ""
    size: float = 1.0
    color: str = "#666666"
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExplorerEdge:
    """An edge connecting two nodes in the graph."""

    source: str = ""
    target: str = ""
    edge_type: str = ""
    weight: float = 1.0
    color: str = "#999999"


@dataclass
class ExplorerView:
    """A graph view with nodes, edges, and display settings."""

    id: UUID = field(default_factory=uuid4)
    mode: VisualizationMode = VisualizationMode.FORCE_DIRECTED
    nodes: list[ExplorerNode] = field(default_factory=list)
    edges: list[ExplorerEdge] = field(default_factory=list)
    filters: dict[str, Any] = field(default_factory=dict)
    zoom: float = 1.0
    center_x: float = 0.0
    center_y: float = 0.0


@dataclass
class DrilldownResult:
    """Result of drilling down into a specific node."""

    node_id: str = ""
    label: str = ""
    neighbors: list[dict[str, Any]] = field(default_factory=list)
    related_violations: list[dict[str, Any]] = field(default_factory=list)
    coverage: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExplorerStats:
    """Statistics for the graph explorer."""

    total_nodes: int = 0
    total_edges: int = 0
    by_node_type: dict[str, int] = field(default_factory=dict)
    visualizations_created: int = 0
