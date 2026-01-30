"""Regulatory prediction engine using AI and signal analysis."""

import json
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import uuid4

import structlog

from app.agents.copilot import CopilotClient, CopilotMessage
from app.services.prediction.models import (
    PredictedRegulation,
    PredictionAnalysis,
    PredictionConfidence,
    RegulationTimeline,
    RegulatorySignal,
    SignalType,
    TimelineEvent,
)
from app.services.prediction.sources import DraftLegislationMonitor


logger = structlog.get_logger()


class RegulatoryPredictionEngine:
    """AI-powered engine for predicting regulatory changes."""

    def __init__(self):
        self.monitor = DraftLegislationMonitor()
        self._prediction_cache: dict[str, PredictedRegulation] = {}
        self._last_analysis: datetime | None = None

    async def analyze_regulatory_landscape(
        self,
        jurisdictions: list[str] | None = None,
        frameworks: list[str] | None = None,
        horizon_months: int = 12,
    ) -> PredictionAnalysis:
        """Analyze the regulatory landscape and generate predictions.

        Args:
            jurisdictions: Filter by jurisdictions
            frameworks: Filter by regulatory frameworks (e.g., "GDPR", "AI Act")
            horizon_months: Prediction horizon in months

        Returns:
            Analysis with predicted regulations
        """
        logger.info(
            "Starting regulatory landscape analysis",
            jurisdictions=jurisdictions,
            frameworks=frameworks,
            horizon_months=horizon_months,
        )

        # Fetch signals from all sources
        async with self.monitor:
            signals = await self.monitor.fetch_signals(
                jurisdictions=jurisdictions,
            )

        logger.info(f"Fetched {len(signals)} regulatory signals")

        # Group signals by jurisdiction/framework
        grouped_signals: dict[str, list[RegulatorySignal]] = {}
        for signal in signals:
            key = f"{signal.jurisdiction}:{','.join(signal.affected_regulations)}"
            if key not in grouped_signals:
                grouped_signals[key] = []
            grouped_signals[key].append(signal)

        # Generate predictions for each group
        predictions = []
        for key, group_signals in grouped_signals.items():
            prediction = await self._generate_prediction(
                signals=group_signals,
                horizon_months=horizon_months,
            )
            if prediction:
                predictions.append(prediction)

        # Filter by frameworks if specified
        if frameworks:
            predictions = [
                p for p in predictions
                if any(f in p.affected_frameworks for f in frameworks)
            ]

        # Sort by confidence and effective date
        predictions.sort(
            key=lambda p: (
                -p.confidence_score,
                p.predicted_effective_date or date.max,
            )
        )

        # Build coverage stats
        coverage = {}
        for p in predictions:
            coverage[p.jurisdiction] = coverage.get(p.jurisdiction, 0) + 1

        self._last_analysis = datetime.now(UTC)

        return PredictionAnalysis(
            predictions=predictions,
            signals_processed=len(signals),
            analysis_timestamp=self._last_analysis,
            next_update=self._last_analysis + timedelta(hours=24),
            coverage=coverage,
        )

    async def _generate_prediction(
        self,
        signals: list[RegulatorySignal],
        horizon_months: int,
    ) -> PredictedRegulation | None:
        """Generate a prediction from a group of related signals."""
        if not signals:
            return None

        # Get the primary signal (highest relevance)
        primary_signal = max(signals, key=lambda s: s.relevance_score)

        # Use AI to analyze signals and generate prediction
        async with CopilotClient() as client:
            try:
                signals_data = [
                    {
                        "type": s.signal_type.value,
                        "title": s.title,
                        "description": s.description,
                        "jurisdiction": s.jurisdiction,
                        "relevance": s.relevance_score,
                        "key_requirements": s.key_requirements,
                        "timeline_indicators": s.timeline_indicators,
                    }
                    for s in signals
                ]

                system_prompt = """You are an expert regulatory analyst predicting future compliance requirements.
Based on regulatory signals, predict:
1. What regulation will be enacted
2. When it will take effect (estimate date range)
3. What code changes will be needed
4. Confidence level in the prediction

Return JSON with:
- title: Predicted regulation title
- description: What this regulation will require
- predicted_effective_date: YYYY-MM-DD (best estimate)
- effective_date_earliest: YYYY-MM-DD
- effective_date_latest: YYYY-MM-DD
- confidence_score: 0.0-1.0
- impact_summary: Brief impact description
- impact_areas: Array of affected areas
- affected_frameworks: Array of related frameworks (GDPR, CCPA, etc.)
- estimated_compliance_effort: low/medium/high
- risk_level: low/medium/high
- likely_code_changes: Array of changes needed
- affected_categories: Array (data_privacy, consent, security, ai_transparency, etc.)
- preparation_recommendations: Array of actions to take now
- key_milestones: Array of {date, description} for regulatory timeline"""

                user_prompt = f"""Analyze these regulatory signals and predict the upcoming regulation:

Jurisdiction: {primary_signal.jurisdiction}
Signals:
{json.dumps(signals_data, indent=2)}

Prediction horizon: {horizon_months} months

Return JSON only."""

                response = await client.chat(
                    messages=[CopilotMessage(role="user", content=user_prompt)],
                    system_message=system_prompt,
                    temperature=0.3,
                    max_tokens=2048,
                )

                content = response.content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                content = content.rstrip("`")
                result = json.loads(content)

                # Parse dates
                effective_date = None
                if result.get("predicted_effective_date"):
                    try:
                        effective_date = date.fromisoformat(result["predicted_effective_date"])
                    except ValueError:
                        pass

                date_range = None
                if result.get("effective_date_earliest") and result.get("effective_date_latest"):
                    try:
                        date_range = (
                            date.fromisoformat(result["effective_date_earliest"]),
                            date.fromisoformat(result["effective_date_latest"]),
                        )
                    except ValueError:
                        pass

                # Determine confidence level
                score = result.get("confidence_score", 0.5)
                if score >= 0.9:
                    confidence = PredictionConfidence.VERY_HIGH
                elif score >= 0.7:
                    confidence = PredictionConfidence.HIGH
                elif score >= 0.5:
                    confidence = PredictionConfidence.MEDIUM
                elif score >= 0.3:
                    confidence = PredictionConfidence.LOW
                else:
                    confidence = PredictionConfidence.VERY_LOW

                return PredictedRegulation(
                    id=uuid4(),
                    title=result.get("title", primary_signal.title),
                    description=result.get("description", primary_signal.description),
                    jurisdiction=primary_signal.jurisdiction,
                    regulatory_body=primary_signal.source_name,
                    predicted_effective_date=effective_date,
                    effective_date_range=date_range,
                    confidence=confidence,
                    confidence_score=score,
                    impact_summary=result.get("impact_summary", ""),
                    impact_areas=result.get("impact_areas", []),
                    affected_frameworks=result.get("affected_frameworks", primary_signal.affected_regulations),
                    estimated_compliance_effort=result.get("estimated_compliance_effort", "medium"),
                    risk_level=result.get("risk_level", "medium"),
                    supporting_signals=signals,
                    likely_code_changes=result.get("likely_code_changes", []),
                    affected_categories=result.get("affected_categories", []),
                    preparation_recommendations=result.get("preparation_recommendations", []),
                    key_milestones=result.get("key_milestones", []),
                )

            except Exception as e:
                logger.warning(f"Failed to generate prediction: {e}")
                # Return basic prediction from signal data
                return PredictedRegulation(
                    id=uuid4(),
                    title=primary_signal.title,
                    description=primary_signal.description,
                    jurisdiction=primary_signal.jurisdiction,
                    regulatory_body=primary_signal.source_name,
                    confidence=PredictionConfidence.LOW,
                    confidence_score=primary_signal.relevance_score * 0.5,
                    affected_frameworks=primary_signal.affected_regulations,
                    supporting_signals=signals,
                )

    async def generate_timeline(
        self,
        prediction_id: str,
    ) -> RegulationTimeline | None:
        """Generate a detailed timeline for a predicted regulation."""
        prediction = self._prediction_cache.get(prediction_id)
        if not prediction:
            return None

        events = []

        # Add milestones from prediction
        for milestone in prediction.key_milestones:
            try:
                event_date = date.fromisoformat(milestone.get("date", ""))
                events.append(TimelineEvent(
                    date=event_date,
                    event_type="milestone",
                    description=milestone.get("description", ""),
                    confidence=prediction.confidence_score,
                ))
            except ValueError:
                continue

        # Add predicted effective date
        if prediction.predicted_effective_date:
            events.append(TimelineEvent(
                date=prediction.predicted_effective_date,
                event_type="effective",
                description="Predicted effective date",
                confidence=prediction.confidence_score,
            ))

        # Sort by date
        events.sort(key=lambda e: e.date)

        return RegulationTimeline(
            regulation_id=prediction.id,
            events=events,
            overall_confidence=prediction.confidence_score,
            last_updated=datetime.now(UTC),
        )

    async def get_predictions_for_framework(
        self,
        framework: str,
        include_low_confidence: bool = False,
    ) -> list[PredictedRegulation]:
        """Get predictions affecting a specific framework."""
        # Run analysis if needed
        if not self._last_analysis or (
            datetime.now(UTC) - self._last_analysis > timedelta(hours=24)
        ):
            await self.analyze_regulatory_landscape()

        predictions = [
            p for p in self._prediction_cache.values()
            if framework in p.affected_frameworks
        ]

        if not include_low_confidence:
            predictions = [
                p for p in predictions
                if p.confidence_score >= 0.3
            ]

        return sorted(predictions, key=lambda p: -p.confidence_score)

    async def assess_code_impact(
        self,
        prediction: PredictedRegulation,
        codebase_info: dict[str, Any],
    ) -> dict[str, Any]:
        """Assess the potential impact of a predicted regulation on a codebase."""
        async with CopilotClient() as client:
            try:
                system_prompt = """You are an expert compliance engineer assessing regulatory impact on code.

Given a predicted regulation and codebase information, identify:
1. Which code areas will need changes
2. Specific code patterns that will be affected
3. Estimated effort for compliance
4. Priority of changes

Return JSON with:
- affected_patterns: Array of {pattern, description, urgency}
- estimated_changes: Array of {area, change_type, description}
- total_effort_days: Number
- priority_areas: Array sorted by urgency
- immediate_actions: Array of steps to take now
- risks: Array of potential compliance risks"""

                user_prompt = f"""Assess impact on codebase:

**Predicted Regulation**:
- Title: {prediction.title}
- Description: {prediction.description}
- Jurisdiction: {prediction.jurisdiction}
- Likely Code Changes: {prediction.likely_code_changes}
- Affected Categories: {prediction.affected_categories}
- Effective Date: {prediction.predicted_effective_date}

**Codebase Information**:
- Languages: {codebase_info.get('languages', [])}
- Frameworks: {codebase_info.get('frameworks', [])}
- Data Types Handled: {codebase_info.get('data_types', [])}
- Current Compliance: {codebase_info.get('current_compliance', [])}

Return JSON only."""

                response = await client.chat(
                    messages=[CopilotMessage(role="user", content=user_prompt)],
                    system_message=system_prompt,
                    temperature=0.3,
                    max_tokens=2048,
                )

                content = response.content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                return json.loads(content.rstrip("`"))

            except Exception as e:
                logger.warning(f"Failed to assess code impact: {e}")
                return {
                    "affected_patterns": [],
                    "estimated_changes": [],
                    "total_effort_days": 0,
                    "priority_areas": [],
                    "immediate_actions": prediction.preparation_recommendations,
                    "risks": [],
                }


# Global engine instance
_engine: RegulatoryPredictionEngine | None = None


def get_prediction_engine() -> RegulatoryPredictionEngine:
    """Get or create the global prediction engine."""
    global _engine
    if _engine is None:
        _engine = RegulatoryPredictionEngine()
    return _engine
