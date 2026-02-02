"""Portfolio data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class RiskLevel(str, Enum):
    """Risk level classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class TrendDirection(str, Enum):
    """Direction of compliance trend."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


@dataclass
class RepositoryRiskProfile:
    """Risk profile for a single repository."""
    repository_id: UUID
    repository_name: str
    repository_url: str | None = None
    
    # Compliance metrics
    compliance_score: float = 0.0
    compliance_grade: str = "F"
    risk_level: RiskLevel = RiskLevel.MEDIUM
    
    # Gap counts
    total_requirements: int = 0
    compliant_requirements: int = 0
    critical_gaps: int = 0
    major_gaps: int = 0
    minor_gaps: int = 0
    
    # Framework breakdown
    framework_scores: dict[str, float] = field(default_factory=dict)
    
    # Trend
    score_change_7d: float = 0.0
    score_change_30d: float = 0.0
    trend: TrendDirection = TrendDirection.STABLE
    
    # Metadata
    last_scanned: datetime | None = None
    next_deadline: datetime | None = None
    days_until_deadline: int | None = None


@dataclass
class FrameworkAggregation:
    """Aggregated metrics for a framework across portfolio."""
    framework: str
    average_score: float
    min_score: float
    max_score: float
    repositories_count: int
    compliant_repos: int
    at_risk_repos: int
    total_gaps: int


@dataclass
class PortfolioSummary:
    """Summary statistics for a portfolio."""
    portfolio_id: UUID
    portfolio_name: str
    
    # Aggregate metrics
    total_repositories: int = 0
    average_compliance_score: float = 0.0
    weighted_compliance_score: float = 0.0
    overall_risk_level: RiskLevel = RiskLevel.MEDIUM
    
    # Repository distribution
    repos_grade_a: int = 0
    repos_grade_b: int = 0
    repos_grade_c: int = 0
    repos_grade_d: int = 0
    repos_grade_f: int = 0
    
    # Risk distribution
    repos_critical_risk: int = 0
    repos_high_risk: int = 0
    repos_medium_risk: int = 0
    repos_low_risk: int = 0
    
    # Gap totals
    total_critical_gaps: int = 0
    total_major_gaps: int = 0
    total_minor_gaps: int = 0
    
    # Framework breakdown
    framework_aggregations: list[FrameworkAggregation] = field(default_factory=list)
    
    # Trend
    score_trend: TrendDirection = TrendDirection.STABLE
    score_change_7d: float = 0.0
    score_change_30d: float = 0.0
    
    # Action items
    repositories_needing_attention: list[UUID] = field(default_factory=list)
    upcoming_deadlines: list[dict] = field(default_factory=list)


@dataclass
class PortfolioTrend:
    """Historical trend data for portfolio."""
    date: datetime
    average_score: float
    total_repositories: int
    critical_gaps: int
    high_risk_repos: int


@dataclass
class Portfolio:
    """A collection of repositories for compliance tracking."""
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID | None = None
    name: str = ""
    description: str | None = None
    
    # Repository membership
    repository_ids: list[UUID] = field(default_factory=list)
    
    # Computed data
    summary: PortfolioSummary | None = None
    repository_profiles: list[RepositoryRiskProfile] = field(default_factory=list)
    
    # History
    trend_history: list[PortfolioTrend] = field(default_factory=list)
    
    # Settings
    alert_threshold_score: float = 70.0
    alert_on_critical_gaps: bool = True
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: UUID | None = None
    
    # Tags for grouping
    tags: list[str] = field(default_factory=list)


@dataclass
class CrossRepoAnalysis:
    """Analysis across repositories in a portfolio."""
    portfolio_id: UUID
    
    # Common gaps (gaps that appear in multiple repos)
    common_gaps: list[dict] = field(default_factory=list)
    
    # Shared dependencies with compliance issues
    shared_risky_dependencies: list[dict] = field(default_factory=list)
    
    # Framework coverage gaps
    framework_coverage: dict[str, dict] = field(default_factory=dict)
    
    # Recommendations
    portfolio_recommendations: list[str] = field(default_factory=list)
    
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
