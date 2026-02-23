"""ESG Sustainability models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ESGFramework(str, Enum):
    """ESG reporting frameworks."""

    CSRD = "csrd"
    TCFD = "tcfd"
    GRI = "gri"
    SDG = "sdg"
    SEC_CLIMATE = "sec_climate"


class ESGCategory(str, Enum):
    """ESG metric categories."""

    ENVIRONMENTAL = "environmental"
    SOCIAL = "social"
    GOVERNANCE = "governance"


class EmissionScope(str, Enum):
    """Greenhouse gas emission scopes."""

    SCOPE_1 = "scope_1"
    SCOPE_2 = "scope_2"
    SCOPE_3 = "scope_3"


@dataclass
class ESGMetric:
    """An ESG performance metric."""

    id: UUID = field(default_factory=uuid4)
    category: ESGCategory = ESGCategory.ENVIRONMENTAL
    framework: ESGFramework = ESGFramework.GRI
    metric_name: str = ""
    value: float = 0.0
    unit: str = ""
    period: str = ""
    target: float | None = None
    on_track: bool = True


@dataclass
class CarbonFootprint:
    """Carbon emissions footprint data."""

    total_emissions_tons: float = 0.0
    by_scope: dict[str, float] = field(default_factory=dict)
    by_source: dict[str, float] = field(default_factory=dict)
    reduction_target_pct: float = 0.0
    reduction_achieved_pct: float = 0.0
    reporting_period: str = ""


@dataclass
class ESGReport:
    """A generated ESG report."""

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    frameworks: list[ESGFramework] = field(default_factory=list)
    metrics: list[ESGMetric] = field(default_factory=list)
    carbon_footprint: CarbonFootprint | None = None
    highlights: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass
class ESGStats:
    """Statistics for the ESG sustainability service."""

    total_metrics: int = 0
    frameworks_tracked: int = 0
    by_category: dict = field(default_factory=dict)
    carbon_tracked: bool = False
    reports_generated: int = 0
