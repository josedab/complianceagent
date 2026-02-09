"""Compliance Health Score Benchmarking models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ComplianceGrade(str, Enum):
    A_PLUS = "A+"
    A = "A"
    A_MINUS = "A-"
    B_PLUS = "B+"
    B = "B"
    B_MINUS = "B-"
    C_PLUS = "C+"
    C = "C"
    D = "D"
    F = "F"


class CompanySize(str, Enum):
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


@dataclass
class HealthScore:
    """Organization compliance health score with multi-dimensional breakdown."""
    id: UUID = field(default_factory=uuid4)
    org_id: str = ""
    overall_score: float = 0.0
    grade: ComplianceGrade = ComplianceGrade.C
    dimensions: dict[str, float] = field(default_factory=dict)
    framework_scores: dict[str, float] = field(default_factory=dict)
    percentile: float = 0.0
    peer_group: str = ""
    computed_at: datetime | None = None


@dataclass
class PeerBenchmark:
    """Aggregated benchmark data for a peer group."""
    peer_group: str = ""
    company_size: CompanySize = CompanySize.MEDIUM
    industry: str = ""
    sample_size: int = 0
    avg_score: float = 0.0
    median_score: float = 0.0
    p25: float = 0.0
    p50: float = 0.0
    p75: float = 0.0
    p90: float = 0.0
    grade_distribution: dict[str, int] = field(default_factory=dict)
    top_gaps: list[str] = field(default_factory=list)


@dataclass
class ImprovementSuggestion:
    """Actionable suggestion to improve a specific compliance dimension."""
    dimension: str = ""
    current_score: float = 0.0
    target_score: float = 0.0
    impact_on_grade: str = ""
    effort: str = ""  # low, medium, high
    actions: list[str] = field(default_factory=list)


@dataclass
class BenchmarkComparison:
    """Side-by-side comparison of org score vs peer benchmark."""
    org_score: HealthScore = field(default_factory=HealthScore)
    benchmark: PeerBenchmark = field(default_factory=PeerBenchmark)
    rank_position: int = 0
    total_in_group: int = 0
    gap_to_median: float = 0.0
    gap_to_p75: float = 0.0
    improvement_suggestions: list[ImprovementSuggestion] = field(default_factory=list)


@dataclass
class ScoreHistory:
    """Historical health scores with trend analysis."""
    scores: list[HealthScore] = field(default_factory=list)
    trend_direction: str = ""  # up, down, stable
    trend_pct: float = 0.0
    period_days: int = 90


@dataclass
class BoardReport:
    """Executive board-ready compliance health report."""
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    org_score: HealthScore = field(default_factory=HealthScore)
    benchmark: PeerBenchmark = field(default_factory=PeerBenchmark)
    highlights: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    generated_at: datetime | None = None
    format: str = "pdf"


@dataclass
class LeaderboardEntry:
    """Anonymized leaderboard entry for peer comparison."""
    rank: int = 0
    org_name_anonymized: str = ""
    industry: str = ""
    score: float = 0.0
    grade: ComplianceGrade = ComplianceGrade.C
    trend: str = ""  # up, down, stable
