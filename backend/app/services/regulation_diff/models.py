"""Regulation Changelog Diff Viewer models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ChangeSeverity(str, Enum):
    """Severity of a regulation change."""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    CLARIFICATION = "clarification"


class ChangeType(str, Enum):
    """Type of regulatory change."""

    ADDITION = "addition"
    DELETION = "deletion"
    MODIFICATION = "modification"
    RENUMBERING = "renumbering"


@dataclass
class RegulationVersion:
    """A version of a regulation."""

    id: str
    regulation: str
    version: str
    title: str
    effective_date: datetime
    published_date: datetime = field(default_factory=datetime.utcnow)
    total_articles: int = 0
    total_words: int = 0
    source_url: str = ""
    hash: str = ""


@dataclass
class RegulationDiff:
    """A diff between two regulation versions."""

    id: str
    regulation: str
    from_version: str
    to_version: str
    total_changes: int = 0
    critical_changes: int = 0
    articles_added: int = 0
    articles_removed: int = 0
    articles_modified: int = 0
    ai_summary: str = ""
    impact_assessment: str = ""
    changes: list[ArticleChange] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ArticleChange:
    """A change to a specific article/section."""

    article: str
    section: str
    change_type: ChangeType
    severity: ChangeSeverity
    old_text: str = ""
    new_text: str = ""
    summary: str = ""
    impact_on_code: str = ""
    affected_controls: list[str] = field(default_factory=list)
