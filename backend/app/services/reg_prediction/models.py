"""Regulatory Impact Prediction models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class PredictionConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SPECULATIVE = "speculative"


class SignalType(str, Enum):
    LEGISLATIVE = "legislative"
    ENFORCEMENT = "enforcement"
    CONSULTATION = "consultation"
    AMENDMENT = "amendment"
    GUIDANCE = "guidance"
    COMMITTEE_ACTIVITY = "committee_activity"
    COURT_RULING = "court_ruling"
    INDUSTRY_STANDARD = "industry_standard"
    GLOBAL_PRECEDENT = "global_precedent"


class ImpactSeverity(str, Enum):
    TRANSFORMATIVE = "transformative"
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"


class MomentumIndicator(str, Enum):
    """NLP-extracted regulatory momentum indicators."""
    ACCELERATING = "accelerating"
    STEADY = "steady"
    DECELERATING = "decelerating"
    STALLED = "stalled"
    REVERSED = "reversed"


class PredictionStatus(str, Enum):
    ACTIVE = "active"
    VERIFIED_CORRECT = "verified_correct"
    VERIFIED_INCORRECT = "verified_incorrect"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


@dataclass
class RegulatorySignal:
    id: UUID = field(default_factory=uuid4)
    signal_type: SignalType = SignalType.LEGISLATIVE
    source: str = ""
    jurisdiction: str = ""
    title: str = ""
    summary: str = ""
    url: str = ""
    detected_at: datetime | None = None
    relevance_score: float = 0.0
    # NLP-extracted metadata
    entities: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    sentiment: float = 0.0  # -1.0 to 1.0
    momentum: MomentumIndicator = MomentumIndicator.STEADY


@dataclass
class LegislativeActivity:
    """Tracked legislative committee activity."""
    id: UUID = field(default_factory=uuid4)
    committee: str = ""
    jurisdiction: str = ""
    activity_type: str = ""  # hearing, markup, vote, report
    title: str = ""
    date: datetime | None = None
    related_bills: list[str] = field(default_factory=list)
    participants: list[str] = field(default_factory=list)
    outcome: str = ""
    signal_strength: float = 0.0


@dataclass
class GlobalPrecedent:
    """Cross-jurisdiction regulatory precedent."""
    id: UUID = field(default_factory=uuid4)
    origin_jurisdiction: str = ""
    regulation_name: str = ""
    adopted_by: list[str] = field(default_factory=list)
    adoption_lag_months: float = 0.0
    adaptation_level: str = "direct"  # direct, modified, inspired
    key_differences: list[str] = field(default_factory=list)


@dataclass
class TimeSeriesPrediction:
    """Time-series prediction with confidence intervals."""
    prediction_date: str = ""
    value: float = 0.0
    lower_bound: float = 0.0
    upper_bound: float = 0.0
    confidence_level: float = 0.95


@dataclass
class RegPrediction:
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    jurisdiction: str = ""
    affected_frameworks: list[str] = field(default_factory=list)
    confidence: PredictionConfidence = PredictionConfidence.MEDIUM
    confidence_score: float = 0.0
    impact_severity: ImpactSeverity = ImpactSeverity.MODERATE
    predicted_effective_date: str = ""
    prediction_horizon_months: int = 6
    supporting_signals: list[str] = field(default_factory=list)
    preparation_tasks: list[dict[str, Any]] = field(default_factory=list)
    predicted_at: datetime | None = None
    # ML pipeline fields
    status: PredictionStatus = PredictionStatus.ACTIVE
    momentum: MomentumIndicator = MomentumIndicator.STEADY
    time_series: list[TimeSeriesPrediction] = field(default_factory=list)
    global_precedents: list[str] = field(default_factory=list)
    signal_ids: list[UUID] = field(default_factory=list)
    model_version: str = "v1.0"
    feature_importance: dict[str, float] = field(default_factory=dict)


@dataclass
class EarlyWarning:
    id: UUID = field(default_factory=uuid4)
    prediction_id: UUID = field(default_factory=uuid4)
    title: str = ""
    urgency: str = "medium"
    days_until_predicted: int = 180
    recommended_actions: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    momentum: MomentumIndicator = MomentumIndicator.STEADY
    confidence_trend: str = ""  # rising, stable, falling


@dataclass
class PredictionAccuracy:
    total_predictions: int = 0
    verified_correct: int = 0
    verified_incorrect: int = 0
    pending_verification: int = 0
    accuracy_rate: float = 0.0
    avg_lead_time_months: float = 0.0
    precision_by_confidence: dict[str, float] = field(default_factory=dict)
    model_version: str = "v1.0"
