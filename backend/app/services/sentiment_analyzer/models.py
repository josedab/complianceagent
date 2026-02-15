"""Regulatory Change Sentiment Analyzer models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class EnforcementTrend(str, Enum):
    HEATING_UP = "heating_up"
    STABLE = "stable"
    COOLING_DOWN = "cooling_down"
    DORMANT = "dormant"
    EMERGING = "emerging"


class SentimentScore(str, Enum):
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


@dataclass
class RegulatorySentiment:
    """Sentiment analysis for a regulation in a jurisdiction."""

    id: UUID = field(default_factory=uuid4)
    regulation: str = ""
    jurisdiction: str = ""
    trend: EnforcementTrend = EnforcementTrend.STABLE
    sentiment: SentimentScore = SentimentScore.NEUTRAL
    enforcement_probability: float = 0.0
    avg_fine_amount: float = 0.0
    enforcement_count_ytd: int = 0
    key_topics: list[str] = field(default_factory=list)
    analyzed_at: datetime | None = None


@dataclass
class EnforcementAction:
    """A recorded enforcement action."""

    id: UUID = field(default_factory=uuid4)
    regulation: str = ""
    jurisdiction: str = ""
    entity_fined: str = ""
    fine_amount: float = 0.0
    violation_type: str = ""
    date: str = ""
    summary: str = ""


@dataclass
class RiskHeatmapCell:
    """A cell in the risk heatmap."""

    regulation: str = ""
    jurisdiction: str = ""
    risk_score: float = 0.0
    trend: EnforcementTrend = EnforcementTrend.STABLE
    color: str = ""


@dataclass
class PrioritizationRecommendation:
    """A prioritization recommendation."""

    regulation: str = ""
    priority_rank: int = 0
    risk_score: float = 0.0
    effort_estimate: str = ""
    rationale: str = ""
    enforcement_likelihood: float = 0.0


@dataclass
class SentimentReport:
    """Overall sentiment analysis report."""

    total_regulations_analyzed: int = 0
    high_risk_count: int = 0
    heatmap: list[RiskHeatmapCell] = field(default_factory=list)
    top_priorities: list[PrioritizationRecommendation] = field(default_factory=list)
    generated_at: datetime | None = None
