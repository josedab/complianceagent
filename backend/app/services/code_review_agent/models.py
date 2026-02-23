"""Compliance-Aware Code Review Agent models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ReviewRiskLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SuggestionStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DISMISSED = "dismissed"


class ReviewDecision(str, Enum):
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    COMMENT = "comment"
    AUTO_APPROVED = "auto_approved"


@dataclass
class DiffHunk:
    file_path: str = ""
    start_line: int = 0
    end_line: int = 0
    added_lines: list[str] = field(default_factory=list)
    removed_lines: list[str] = field(default_factory=list)
    risk_level: ReviewRiskLevel = ReviewRiskLevel.NONE
    frameworks_affected: list[str] = field(default_factory=list)


@dataclass
class ComplianceSuggestion:
    id: UUID = field(default_factory=uuid4)
    file_path: str = ""
    line_number: int = 0
    rule_id: str = ""
    framework: str = ""
    article_ref: str = ""
    message: str = ""
    suggested_code: str = ""
    risk_level: ReviewRiskLevel = ReviewRiskLevel.MEDIUM
    status: SuggestionStatus = SuggestionStatus.PENDING
    created_at: datetime | None = None


@dataclass
class PRComplianceReview:
    id: UUID = field(default_factory=uuid4)
    repo: str = ""
    pr_number: int = 0
    commit_sha: str = ""
    overall_risk: ReviewRiskLevel = ReviewRiskLevel.NONE
    decision: ReviewDecision = ReviewDecision.COMMENT
    suggestions: list[ComplianceSuggestion] = field(default_factory=list)
    files_analyzed: int = 0
    hunks_analyzed: int = 0
    compliance_score_before: float = 100.0
    compliance_score_after: float = 100.0
    auto_approve_eligible: bool = False
    review_time_ms: float = 0.0
    created_at: datetime | None = None


@dataclass
class ReviewConfig:
    auto_approve_low_risk: bool = True
    frameworks: list[str] = field(default_factory=lambda: ["GDPR", "HIPAA", "PCI-DSS", "SOC2"])
    min_risk_for_block: ReviewRiskLevel = ReviewRiskLevel.HIGH
    suggestion_threshold: float = 0.7
    max_suggestions_per_pr: int = 20


@dataclass
class ReviewStats:
    total_reviews: int = 0
    auto_approved: int = 0
    suggestions_made: int = 0
    suggestions_accepted: int = 0
    acceptance_rate: float = 0.0
    avg_review_time_ms: float = 0.0
    by_risk_level: dict[str, int] = field(default_factory=dict)
