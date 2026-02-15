"""Regulatory Change Impact Simulator models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class SimulationStatus(str, Enum):
    """Simulation run status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ImpactLevel(str, Enum):
    """Impact severity level."""

    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    NONE = "none"


class ScenarioType(str, Enum):
    """Type of regulatory change scenario."""

    REGULATION_CHANGE = "regulation_change"
    NEW_REGULATION = "new_regulation"
    JURISDICTION_EXPANSION = "jurisdiction_expansion"
    DEADLINE_CHANGE = "deadline_change"
    ENFORCEMENT_ACTION = "enforcement_action"


@dataclass
class RegulatoryChange:
    """A hypothetical regulatory change to simulate."""

    regulation: str = ""
    article_ref: str = ""
    change_description: str = ""
    scenario_type: ScenarioType = ScenarioType.REGULATION_CHANGE
    new_requirements: list[str] = field(default_factory=list)
    modified_requirements: list[str] = field(default_factory=list)
    removed_requirements: list[str] = field(default_factory=list)
    effective_date: str = ""


@dataclass
class AffectedComponent:
    """A code component affected by a simulated change."""

    file_path: str = ""
    component_type: str = ""  # service, endpoint, model, config
    component_name: str = ""
    impact_level: ImpactLevel = ImpactLevel.LOW
    changes_required: list[str] = field(default_factory=list)
    estimated_hours: float = 0.0
    dependencies: list[str] = field(default_factory=list)


@dataclass
class BlastRadius:
    """The blast radius of a simulated regulatory change."""

    total_files: int = 0
    total_services: int = 0
    total_endpoints: int = 0
    total_data_stores: int = 0
    affected_components: list[AffectedComponent] = field(default_factory=list)
    dependency_chain: list[str] = field(default_factory=list)
    estimated_total_hours: float = 0.0
    estimated_person_weeks: float = 0.0


@dataclass
class SimulationResult:
    """Result of a regulatory impact simulation."""

    id: UUID = field(default_factory=uuid4)
    scenario_name: str = ""
    status: SimulationStatus = SimulationStatus.PENDING
    change: RegulatoryChange = field(default_factory=RegulatoryChange)
    blast_radius: BlastRadius = field(default_factory=BlastRadius)
    overall_impact: ImpactLevel = ImpactLevel.LOW
    risk_score: float = 0.0
    recommendations: list[str] = field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class PrebuiltScenario:
    """A pre-built simulation scenario."""

    id: str = ""
    name: str = ""
    description: str = ""
    category: str = ""
    change: RegulatoryChange = field(default_factory=RegulatoryChange)
    difficulty: str = "medium"


@dataclass
class BlastRadiusComponent:
    """A component affected by a regulatory change."""

    component_path: str = ""
    component_type: str = "file"  # file, module, service, api_endpoint
    impact_level: str = "medium"  # low, medium, high, critical
    regulations_affected: list[str] = field(default_factory=list)
    estimated_effort_hours: float = 0.0
    change_type: str = "modification"  # modification, addition, removal, review_only
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_path": self.component_path,
            "component_type": self.component_type,
            "impact_level": self.impact_level,
            "regulations_affected": self.regulations_affected,
            "estimated_effort_hours": self.estimated_effort_hours,
            "change_type": self.change_type,
            "description": self.description,
        }


@dataclass
class BlastRadiusAnalysis:
    """Full blast radius analysis for a regulatory scenario."""

    scenario_id: str = ""
    total_components: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    components: list[BlastRadiusComponent] = field(default_factory=list)
    total_effort_hours: float = 0.0
    risk_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "total_components": self.total_components,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "components": [c.to_dict() for c in self.components],
            "total_effort_hours": self.total_effort_hours,
            "risk_score": self.risk_score,
        }


@dataclass
class ScenarioComparison:
    """Comparison of multiple regulatory scenarios."""

    scenarios: list[dict[str, Any]] = field(default_factory=list)
    winner: str = ""
    recommendation: str = ""
    comparison_matrix: dict[str, dict[str, float]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenarios": self.scenarios,
            "winner": self.winner,
            "recommendation": self.recommendation,
            "comparison_matrix": self.comparison_matrix,
        }
