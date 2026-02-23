"""Compliance Badge & Scorecard models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class BadgeStyle(str, Enum):
    FLAT = "flat"
    FLAT_SQUARE = "flat-square"
    PLASTIC = "plastic"
    FOR_THE_BADGE = "for-the-badge"


class Grade(str, Enum):
    A_PLUS = "A+"
    A = "A"
    A_MINUS = "A-"
    B_PLUS = "B+"
    B = "B"
    B_MINUS = "B-"
    C_PLUS = "C+"
    C = "C"
    D = "D"
    F = "F"


@dataclass
class BadgeConfig:
    repo: str = ""
    style: BadgeStyle = BadgeStyle.FLAT
    label: str = "compliance"
    color_thresholds: dict[str, str] = field(
        default_factory=lambda: {"A": "brightgreen", "B": "green", "C": "yellow", "D": "orange", "F": "red"}
    )


@dataclass
class BadgeData:
    repo: str = ""
    grade: Grade = Grade.B
    score: float = 80.0
    label: str = "compliance"
    color: str = "green"
    style: BadgeStyle = BadgeStyle.FLAT
    svg: str = ""
    generated_at: datetime | None = None
    cache_ttl_seconds: int = 300


@dataclass
class PublicScorecard:
    id: UUID = field(default_factory=uuid4)
    repo: str = ""
    overall_score: float = 0.0
    overall_grade: Grade = Grade.B
    frameworks: list[dict[str, Any]] = field(default_factory=list)
    trend: list[dict[str, Any]] = field(default_factory=list)
    last_scan_at: datetime | None = None
    generated_at: datetime | None = None
    is_public: bool = True


@dataclass
class EmbedSnippet:
    format: str = "markdown"
    code: str = ""
    preview_url: str = ""
