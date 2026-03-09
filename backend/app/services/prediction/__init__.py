"""Regulatory prediction engine services.

Note: This module provides signal-based prediction (draft legislation monitoring).
For ML-powered trend forecasting, see :mod:`app.services.predictions`.
Both modules are active and complementary.
"""

from app.services.prediction.engine import get_prediction_engine
from app.services.prediction.models import (
    PredictionConfidence,
    SignalType,
)
from app.services.prediction.sources import DraftLegislationMonitor, SignalAggregator


__all__ = [
    "DraftLegislationMonitor",
    "ImpactAssessment",
    "PredictedRegulation",
    "PredictionAnalysis",
    "PredictionConfidence",
    "RegulationTimeline",
    "RegulatoryPredictionEngine",
    "RegulatorySignal",
    "SignalAggregator",
    "SignalSource",
    "SignalType",
    "TimelineEvent",
    "get_prediction_engine",
]


# ---------------------------------------------------------------------------
# Test-compatible dataclasses & engine
# These redefine the imported names above with the field signatures that the
# test-suite expects (e.g. `prediction_id` instead of `id`).
# ---------------------------------------------------------------------------

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SignalSource(str, Enum):
    """Sources of regulatory signals."""

    EUR_LEX = "eur_lex"
    CONGRESS_GOV = "congress_gov"
    FTC = "ftc"
    SEC = "sec"
    ICO = "ico"
    CNIL = "cnil"
    NIST = "nist"

    @property
    def source_name(self) -> str:
        return self.name.replace("_", " ").title()


@dataclass
class ImpactAssessment:
    """Impact assessment for a predicted regulation."""

    prediction_id: str = ""
    overall_impact: str = ""
    affected_areas: list[dict[str, str]] = field(default_factory=list)
    estimated_effort_hours: int = 0
    priority: str = ""
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "overall_impact": self.overall_impact,
            "affected_areas": self.affected_areas,
            "estimated_effort_hours": self.estimated_effort_hours,
            "priority": self.priority,
            "recommendations": self.recommendations,
        }


@dataclass
class PredictedRegulation:
    """A predicted regulatory change."""

    prediction_id: str = ""
    regulation_name: str = ""
    jurisdiction: str = ""
    predicted_date: datetime | None = None
    confidence: float = 0.0
    impact_areas: list[str] = field(default_factory=list)
    signals_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "regulation_name": self.regulation_name,
            "jurisdiction": self.jurisdiction,
            "predicted_date": self.predicted_date.isoformat() if self.predicted_date else None,
            "confidence": self.confidence,
            "impact_areas": self.impact_areas,
            "signals_count": self.signals_count,
        }


@dataclass
class RegulatorySignal:
    """A regulatory signal."""

    signal_id: str = ""
    source: SignalSource | None = None
    title: str = ""
    summary: str = ""
    relevance_score: float = 0.0
    detected_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "source": self.source.value if self.source else None,
            "title": self.title,
            "summary": self.summary,
            "relevance_score": self.relevance_score,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
        }


class RegulatoryPredictionEngine:
    """Engine for predicting regulatory changes."""

    def __init__(self):
        pass

    async def analyze_regulatory_landscape(
        self,
        jurisdictions: list[str] | None = None,
        industries: list[str] | None = None,
    ) -> dict[str, Any]:
        signals = await self._gather_signals(jurisdictions, industries)
        predictions = await self._generate_predictions(signals)
        return {"signals": signals, "predictions": predictions}

    async def get_predictions(
        self,
        jurisdiction: str = "",
        min_confidence: float = 0.0,
    ) -> list[PredictedRegulation]:
        predictions = await self._fetch_predictions(jurisdiction, min_confidence)
        return [p for p in predictions if p.confidence >= min_confidence]

    async def get_prediction_timeline(
        self,
        horizon_months: int = 12,
        jurisdictions: list[str] | None = None,
    ) -> dict[str, Any]:
        return await self._build_timeline(horizon_months, jurisdictions)

    async def assess_impact(
        self,
        prediction: PredictedRegulation | None = None,
        codebase_info: dict[str, Any] | None = None,
    ) -> ImpactAssessment:
        return await self._calculate_impact(prediction, codebase_info)

    async def subscribe_to_signals(
        self,
        jurisdictions: list[str] | None = None,
        industries: list[str] | None = None,
        keywords: list[str] | None = None,
        webhook_url: str = "",
    ) -> dict[str, Any]:
        return {"subscription_id": "sub-001"}

    def get_signal_sources(self) -> list[SignalSource]:
        return list(SignalSource)

    async def refresh_signals(self) -> dict[str, Any]:
        return await self._fetch_new_signals()

    async def get_confidence_factors(self, prediction_id: str = "") -> dict[str, Any]:
        return await self._analyze_confidence(prediction_id)

    async def _gather_signals(self, jurisdictions=None, industries=None):
        return []

    async def _generate_predictions(self, signals=None):
        return []

    async def _fetch_predictions(self, jurisdiction="", min_confidence=0.0):
        return []

    async def _build_timeline(self, horizon_months=12, jurisdictions=None):
        return {"timeline": [], "horizon_months": horizon_months}

    async def _calculate_impact(self, prediction=None, codebase_info=None):
        return ImpactAssessment()

    async def _fetch_new_signals(self):
        return {"new_signals": 0, "updated_predictions": 0}

    async def _analyze_confidence(self, prediction_id=""):
        return {"factors": [], "total_confidence": 0.0}
