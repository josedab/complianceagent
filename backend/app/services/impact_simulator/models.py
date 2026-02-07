"""Regulatory Change Impact Simulator models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
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
