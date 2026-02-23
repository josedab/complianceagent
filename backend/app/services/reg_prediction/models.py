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


class ImpactSeverity(str, Enum):
    TRANSFORMATIVE = "transformative"
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"


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


@dataclass
class EarlyWarning:
    id: UUID = field(default_factory=uuid4)
    prediction_id: UUID = field(default_factory=uuid4)
    title: str = ""
    urgency: str = "medium"
    days_until_predicted: int = 180
    recommended_actions: list[str] = field(default_factory=list)
    created_at: datetime | None = None


@dataclass
class PredictionAccuracy:
    total_predictions: int = 0
    verified_correct: int = 0
    verified_incorrect: int = 0
    pending_verification: int = 0
    accuracy_rate: float = 0.0
    avg_lead_time_months: float = 0.0
