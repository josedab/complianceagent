"""Scoring data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ComplianceGrade(str, Enum):
    """Letter grade for compliance score."""
    A = "A"  # 90-100%
    B = "B"  # 80-89%
    C = "C"  # 70-79%
    D = "D"  # 60-69%
    F = "F"  # Below 60%

    @classmethod
    def from_score(cls, score: float) -> "ComplianceGrade":
        """Convert numeric score to letter grade."""
        if score >= 90:
            return cls.A
        elif score >= 80:
            return cls.B
        elif score >= 70:
            return cls.C
        elif score >= 60:
            return cls.D
        return cls.F


@dataclass
class GapDetail:
    """Details of a compliance gap."""
    framework: str
    requirement_id: str
    title: str
    severity: str  # critical, major, minor
    description: str
    affected_files: list[str] = field(default_factory=list)
    remediation_hint: str | None = None


@dataclass
class FrameworkScore:
    """Score for a single regulatory framework."""
    framework: str
    score: float
    grade: ComplianceGrade
    total_requirements: int
    compliant_requirements: int
    critical_gaps: int
    major_gaps: int
    minor_gaps: int
    gaps: list[GapDetail] = field(default_factory=list)


@dataclass
class ScoringResult:
    """Complete scoring result for a codebase."""
    overall_score: float
    overall_grade: ComplianceGrade
    framework_scores: list[FrameworkScore]
    total_requirements: int
    compliant_requirements: int
    total_gaps: int
    critical_gaps: int
    major_gaps: int
    minor_gaps: int
    top_gaps: list[GapDetail]
    badge_url: str | None = None
    badge_markdown: str | None = None
    scored_at: datetime = field(default_factory=datetime.utcnow)
    scan_duration_seconds: float = 0.0
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
