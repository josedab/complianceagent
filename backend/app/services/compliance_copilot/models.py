"""AI Compliance Co-Pilot models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class CopilotActionType(str, Enum):
    ANALYZE = "analyze"
    FIX = "fix"
    EXPLAIN = "explain"
    NAVIGATE = "navigate"
    REVIEW = "review"


class FixStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    APPLIED = "applied"


class ViolationSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ComplianceViolation:
    id: UUID = field(default_factory=uuid4)
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    rule_id: str = ""
    framework: str = ""
    article_ref: str = ""
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    message: str = ""
    code_snippet: str = ""
    detected_at: datetime | None = None


@dataclass
class ProposedFix:
    id: UUID = field(default_factory=uuid4)
    violation_id: UUID = field(default_factory=uuid4)
    file_path: str = ""
    original_code: str = ""
    fixed_code: str = ""
    explanation: str = ""
    article_reference: str = ""
    confidence: float = 0.0
    status: FixStatus = FixStatus.PROPOSED
    created_at: datetime | None = None


@dataclass
class CopilotSession:
    id: UUID = field(default_factory=uuid4)
    repo: str = ""
    user_id: str = ""
    actions: list[dict[str, Any]] = field(default_factory=list)
    violations_found: int = 0
    fixes_proposed: int = 0
    fixes_accepted: int = 0
    started_at: datetime | None = None
    last_active_at: datetime | None = None


@dataclass
class CodebaseAnalysis:
    repo: str = ""
    total_files: int = 0
    files_analyzed: int = 0
    violations: list[ComplianceViolation] = field(default_factory=list)
    score: float = 100.0
    frameworks_checked: list[str] = field(default_factory=list)
    analyzed_at: datetime | None = None


@dataclass
class RegulationExplanation:
    regulation: str = ""
    article: str = ""
    plain_language: str = ""
    technical_implications: list[str] = field(default_factory=list)
    code_examples: list[dict[str, str]] = field(default_factory=list)
    related_articles: list[str] = field(default_factory=list)
