"""Regulatory Horizon Scanner models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class LegislativeStatus(str, Enum):
    DRAFT = "draft"
    PROPOSED = "proposed"
    COMMITTEE = "committee"
    PASSED_ONE_CHAMBER = "passed_one_chamber"
    PASSED = "passed"
    ENACTED = "enacted"
    EFFECTIVE = "effective"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImpactSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LegislativeSource(str, Enum):
    CONGRESS_GOV = "congress_gov"
    EUR_LEX = "eur_lex"
    SEC_EDGAR = "sec_edgar"
    FCA_UK = "fca_uk"
    ICO_UK = "ico_uk"
    EDPB = "edpb"
    NIST = "nist"
    ISO = "iso"
    CUSTOM = "custom"


@dataclass
class PendingLegislation:
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    summary: str = ""
    source: LegislativeSource = LegislativeSource.CUSTOM
    source_url: str = ""
    jurisdiction: str = ""
    status: LegislativeStatus = LegislativeStatus.DRAFT
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    expected_effective_date: datetime | None = None
    discovered_at: datetime | None = None
    frameworks_affected: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class CodebaseImpactPrediction:
    id: UUID = field(default_factory=uuid4)
    legislation_id: UUID | None = None
    affected_files: int = 0
    affected_modules: list[str] = field(default_factory=list)
    estimated_effort_days: float = 0.0
    impact_severity: ImpactSeverity = ImpactSeverity.MEDIUM
    requirements_preview: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    confidence_score: float = 0.0


@dataclass
class HorizonAlert:
    id: UUID = field(default_factory=uuid4)
    legislation_id: UUID | None = None
    title: str = ""
    message: str = ""
    severity: ImpactSeverity = ImpactSeverity.MEDIUM
    months_until_effective: float = 0.0
    created_at: datetime | None = None


@dataclass
class HorizonTimeline:
    upcoming: list[PendingLegislation] = field(default_factory=list)
    alerts: list[HorizonAlert] = field(default_factory=list)
    total_tracked: int = 0
    high_impact_count: int = 0
