"""Compliance Graph Neural Network models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class NodeType(str, Enum):
    REGULATION = "regulation"
    CODE_FILE = "code_file"
    VIOLATION = "violation"
    FRAMEWORK = "framework"
    CONTROL = "control"


class EdgeType(str, Enum):
    REQUIRES = "requires"
    VIOLATES = "violates"
    IMPLEMENTS = "implements"
    DEPENDS_ON = "depends_on"
    RELATED_TO = "related_to"


class PredictionType(str, Enum):
    VIOLATION_RISK = "violation_risk"
    COMPLIANCE_GAP = "compliance_gap"
    IMPACT_PROPAGATION = "impact_propagation"


@dataclass
class GraphNode:
    id: str = ""
    node_type: NodeType = NodeType.CODE_FILE
    label: str = ""
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str = ""
    target: str = ""
    edge_type: EdgeType = EdgeType.RELATED_TO
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class ViolationPrediction:
    id: UUID = field(default_factory=uuid4)
    file_path: str = ""
    prediction_type: PredictionType = PredictionType.VIOLATION_RISK
    risk_score: float = 0.0
    confidence: float = 0.0
    frameworks: list[str] = field(default_factory=list)
    contributing_factors: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    predicted_at: datetime | None = None


@dataclass
class GraphStats:
    total_nodes: int = 0
    total_edges: int = 0
    by_node_type: dict[str, int] = field(default_factory=dict)
    by_edge_type: dict[str, int] = field(default_factory=dict)
    predictions_made: int = 0
    avg_prediction_confidence: float = 0.0
