"""Cross-Organization Compliance Benchmarking models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class Industry(str, Enum):
    FINTECH = "fintech"
    HEALTHTECH = "healthtech"
    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    INSURTECH = "insurtech"
    EDTECH = "edtech"
    AI_ML = "ai_ml"
    GOVERNMENT = "government"


class OrgSize(str, Enum):
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class PrivacyLevel(str, Enum):
    STRICT = "strict"
    STANDARD = "standard"
    RELAXED = "relaxed"


class ImprovementPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class DifferentialPrivacyConfig:
    """Configuration for differential privacy Laplace noise mechanism."""
    epsilon: float = 1.0
    delta: float = 1e-5
    sensitivity: float = 1.0
    noise_mechanism: str = "laplace"
    min_group_size: int = 50


@dataclass
class AnonymizedProfile:
    id: UUID = field(default_factory=uuid4)
    industry: Industry = Industry.SAAS
    org_size: OrgSize = OrgSize.MEDIUM
    frameworks: list[str] = field(default_factory=list)
    overall_score: float = 0.0
    framework_scores: dict[str, float] = field(default_factory=dict)
    privacy_level: PrivacyLevel = PrivacyLevel.STANDARD
    contributed_at: datetime | None = None


@dataclass
class BenchmarkSubmission:
    """Anonymized benchmark data submission from an organization."""
    id: UUID = field(default_factory=uuid4)
    industry: Industry = Industry.SAAS
    org_size: OrgSize = OrgSize.MEDIUM
    frameworks: list[str] = field(default_factory=list)
    overall_score: float = 0.0
    framework_scores: dict[str, float] = field(default_factory=dict)
    control_area_scores: dict[str, float] = field(default_factory=dict)
    privacy_config: DifferentialPrivacyConfig = field(default_factory=DifferentialPrivacyConfig)
    noised_score: float = 0.0
    submitted_at: datetime | None = None


@dataclass
class PercentileRanking:
    """Percentile rankings across multiple dimensions."""
    overall_percentile: float = 0.0
    industry_percentile: float = 0.0
    size_percentile: float = 0.0
    framework_percentiles: dict[str, float] = field(default_factory=dict)
    control_area_percentiles: dict[str, float] = field(default_factory=dict)
    peer_group_percentile: float = 0.0
    sample_sizes: dict[str, int] = field(default_factory=dict)
    is_statistically_significant: bool = False


@dataclass
class PeerGroup:
    """Definition of a peer group for 'companies like you' comparison."""
    id: UUID = field(default_factory=uuid4)
    industry: Industry = Industry.SAAS
    org_size: OrgSize = OrgSize.MEDIUM
    frameworks: list[str] = field(default_factory=list)
    peer_count: int = 0
    avg_score: float = 0.0
    median_score: float = 0.0
    top_quartile_score: float = 0.0
    bottom_quartile_score: float = 0.0
    score_std_dev: float = 0.0
    meets_minimum_threshold: bool = False


@dataclass
class PeerRecommendation:
    """Anonymized recommendation derived from peer group analysis."""
    area: str = ""
    priority: ImprovementPriority = ImprovementPriority.MEDIUM
    your_score: float = 0.0
    peer_avg_score: float = 0.0
    gap: float = 0.0
    recommendation: str = ""
    peer_adoption_rate: float = 0.0


@dataclass
class InsightsDashboard:
    """Aggregated insights dashboard with improvement priorities."""
    org_score: float = 0.0
    rankings: PercentileRanking = field(default_factory=PercentileRanking)
    peer_group: PeerGroup = field(default_factory=PeerGroup)
    improvement_priorities: list[PeerRecommendation] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    peer_recommendations: list[PeerRecommendation] = field(default_factory=list)
    benchmark_summary: str = ""
    data_quality_warning: str | None = None
    generated_at: datetime | None = None


@dataclass
class BenchmarkResult:
    id: UUID = field(default_factory=uuid4)
    industry: Industry = Industry.SAAS
    org_size: OrgSize = OrgSize.MEDIUM
    your_score: float = 0.0
    percentile: float = 0.0
    industry_avg: float = 0.0
    industry_median: float = 0.0
    top_quartile: float = 0.0
    peer_count: int = 0
    framework_comparisons: list[dict[str, Any]] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass
class BenchmarkTrend:
    period: str = "30d"
    data_points: list[dict[str, Any]] = field(default_factory=list)
    your_trend: str = "improving"
    industry_trend: str = "stable"


@dataclass
class BenchmarkStats:
    total_participants: int = 0
    by_industry: dict[str, int] = field(default_factory=dict)
    by_size: dict[str, int] = field(default_factory=dict)
    global_avg_score: float = 0.0
    data_freshness_hours: float = 0.0
