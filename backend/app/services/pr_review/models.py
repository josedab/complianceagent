"""Data models for PR Review service."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class ViolationSeverity(str, Enum):
    """Severity levels for compliance violations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ReviewStatus(str, Enum):
    """Status of a PR review."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AutoFixStatus(str, Enum):
    """Status of an auto-fix."""
    GENERATED = "generated"
    APPLIED = "applied"
    REJECTED = "rejected"
    PENDING_REVIEW = "pending_review"


@dataclass
class FileDiff:
    """Represents a file diff from a PR."""
    path: str
    old_path: str | None
    status: str  # added, modified, deleted, renamed
    additions: int
    deletions: int
    patch: str
    content: str | None = None
    language: str | None = None


@dataclass
class ComplianceViolation:
    """A compliance violation found in code."""
    id: UUID = field(default_factory=uuid4)
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    column_start: int = 0
    column_end: int = 0
    code: str = ""
    message: str = ""
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    regulation: str | None = None
    article_reference: str | None = None
    category: str | None = None
    suggestion: str | None = None
    evidence: str | None = None
    confidence: float = 0.0
    detected_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReviewComment:
    """A review comment to be posted on a PR."""
    id: UUID = field(default_factory=uuid4)
    violation: ComplianceViolation | None = None
    file_path: str = ""
    line: int = 0
    side: str = "RIGHT"
    body: str = ""
    in_reply_to: int | None = None
    position: int | None = None


@dataclass
class AutoFix:
    """An auto-generated fix for a compliance violation."""
    id: UUID = field(default_factory=uuid4)
    violation_id: UUID | None = None
    file_path: str = ""
    original_code: str = ""
    fixed_code: str = ""
    diff: str = ""
    description: str = ""
    confidence: float = 0.0
    status: AutoFixStatus = AutoFixStatus.GENERATED
    generated_at: datetime = field(default_factory=datetime.utcnow)
    applied_at: datetime | None = None
    commit_sha: str | None = None
    tests_generated: list[str] = field(default_factory=list)


@dataclass
class PRAnalysisResult:
    """Result of analyzing a PR for compliance issues."""
    id: UUID = field(default_factory=uuid4)
    pr_number: int = 0
    repository: str = ""
    owner: str = ""
    base_sha: str = ""
    head_sha: str = ""
    files_analyzed: int = 0
    total_additions: int = 0
    total_deletions: int = 0
    violations: list[ComplianceViolation] = field(default_factory=list)
    files: list[FileDiff] = field(default_factory=list)
    regulations_checked: list[str] = field(default_factory=list)
    analysis_time_ms: float = 0.0
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def critical_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == ViolationSeverity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == ViolationSeverity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == ViolationSeverity.MEDIUM)

    @property
    def low_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == ViolationSeverity.LOW)

    @property
    def passed(self) -> bool:
        return self.critical_count == 0 and self.high_count == 0


@dataclass
class PRReviewResult:
    """Result of a complete PR compliance review."""
    id: UUID = field(default_factory=uuid4)
    analysis: PRAnalysisResult | None = None
    comments: list[ReviewComment] = field(default_factory=list)
    auto_fixes: list[AutoFix] = field(default_factory=list)
    status: ReviewStatus = ReviewStatus.COMPLETED
    summary: str = ""
    recommendation: str = ""  # approve, request_changes, comment
    reviewed_at: datetime = field(default_factory=datetime.utcnow)
    review_time_ms: float = 0.0
    gh_review_id: int | None = None

    @property
    def fixable_violations_count(self) -> int:
        return len(self.auto_fixes)

    @property
    def total_violations_count(self) -> int:
        return len(self.analysis.violations) if self.analysis else 0
