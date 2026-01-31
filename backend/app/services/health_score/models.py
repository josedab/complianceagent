"""Data models for Compliance Health Score API."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ScoreCategory(str, Enum):
    """Categories that contribute to health score."""
    
    REGULATORY_COVERAGE = "regulatory_coverage"
    CONTROL_IMPLEMENTATION = "control_implementation"
    EVIDENCE_FRESHNESS = "evidence_freshness"
    ISSUE_MANAGEMENT = "issue_management"
    SECURITY_POSTURE = "security_posture"
    POLICY_COMPLIANCE = "policy_compliance"


class ScoreGrade(str, Enum):
    """Grade interpretation of numeric scores."""
    
    A_PLUS = "A+"
    A = "A"
    A_MINUS = "A-"
    B_PLUS = "B+"
    B = "B"
    B_MINUS = "B-"
    C_PLUS = "C+"
    C = "C"
    C_MINUS = "C-"
    D = "D"
    F = "F"


class BadgeStyle(str, Enum):
    """Available badge visual styles."""
    
    FLAT = "flat"
    FLAT_SQUARE = "flat-square"
    PLASTIC = "plastic"
    FOR_THE_BADGE = "for-the-badge"
    SOCIAL = "social"


class TrendDirection(str, Enum):
    """Trend direction for score changes."""
    
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


@dataclass
class CategoryScore:
    """Score for a specific compliance category."""
    
    category: ScoreCategory
    score: float  # 0-100
    weight: float  # Contribution weight (0-1)
    details: dict = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    
    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


@dataclass
class HealthScore:
    """Comprehensive compliance health score."""
    
    id: UUID
    repository_id: UUID
    overall_score: float  # 0-100
    grade: ScoreGrade
    category_scores: dict[str, CategoryScore]
    calculated_at: datetime
    
    trend: TrendDirection = TrendDirection.STABLE
    trend_delta: float = 0.0
    previous_score: float | None = None
    
    regulations_checked: list[str] = field(default_factory=list)
    total_controls: int = 0
    passing_controls: int = 0
    failing_controls: int = 0
    not_applicable_controls: int = 0
    
    critical_findings: list[dict] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class ScoreHistory:
    """Historical score record."""
    
    id: UUID
    repository_id: UUID
    score: float
    grade: ScoreGrade
    recorded_at: datetime
    metadata: dict = field(default_factory=dict)


@dataclass
class BadgeConfig:
    """Configuration for generating compliance badges."""
    
    repository_id: UUID
    style: BadgeStyle = BadgeStyle.FLAT
    show_grade: bool = True
    show_score: bool = True
    label: str = "compliance"
    label_color: str = "555"
    cache_seconds: int = 3600
    
    include_regulations: list[str] | None = None
    custom_colors: dict[str, str] | None = None


@dataclass
class Badge:
    """Generated badge output."""
    
    repository_id: UUID
    score: float
    grade: ScoreGrade
    svg_content: str
    url: str
    markdown: str
    html: str
    generated_at: datetime


@dataclass
class CICDIntegration:
    """CI/CD integration configuration."""
    
    id: UUID
    repository_id: UUID
    platform: str  # github_actions, gitlab_ci, jenkins, circleci, azure_devops
    
    fail_threshold: float = 70.0
    warn_threshold: float = 85.0
    
    block_on_failure: bool = False
    comment_on_pr: bool = True
    update_status_check: bool = True
    
    regulations_required: list[str] = field(default_factory=list)
    
    webhook_url: str | None = None
    api_token_hash: str | None = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CICDResult:
    """Result of CI/CD compliance check."""
    
    id: UUID
    integration_id: UUID
    repository_id: UUID
    
    score: float
    grade: ScoreGrade
    passed: bool
    
    commit_sha: str
    branch: str
    pr_number: int | None = None
    
    summary: str = ""
    details: dict = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.utcnow)


# Default scoring weights
DEFAULT_WEIGHTS: dict[ScoreCategory, float] = {
    ScoreCategory.REGULATORY_COVERAGE: 0.20,
    ScoreCategory.CONTROL_IMPLEMENTATION: 0.30,
    ScoreCategory.EVIDENCE_FRESHNESS: 0.15,
    ScoreCategory.ISSUE_MANAGEMENT: 0.15,
    ScoreCategory.SECURITY_POSTURE: 0.15,
    ScoreCategory.POLICY_COMPLIANCE: 0.05,
}


# Grade thresholds
GRADE_THRESHOLDS: list[tuple[float, ScoreGrade]] = [
    (97, ScoreGrade.A_PLUS),
    (93, ScoreGrade.A),
    (90, ScoreGrade.A_MINUS),
    (87, ScoreGrade.B_PLUS),
    (83, ScoreGrade.B),
    (80, ScoreGrade.B_MINUS),
    (77, ScoreGrade.C_PLUS),
    (73, ScoreGrade.C),
    (70, ScoreGrade.C_MINUS),
    (60, ScoreGrade.D),
    (0, ScoreGrade.F),
]


# Badge color scheme based on score
BADGE_COLORS: dict[str, str] = {
    "excellent": "brightgreen",  # 90+
    "good": "green",  # 80-89
    "fair": "yellow",  # 70-79
    "poor": "orange",  # 60-69
    "critical": "red",  # <60
}


def score_to_grade(score: float) -> ScoreGrade:
    """Convert numeric score to letter grade."""
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return ScoreGrade.F


def score_to_color(score: float) -> str:
    """Get badge color for score."""
    if score >= 90:
        return BADGE_COLORS["excellent"]
    elif score >= 80:
        return BADGE_COLORS["good"]
    elif score >= 70:
        return BADGE_COLORS["fair"]
    elif score >= 60:
        return BADGE_COLORS["poor"]
    return BADGE_COLORS["critical"]
