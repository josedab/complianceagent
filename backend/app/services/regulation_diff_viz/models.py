"""Regulation Diff Visualizer models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class DiffChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class ImpactLevel(str, Enum):
    BREAKING = "breaking"
    SIGNIFICANT = "significant"
    MINOR = "minor"
    COSMETIC = "cosmetic"


@dataclass
class RegulationVersion:
    id: UUID = field(default_factory=uuid4)
    regulation: str = ""
    version: str = ""
    effective_date: str = ""
    sections: list[dict[str, Any]] = field(default_factory=list)
    published_at: datetime | None = None


@dataclass
class DiffSection:
    section_id: str = ""
    title: str = ""
    change_type: DiffChangeType = DiffChangeType.UNCHANGED
    old_text: str = ""
    new_text: str = ""
    impact_level: ImpactLevel = ImpactLevel.MINOR
    affected_code_areas: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class RegulationDiffResult:
    id: UUID = field(default_factory=uuid4)
    regulation: str = ""
    old_version: str = ""
    new_version: str = ""
    total_sections: int = 0
    changed_sections: int = 0
    sections: list[DiffSection] = field(default_factory=list)
    impact_summary: dict[str, int] = field(default_factory=dict)
    affected_repositories: list[str] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass
class DiffAnnotation:
    id: UUID = field(default_factory=uuid4)
    diff_id: UUID = field(default_factory=uuid4)
    section_id: str = ""
    author: str = ""
    comment: str = ""
    action_required: bool = False
    created_at: datetime | None = None
