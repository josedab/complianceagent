"""Scenario planner models for compliance planning and impact analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ScenarioType(str, Enum):
    """Types of planning scenarios."""

    market_expansion = "market_expansion"
    product_launch = "product_launch"
    data_processing = "data_processing"
    vendor_change = "vendor_change"
    acquisition = "acquisition"


class RegionGroup(str, Enum):
    """Geographic region groups."""

    eu = "eu"
    us = "us"
    apac = "apac"
    latam = "latam"
    mena = "mena"
    global_ = "global"


@dataclass
class PlanningScenario:
    """A compliance planning scenario."""

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    scenario_type: ScenarioType = ScenarioType.market_expansion
    description: str = ""
    target_regions: list[RegionGroup] = field(default_factory=list)
    data_types: list[str] = field(default_factory=list)
    ai_features: bool = False
    health_data: bool = False
    payment_data: bool = False


@dataclass
class ComplianceRequirementSet:
    """Set of compliance requirements for a scenario."""

    scenario_id: UUID = field(default_factory=uuid4)
    applicable_frameworks: list[str] = field(default_factory=list)
    total_requirements: int = 0
    estimated_effort_hours: float = 0.0
    estimated_cost_usd: float = 0.0
    priority_actions: list[dict] = field(default_factory=list)
    timeline_months: int = 0


@dataclass
class PlanningReport:
    """A complete planning report for a scenario."""

    id: UUID = field(default_factory=uuid4)
    scenario: PlanningScenario = field(default_factory=PlanningScenario)
    requirements: ComplianceRequirementSet = field(default_factory=ComplianceRequirementSet)
    risk_assessment: str = ""
    recommendations: list[str] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass
class PlannerStats:
    """Aggregate planner statistics."""

    total_scenarios: int = 0
    by_type: dict = field(default_factory=dict)
    by_region: dict = field(default_factory=dict)
    avg_frameworks_per_scenario: float = 0.0
