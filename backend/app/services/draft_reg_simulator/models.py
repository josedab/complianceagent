"""Draft Regulation Impact Simulator models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class DraftStatus(str, Enum):
    PROPOSED = "proposed"
    COMMITTEE = "committee"
    FLOOR_VOTE = "floor_vote"
    ENACTED = "enacted"


class ImpactScope(str, Enum):
    NARROW = "narrow"
    MODERATE = "moderate"
    BROAD = "broad"
    TRANSFORMATIVE = "transformative"


@dataclass
class DraftRegulation:
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    jurisdiction: str = ""
    source_url: str = ""
    draft_text: str = ""
    status: DraftStatus = DraftStatus.PROPOSED
    effective_date_est: datetime | None = None
    sponsoring_body: str = ""


@dataclass
class ImpactAnalysis:
    id: UUID = field(default_factory=uuid4)
    draft_id: UUID | None = None
    affected_repos: list[str] = field(default_factory=list)
    affected_frameworks: list[str] = field(default_factory=list)
    code_changes_needed: int = 0
    estimated_effort_hours: float = 0.0
    impact_scope: ImpactScope = ImpactScope.NARROW
    preparation_tasks: list[str] = field(default_factory=list)
    risk_score: float = 0.0


@dataclass
class SimulationStats:
    total_drafts: int = 0
    by_status: dict[str, int] = field(default_factory=dict)
    by_jurisdiction: dict[str, int] = field(default_factory=dict)
    total_analyses: int = 0
    avg_effort_hours: float = 0.0
