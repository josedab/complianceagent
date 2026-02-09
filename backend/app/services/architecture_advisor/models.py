"""Regulation-to-Architecture Advisor models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class PatternType(str, Enum):
    """Architectural pattern types."""

    MICROSERVICES = "microservices"
    MONOLITH = "monolith"
    EVENT_DRIVEN = "event_driven"
    SERVERLESS = "serverless"
    DATA_LAKE = "data_lake"
    API_GATEWAY = "api_gateway"
    CQRS = "cqrs"
    DATA_MESH = "data_mesh"


class RiskSeverity(str, Enum):
    """Risk severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ArchitecturePattern:
    """Detected architectural pattern in a codebase."""

    pattern_type: PatternType = PatternType.MONOLITH
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ComplianceRisk:
    """A compliance risk identified in the architecture."""

    id: UUID = field(default_factory=uuid4)
    pattern: PatternType = PatternType.MONOLITH
    regulation: str = ""
    severity: RiskSeverity = RiskSeverity.MEDIUM
    title: str = ""
    description: str = ""
    affected_components: list[str] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class ArchitectureRecommendation:
    """A recommendation for improving compliance through architecture."""

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    regulation: str = ""
    current_pattern: PatternType = PatternType.MONOLITH
    recommended_pattern: str = ""
    effort_estimate_days: int = 0
    impact: RiskSeverity = RiskSeverity.MEDIUM
    trade_offs: list[str] = field(default_factory=list)


@dataclass
class ArchitectureScore:
    """Compliance architecture score for a codebase."""

    overall_score: int = 0
    data_isolation_score: int = 0
    encryption_score: int = 0
    audit_trail_score: int = 0
    access_control_score: int = 0
    data_flow_score: int = 0
    max_score: int = 100
    grade: str = ""
    risks_found: int = 0
    recommendations_count: int = 0


@dataclass
class DesignReviewResult:
    """Result of an architecture design review."""

    id: UUID = field(default_factory=uuid4)
    repo: str = ""
    detected_patterns: list[ArchitecturePattern] = field(default_factory=list)
    risks: list[ComplianceRisk] = field(default_factory=list)
    recommendations: list[ArchitectureRecommendation] = field(default_factory=list)
    score: ArchitectureScore = field(default_factory=ArchitectureScore)
    regulations_analyzed: list[str] = field(default_factory=list)
    reviewed_at: datetime | None = None
