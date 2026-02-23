"""Regulatory Simulation models."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class SimulationModel(str, Enum):
    MONTE_CARLO = "monte_carlo"
    BAYESIAN = "bayesian"
    SCENARIO_TREE = "scenario_tree"
    ENSEMBLE = "ensemble"


class RegOutcome(str, Enum):
    ENACTED = "enacted"
    AMENDED = "amended"
    WITHDRAWN = "withdrawn"
    DELAYED = "delayed"
    SPLIT = "split"


@dataclass
class SimulationScenario:
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    regulation: str = ""
    jurisdiction: str = ""
    base_probability: float = 0.0
    factors: list[dict[str, Any]] = field(default_factory=list)
    predicted_outcome: RegOutcome = RegOutcome.ENACTED
    confidence_interval: tuple[float, float] | None = None


@dataclass
class SimulationRun:
    id: UUID = field(default_factory=uuid4)
    scenarios: list[SimulationScenario] = field(default_factory=list)
    iterations: int = 0
    model: SimulationModel = SimulationModel.MONTE_CARLO
    results: dict[str, Any] = field(default_factory=dict)
    probability_distribution: list[dict[str, Any]] = field(default_factory=list)
    execution_time_ms: float = 0.0
    run_at: datetime | None = None


@dataclass
class ImpactForecast:
    regulation: str = ""
    probability: float = 0.0
    impact_if_enacted: str = ""
    preparation_cost_usd: float = 0.0
    non_compliance_risk_usd: float = 0.0
    recommended_action: str = ""


@dataclass
class SimulationStats:
    total_runs: int = 0
    total_scenarios: int = 0
    by_model: dict[str, int] = field(default_factory=dict)
    avg_iterations: int = 0
    predictions_validated: int = 0
