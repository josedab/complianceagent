"""Prediction models and data structures."""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class SignalType(str, Enum):
    """Types of regulatory signals."""

    DRAFT_LEGISLATION = "draft_legislation"
    REGULATORY_PROPOSAL = "regulatory_proposal"
    PUBLIC_CONSULTATION = "public_consultation"
    ENFORCEMENT_ACTION = "enforcement_action"
    REGULATORY_GUIDANCE = "regulatory_guidance"
    INDUSTRY_STANDARD = "industry_standard"
    COURT_DECISION = "court_decision"
    POLITICAL_STATEMENT = "political_statement"
    EXPERT_ANALYSIS = "expert_analysis"
    MEDIA_COVERAGE = "media_coverage"


class PredictionConfidence(str, Enum):
    """Confidence levels for predictions."""

    VERY_HIGH = "very_high"  # >90% confidence
    HIGH = "high"  # 70-90%
    MEDIUM = "medium"  # 50-70%
    LOW = "low"  # 30-50%
    VERY_LOW = "very_low"  # <30%


@dataclass
class RegulatorySignal:
    """A signal indicating potential regulatory change."""

    id: UUID = field(default_factory=uuid4)
    signal_type: SignalType = SignalType.DRAFT_LEGISLATION
    title: str = ""
    description: str = ""
    source_url: str = ""
    source_name: str = ""
    jurisdiction: str = ""
    detected_at: datetime = field(default_factory=datetime.utcnow)
    relevance_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    # Extracted regulatory implications
    affected_regulations: list[str] = field(default_factory=list)
    affected_industries: list[str] = field(default_factory=list)
    affected_data_types: list[str] = field(default_factory=list)
    key_requirements: list[str] = field(default_factory=list)
    timeline_indicators: list[str] = field(default_factory=list)


@dataclass
class PredictedRegulation:
    """A predicted regulatory change."""

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    jurisdiction: str = ""
    regulatory_body: str = ""
    
    # Prediction details
    predicted_effective_date: date | None = None
    effective_date_range: tuple[date, date] | None = None
    confidence: PredictionConfidence = PredictionConfidence.MEDIUM
    confidence_score: float = 0.5
    
    # Impact assessment
    impact_summary: str = ""
    impact_areas: list[str] = field(default_factory=list)
    affected_frameworks: list[str] = field(default_factory=list)
    estimated_compliance_effort: str = ""
    risk_level: str = "medium"
    
    # Supporting evidence
    supporting_signals: list[RegulatorySignal] = field(default_factory=list)
    source_documents: list[str] = field(default_factory=list)
    key_milestones: list[dict[str, Any]] = field(default_factory=list)
    
    # Code impact
    likely_code_changes: list[str] = field(default_factory=list)
    affected_categories: list[str] = field(default_factory=list)
    preparation_recommendations: list[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    reviewed_by: str | None = None
    status: str = "active"  # active, archived, confirmed, invalidated


@dataclass
class PredictionAnalysis:
    """Analysis result from the prediction engine."""

    predictions: list[PredictedRegulation]
    signals_processed: int
    analysis_timestamp: datetime
    next_update: datetime | None = None
    model_version: str = "1.0.0"
    coverage: dict[str, int] = field(default_factory=dict)  # jurisdiction -> count


@dataclass
class TimelineEvent:
    """An event in the regulatory timeline."""

    date: date
    event_type: str  # draft, vote, adoption, effective, enforcement
    description: str
    confidence: float = 0.5
    source: str | None = None


@dataclass
class RegulationTimeline:
    """Predicted timeline for a regulation."""

    regulation_id: UUID
    events: list[TimelineEvent]
    overall_confidence: float
    last_updated: datetime
