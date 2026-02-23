"""Data models for Compliance Editor Service."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class EditorAction(str, Enum):
    """Actions available in the compliance editor."""

    OPEN = "open"
    SAVE = "save"
    APPLY_FIX = "apply_fix"
    RUN_DIAGNOSTIC = "run_diagnostic"
    HOVER_TOOLTIP = "hover_tooltip"


class FileLanguage(str, Enum):
    """Supported file languages."""

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    YAML = "yaml"


@dataclass
class EditorFile:
    """A file open in the compliance editor."""

    id: UUID = field(default_factory=uuid4)
    path: str = ""
    content: str = ""
    language: FileLanguage = FileLanguage.PYTHON
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    posture_score: float = 100.0
    last_saved_at: datetime | None = None


@dataclass
class EditorSession:
    """An active editor session."""

    id: UUID = field(default_factory=uuid4)
    user_id: str = ""
    files: list[EditorFile] = field(default_factory=list)
    active_file: str = ""
    total_diagnostics: int = 0
    fixes_applied: int = 0
    started_at: datetime | None = None


@dataclass
class InlineFix:
    """A suggested inline fix for a compliance issue."""

    id: UUID = field(default_factory=uuid4)
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    original_code: str = ""
    fixed_code: str = ""
    rule_id: str = ""
    framework: str = ""
    explanation: str = ""
    confidence: float = 0.0


@dataclass
class EditorStats:
    """Statistics for the compliance editor."""

    total_sessions: int = 0
    files_opened: int = 0
    diagnostics_shown: int = 0
    fixes_applied: int = 0
    avg_posture_score: float = 0.0
