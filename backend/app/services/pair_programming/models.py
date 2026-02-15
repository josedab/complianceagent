"""Real-Time Compliance Pair Programming models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from uuid import UUID


class SuggestionSeverity(str, Enum):
    """Severity of a compliance suggestion."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class SuggestionStatus(str, Enum):
    """Status of a suggestion."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    DEFERRED = "deferred"


@dataclass
class ComplianceSuggestion:
    """A real-time compliance suggestion during coding."""

    id: UUID
    file_path: str
    line_number: int
    severity: SuggestionSeverity
    status: SuggestionStatus = SuggestionStatus.PENDING
    rule_id: str = ""
    regulation: str = ""
    article: str = ""
    message: str = ""
    explanation: str = ""
    suggested_fix: str = ""
    original_code: str = ""
    confidence: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PairSession:
    """An active pair programming session."""

    id: UUID
    user_id: UUID
    repository: str
    active_file: str = ""
    language: str = "python"
    frameworks: list[str] = field(default_factory=list)
    suggestions_given: int = 0
    suggestions_accepted: int = 0
    violations_prevented: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RegulationContext:
    """Relevant regulation context for current coding session."""

    regulation: str
    article: str
    title: str
    summary: str
    relevance_score: float = 0.0
    applicable_patterns: list[str] = field(default_factory=list)


@dataclass
class MultiFileAnalysisResult:
    """Results from analyzing multiple files."""

    files_analyzed: int = 0
    total_suggestions: int = 0
    suggestions_by_file: dict[str, list[ComplianceSuggestion]] = field(default_factory=dict)
    cross_file_issues: list[dict[str, Any]] = field(default_factory=list)
    refactoring_opportunities: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RefactoringSuggestion:
    """A suggested multi-file refactoring for compliance."""

    id: UUID
    title: str
    description: str
    affected_files: list[str] = field(default_factory=list)
    regulation: str = ""
    article: str = ""
    effort_estimate: str = ""  # "low", "medium", "high"
    priority: int = 0  # 1-10
    suggested_approach: str = ""
