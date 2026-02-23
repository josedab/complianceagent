"""Regulatory Change Simulator models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass
class SimulationScenario:
    """A regulatory change scenario to simulate."""

    id: UUID = field(default_factory=uuid4)
    regulation: str = ""
    change_description: str = ""
    affected_articles: list[str] = field(default_factory=list)
    severity: str = "medium"


@dataclass
class SimulationImpact:
    """Impact assessment from a simulation run."""

    scenario_id: UUID = field(default_factory=uuid4)
    affected_repos: list[str] = field(default_factory=list)
    affected_files_count: int = 0
    remediation_hours: float = 0.0
    risk_score: float = 0.0
    affected_frameworks: list[str] = field(default_factory=list)


@dataclass
class PreparationMilestone:
    """A milestone in a preparation roadmap."""

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    deadline_weeks: int = 0
    team: str = ""
    status: str = "pending"


@dataclass
class PreparationRoadmap:
    """A roadmap for preparing for a regulatory change."""

    scenario_id: UUID = field(default_factory=uuid4)
    milestones: list[PreparationMilestone] = field(default_factory=list)
    total_effort_hours: float = 0.0
    recommended_start: datetime = field(default_factory=lambda: datetime.now(UTC))
