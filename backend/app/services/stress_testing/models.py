"""Regulatory Compliance Stress Testing models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ScenarioType(str, Enum):
    """Type of stress test scenario."""

    DATA_BREACH = "data_breach"
    REGULATORY_AUDIT = "regulatory_audit"
    NEW_REGULATION = "new_regulation"
    VENDOR_FAILURE = "vendor_failure"
    MASS_DELETION_REQUEST = "mass_deletion_request"


class RiskTier(str, Enum):
    """Risk tier classification."""

    MINIMAL = "minimal"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    SEVERE = "severe"
    CATASTROPHIC = "catastrophic"


@dataclass
class StressScenario:
    """A stress test scenario definition."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    scenario_type: ScenarioType = ScenarioType.DATA_BREACH
    description: str = ""
    parameters: dict = field(default_factory=dict)
    probability: float = 0.0
    severity: RiskTier = RiskTier.MODERATE


@dataclass
class SimulationResult:
    """Result metrics from a single simulation iteration."""

    id: UUID = field(default_factory=uuid4)
    run_id: UUID = field(default_factory=uuid4)
    metric: str = ""
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    mean: float = 0.0
    std_dev: float = 0.0
    distribution: list[dict] = field(default_factory=list)


@dataclass
class SimulationRun:
    """A Monte Carlo simulation run."""

    id: UUID = field(default_factory=uuid4)
    scenario_id: UUID = field(default_factory=uuid4)
    iterations: int = 1000
    confidence_level: float = 0.95
    status: str = "pending"
    results: list[SimulationResult] = field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class RiskExposure:
    """Calculated risk exposure for a regulation."""

    id: UUID = field(default_factory=uuid4)
    regulation: str = ""
    exposure_amount: float = 0.0
    probability: float = 0.0
    expected_loss: float = 0.0
    risk_tier: RiskTier = RiskTier.MODERATE
    mitigations: list[str] = field(default_factory=list)


@dataclass
class StressTestReport:
    """Aggregate stress test report."""

    id: UUID = field(default_factory=uuid4)
    total_scenarios: int = 0
    total_simulations: int = 0
    aggregate_exposure: float = 0.0
    risk_exposures: list[RiskExposure] = field(default_factory=list)
    worst_case_scenario: str = ""
    recommendations: list[str] = field(default_factory=list)
    generated_at: datetime | None = None
