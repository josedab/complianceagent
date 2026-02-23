"""Compliance Copilot IDE Extension models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class DiagnosticSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class QuickFixType(str, Enum):
    CODE_REPLACE = "code_replace"
    CODE_INSERT = "code_insert"
    CONFIG_ADD = "config_add"
    SUPPRESS = "suppress"


@dataclass
class ComplianceDiagnostic:
    id: UUID = field(default_factory=uuid4)
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    col_start: int = 0
    col_end: int = 0
    rule_id: str = ""
    framework: str = ""
    article_ref: str = ""
    severity: DiagnosticSeverity = DiagnosticSeverity.WARNING
    message: str = ""
    quick_fixes: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RegulationTooltip:
    regulation: str = ""
    article: str = ""
    title: str = ""
    summary: str = ""
    url: str = ""
    obligation_level: str = "must"
    related_code_patterns: list[str] = field(default_factory=list)


@dataclass
class PostureSidebar:
    file_path: str = ""
    file_score: float = 100.0
    file_grade: str = "A"
    violations: int = 0
    frameworks_affected: list[str] = field(default_factory=list)
    last_scan_at: datetime | None = None
    repo_score: float = 85.0
    repo_grade: str = "B+"


@dataclass
class IDEQuickFix:
    id: UUID = field(default_factory=uuid4)
    diagnostic_id: UUID = field(default_factory=uuid4)
    fix_type: QuickFixType = QuickFixType.CODE_REPLACE
    title: str = ""
    description: str = ""
    replacement_code: str = ""
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    confidence: float = 0.0
    framework: str = ""
    article_ref: str = ""


@dataclass
class ExtensionStats:
    active_sessions: int = 0
    diagnostics_shown: int = 0
    quick_fixes_applied: int = 0
    tooltips_displayed: int = 0
    files_analyzed: int = 0
