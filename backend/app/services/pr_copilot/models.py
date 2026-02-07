"""Compliance Co-Pilot for PRs models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ReviewSeverity(str, Enum):
    """Compliance review finding severity."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ReviewStatus(str, Enum):
    """PR review status."""

    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class SuggestionAction(str, Enum):
    """Suggested action for a finding."""

    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    DEFERRED = "deferred"
    PENDING = "pending"


@dataclass
class ComplianceFinding:
    """A compliance finding in a PR."""

    id: UUID = field(default_factory=uuid4)
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    severity: ReviewSeverity = ReviewSeverity.MEDIUM
    regulation: str = ""
    article_ref: str = ""
    title: str = ""
    description: str = ""
    suggestion: str = ""
    suggested_code: str = ""
    confidence: float = 0.0


@dataclass
class PRReviewResult:
    """Result of a PR compliance review."""

    id: UUID = field(default_factory=uuid4)
    pr_number: int = 0
    repo: str = ""
    status: ReviewStatus = ReviewStatus.PENDING
    findings: list[ComplianceFinding] = field(default_factory=list)
    summary: str = ""
    risk_level: str = "low"
    labels: list[str] = field(default_factory=list)
    analysis_time_ms: float = 0.0
    analyzed_at: datetime | None = None

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == ReviewSeverity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == ReviewSeverity.HIGH)

    @property
    def should_block_merge(self) -> bool:
        return self.critical_count > 0


@dataclass
class SuggestionFeedback:
    """User feedback on a compliance suggestion."""

    finding_id: UUID = field(default_factory=uuid4)
    action: SuggestionAction = SuggestionAction.PENDING
    reason: str = ""
    user_id: str = ""
    recorded_at: datetime | None = None


@dataclass
class LearningStats:
    """Aggregated learning statistics for suggestion quality."""

    total_suggestions: int = 0
    accepted: int = 0
    dismissed: int = 0
    deferred: int = 0
    acceptance_rate: float = 0.0
    by_regulation: dict[str, dict] = field(default_factory=dict)
