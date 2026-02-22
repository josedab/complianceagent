"""Regulatory prediction API endpoints."""

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.services.prediction import (
    get_prediction_engine,
)


router = APIRouter()


class SignalResponse(BaseModel):
    """A regulatory signal."""

    id: str
    signal_type: str
    title: str
    description: str
    source_url: str
    source_name: str
    jurisdiction: str
    detected_at: datetime
    relevance_score: float
    affected_regulations: list[str]
    affected_industries: list[str]
    key_requirements: list[str]
    timeline_indicators: list[str]


class PredictionResponse(BaseModel):
    """A predicted regulatory change."""

    id: str
    title: str
    description: str
    jurisdiction: str
    regulatory_body: str
    predicted_effective_date: date | None = None
    effective_date_range: tuple[date, date] | None = None
    confidence: str
    confidence_score: float
    impact_summary: str
    impact_areas: list[str]
    affected_frameworks: list[str]
    estimated_compliance_effort: str
    risk_level: str
    likely_code_changes: list[str]
    affected_categories: list[str]
    preparation_recommendations: list[str]
    key_milestones: list[dict[str, Any]]
    supporting_signals: list[SignalResponse]
    created_at: datetime
    status: str


class AnalysisResponse(BaseModel):
    """Response from regulatory landscape analysis."""

    predictions: list[PredictionResponse]
    signals_processed: int
    analysis_timestamp: datetime
    next_update: datetime | None = None
    coverage: dict[str, int]


class TimelineEvent(BaseModel):
    """An event in the regulatory timeline."""

    date: date
    event_type: str
    description: str
    confidence: float


class TimelineResponse(BaseModel):
    """Predicted timeline for a regulation."""

    regulation_id: str
    events: list[TimelineEvent]
    overall_confidence: float
    last_updated: datetime


class ImpactAssessmentRequest(BaseModel):
    """Request for code impact assessment."""

    prediction_id: str
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    data_types: list[str] = Field(default_factory=list)
    current_compliance: list[str] = Field(default_factory=list)


class ImpactPattern(BaseModel):
    """An affected code pattern."""

    pattern: str
    description: str
    urgency: str


class EstimatedChange(BaseModel):
    """An estimated code change."""

    area: str
    change_type: str
    description: str


class ImpactAssessmentResponse(BaseModel):
    """Response from code impact assessment."""

    prediction_id: str
    affected_patterns: list[ImpactPattern]
    estimated_changes: list[EstimatedChange]
    total_effort_days: float
    priority_areas: list[str]
    immediate_actions: list[str]
    risks: list[str]


class SourceStatus(BaseModel):
    """Status of a regulatory source."""

    name: str
    jurisdiction: str
    enabled: bool
    signal_types: list[str]
    last_check: datetime | None
    cached_signals: int
    update_frequency_hours: int


def _prediction_to_response(prediction) -> PredictionResponse:
    """Convert prediction model to response."""
    signals = [
        SignalResponse(
            id=str(s.id),
            signal_type=s.signal_type.value,
            title=s.title,
            description=s.description,
            source_url=s.source_url,
            source_name=s.source_name,
            jurisdiction=s.jurisdiction,
            detected_at=s.detected_at,
            relevance_score=s.relevance_score,
            affected_regulations=s.affected_regulations,
            affected_industries=s.affected_industries,
            key_requirements=s.key_requirements,
            timeline_indicators=s.timeline_indicators,
        )
        for s in prediction.supporting_signals
    ]

    return PredictionResponse(
        id=str(prediction.id),
        title=prediction.title,
        description=prediction.description,
        jurisdiction=prediction.jurisdiction,
        regulatory_body=prediction.regulatory_body,
        predicted_effective_date=prediction.predicted_effective_date,
        effective_date_range=prediction.effective_date_range,
        confidence=prediction.confidence.value,
        confidence_score=prediction.confidence_score,
        impact_summary=prediction.impact_summary,
        impact_areas=prediction.impact_areas,
        affected_frameworks=prediction.affected_frameworks,
        estimated_compliance_effort=prediction.estimated_compliance_effort,
        risk_level=prediction.risk_level,
        likely_code_changes=prediction.likely_code_changes,
        affected_categories=prediction.affected_categories,
        preparation_recommendations=prediction.preparation_recommendations,
        key_milestones=prediction.key_milestones,
        supporting_signals=signals,
        created_at=prediction.created_at,
        status=prediction.status,
    )


@router.get("/analyze", response_model=AnalysisResponse)
async def analyze_regulatory_landscape(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    jurisdictions: list[str] | None = Query(
        default=None,
        description="Filter by jurisdictions (e.g., EU, US-Federal, UK)",
    ),
    frameworks: list[str] | None = Query(
        default=None,
        description="Filter by regulatory frameworks (e.g., GDPR, AI Act)",
    ),
    horizon_months: int = Query(
        default=12,
        ge=3,
        le=36,
        description="Prediction horizon in months",
    ),
) -> AnalysisResponse:
    """Analyze the regulatory landscape and generate predictions.

    Scans regulatory sources for signals (draft legislation, consultations,
    enforcement actions) and uses AI to predict upcoming regulatory changes.

    Returns predictions with confidence scores, timelines, and preparation
    recommendations.
    """
    engine = get_prediction_engine()

    analysis = await engine.analyze_regulatory_landscape(
        jurisdictions=jurisdictions,
        frameworks=frameworks,
        horizon_months=horizon_months,
    )

    predictions = [_prediction_to_response(p) for p in analysis.predictions]

    return AnalysisResponse(
        predictions=predictions,
        signals_processed=analysis.signals_processed,
        analysis_timestamp=analysis.analysis_timestamp,
        next_update=analysis.next_update,
        coverage=analysis.coverage,
    )


@router.get("/predictions", response_model=list[PredictionResponse])
async def list_predictions(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    jurisdiction: str | None = Query(default=None),
    framework: str | None = Query(default=None),
    min_confidence: float = Query(default=0.3, ge=0, le=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[PredictionResponse]:
    """List cached regulatory predictions.

    Returns predictions from the most recent analysis, filtered by
    jurisdiction, framework, and confidence threshold.
    """
    engine = get_prediction_engine()

    # Ensure we have predictions
    if not engine._prediction_cache:
        await engine.analyze_regulatory_landscape()

    predictions = list(engine._prediction_cache.values())

    # Apply filters
    if jurisdiction:
        predictions = [p for p in predictions if p.jurisdiction == jurisdiction]

    if framework:
        predictions = [p for p in predictions if framework in p.affected_frameworks]

    predictions = [p for p in predictions if p.confidence_score >= min_confidence]

    # Sort by confidence and limit
    predictions = sorted(predictions, key=lambda p: -p.confidence_score)[:limit]

    return [_prediction_to_response(p) for p in predictions]


@router.get("/predictions/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(
    prediction_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> PredictionResponse:
    """Get details of a specific prediction."""
    engine = get_prediction_engine()

    prediction = engine._prediction_cache.get(prediction_id)
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction {prediction_id} not found",
        )

    return _prediction_to_response(prediction)


@router.get("/predictions/{prediction_id}/timeline", response_model=TimelineResponse)
async def get_prediction_timeline(
    prediction_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> TimelineResponse:
    """Get the predicted timeline for a regulation.

    Returns key dates and milestones in the regulatory process.
    """
    engine = get_prediction_engine()

    timeline = await engine.generate_timeline(prediction_id)
    if not timeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Timeline not available for prediction {prediction_id}",
        )

    events = [
        TimelineEvent(
            date=e.date,
            event_type=e.event_type,
            description=e.description,
            confidence=e.confidence,
        )
        for e in timeline.events
    ]

    return TimelineResponse(
        regulation_id=str(timeline.regulation_id),
        events=events,
        overall_confidence=timeline.overall_confidence,
        last_updated=timeline.last_updated,
    )


@router.post("/impact-assessment", response_model=ImpactAssessmentResponse)
async def assess_code_impact(
    request: ImpactAssessmentRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ImpactAssessmentResponse:
    """Assess the potential code impact of a predicted regulation.

    Analyzes how a predicted regulation would affect the codebase based
    on languages, frameworks, and data types handled.
    """
    engine = get_prediction_engine()

    prediction = engine._prediction_cache.get(request.prediction_id)
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction {request.prediction_id} not found",
        )

    codebase_info = {
        "languages": request.languages,
        "frameworks": request.frameworks,
        "data_types": request.data_types,
        "current_compliance": request.current_compliance,
    }

    result = await engine.assess_code_impact(prediction, codebase_info)

    affected_patterns = [
        ImpactPattern(
            pattern=p.get("pattern", ""),
            description=p.get("description", ""),
            urgency=p.get("urgency", "medium"),
        )
        for p in result.get("affected_patterns", [])
    ]

    estimated_changes = [
        EstimatedChange(
            area=c.get("area", ""),
            change_type=c.get("change_type", ""),
            description=c.get("description", ""),
        )
        for c in result.get("estimated_changes", [])
    ]

    return ImpactAssessmentResponse(
        prediction_id=request.prediction_id,
        affected_patterns=affected_patterns,
        estimated_changes=estimated_changes,
        total_effort_days=result.get("total_effort_days", 0),
        priority_areas=result.get("priority_areas", []),
        immediate_actions=result.get("immediate_actions", []),
        risks=result.get("risks", []),
    )


@router.get("/sources", response_model=list[SourceStatus])
async def list_regulatory_sources(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[SourceStatus]:
    """List all configured regulatory monitoring sources.

    Shows the status of each source including last check time and
    cached signal count.
    """
    engine = get_prediction_engine()

    async with engine.monitor:
        status_list = engine.monitor.get_source_status()

    return [
        SourceStatus(
            name=s["name"],
            jurisdiction=s["jurisdiction"],
            enabled=s["enabled"],
            signal_types=s["signal_types"],
            last_check=datetime.fromisoformat(s["last_check"]) if s["last_check"] else None,
            cached_signals=s["cached_signals"],
            update_frequency_hours=s["update_frequency_hours"],
        )
        for s in status_list
    ]


@router.get("/signals", response_model=list[SignalResponse])
async def list_regulatory_signals(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    jurisdictions: list[str] | None = Query(default=None),
    signal_types: list[str] | None = Query(default=None),
    force_refresh: bool = Query(default=False),
) -> list[SignalResponse]:
    """Fetch regulatory signals from configured sources.

    Signals include draft legislation, public consultations,
    enforcement actions, and regulatory guidance.
    """
    from app.services.prediction.models import SignalType

    engine = get_prediction_engine()

    # Convert signal types
    types = None
    if signal_types:
        types = [SignalType(t) for t in signal_types if t in SignalType.__members__.values()]

    async with engine.monitor:
        signals = await engine.monitor.fetch_signals(
            jurisdictions=jurisdictions,
            signal_types=types,
            force_refresh=force_refresh,
        )

    return [
        SignalResponse(
            id=str(s.id),
            signal_type=s.signal_type.value,
            title=s.title,
            description=s.description,
            source_url=s.source_url,
            source_name=s.source_name,
            jurisdiction=s.jurisdiction,
            detected_at=s.detected_at,
            relevance_score=s.relevance_score,
            affected_regulations=s.affected_regulations,
            affected_industries=s.affected_industries,
            key_requirements=s.key_requirements,
            timeline_indicators=s.timeline_indicators,
        )
        for s in signals
    ]


# ---------------------------------------------------------------------------
# v2: ML Prediction Engine with Signal Ingestion & Impact Assessment
# ---------------------------------------------------------------------------


class IngestSignalRequest(BaseModel):
    """Request to ingest a regulatory signal."""

    source: str = Field(
        ...,
        description="Signal source: legislative, committee, publication, news, enforcement, industry",
    )
    strength: str = Field("moderate", description="Signal strength: strong, moderate, weak")
    jurisdiction: str = Field(..., description="Jurisdiction code (e.g., 'EU', 'US-CA')")
    framework: str = Field(..., description="Regulatory framework (e.g., 'gdpr', 'hipaa')")
    title: str = Field(..., description="Signal title")
    description: str = Field("", description="Signal description")
    url: str | None = Field(None, description="Source URL")


class MLPredictionSchema(BaseModel):
    """An ML-generated regulatory prediction."""

    id: str
    title: str
    description: str
    jurisdiction: str
    framework: str
    predicted_effective_date: str | None
    confidence: str
    confidence_score: float
    impact_level: str
    supporting_signals: list[str]
    affected_areas: list[str]
    preparation_recommendations: list[str]


class MLImpactAssessmentSchema(BaseModel):
    """Impact assessment of a predicted regulation."""

    prediction_id: str
    repository: str
    affected_components: list[str]
    estimated_effort_hours: float
    risk_score: float
    preparation_timeline: list[dict]


class AccuracyMetricsSchema(BaseModel):
    """Prediction accuracy metrics."""

    total_predictions: int
    correct_predictions: int
    partially_correct: int
    incorrect_predictions: int
    accuracy_rate: float
    avg_lead_time_days: float


@router.post("/v2/signals", summary="Ingest regulatory signal")
async def ingest_regulatory_signal(
    request: IngestSignalRequest,
    db: DB,
) -> dict:
    """Ingest a new regulatory signal for prediction analysis."""
    from app.services.predictions.prediction_engine import (
        PredictionEngine,
        RegulatorySignal,
        SignalSource,
        SignalStrength,
    )

    engine = PredictionEngine(db=db)
    signal = RegulatorySignal(
        source=SignalSource(request.source),
        strength=SignalStrength(request.strength),
        jurisdiction=request.jurisdiction,
        framework=request.framework,
        title=request.title,
        description=request.description,
        url=request.url,
    )
    result = await engine.ingest_signal(signal)
    return {
        "id": str(result.id),
        "source": result.source.value,
        "framework": result.framework,
        "jurisdiction": result.jurisdiction,
        "detected_at": result.detected_at.isoformat(),
    }


@router.post(
    "/v2/generate", response_model=list[MLPredictionSchema], summary="Generate ML predictions"
)
async def generate_ml_predictions(
    db: DB,
    jurisdiction: str | None = None,
    framework: str | None = None,
) -> list[MLPredictionSchema]:
    """Generate ML-powered predictions from accumulated signals."""
    from app.services.predictions.prediction_engine import PredictionEngine

    engine = PredictionEngine(db=db)
    predictions = await engine.generate_predictions(jurisdiction=jurisdiction, framework=framework)
    return [
        MLPredictionSchema(
            id=str(p.id),
            title=p.title,
            description=p.description,
            jurisdiction=p.jurisdiction,
            framework=p.framework,
            predicted_effective_date=p.predicted_effective_date.isoformat()
            if p.predicted_effective_date
            else None,
            confidence=p.confidence.value,
            confidence_score=p.confidence_score,
            impact_level=p.impact_level.value,
            supporting_signals=[str(s) for s in p.supporting_signals],
            affected_areas=p.affected_areas,
            preparation_recommendations=p.preparation_recommendations,
        )
        for p in predictions
    ]


@router.get(
    "/v2/ml-predictions", response_model=list[MLPredictionSchema], summary="List ML predictions"
)
async def list_ml_predictions(
    db: DB,
    jurisdiction: str | None = None,
    min_confidence: float = 0.0,
    limit: int = 50,
) -> list[MLPredictionSchema]:
    """List ML-generated predictions with optional filters."""
    from app.services.predictions.prediction_engine import PredictionEngine

    engine = PredictionEngine(db=db)
    predictions = await engine.list_predictions(
        jurisdiction=jurisdiction,
        min_confidence=min_confidence,
        limit=limit,
    )
    return [
        MLPredictionSchema(
            id=str(p.id),
            title=p.title,
            description=p.description,
            jurisdiction=p.jurisdiction,
            framework=p.framework,
            predicted_effective_date=p.predicted_effective_date.isoformat()
            if p.predicted_effective_date
            else None,
            confidence=p.confidence.value,
            confidence_score=p.confidence_score,
            impact_level=p.impact_level.value,
            supporting_signals=[str(s) for s in p.supporting_signals],
            affected_areas=p.affected_areas,
            preparation_recommendations=p.preparation_recommendations,
        )
        for p in predictions
    ]


@router.post(
    "/v2/impact", response_model=MLImpactAssessmentSchema, summary="Assess prediction impact"
)
async def assess_prediction_impact(
    prediction_id: str,
    repository: str,
    db: DB,
) -> MLImpactAssessmentSchema:
    """Assess the impact of a predicted regulation on a repository."""
    from uuid import UUID

    from app.services.predictions.prediction_engine import PredictionEngine

    engine = PredictionEngine(db=db)
    assessment = await engine.assess_impact(
        prediction_id=UUID(prediction_id),
        repository=repository,
    )
    return MLImpactAssessmentSchema(
        prediction_id=assessment.prediction_id,
        repository=assessment.repository,
        affected_components=assessment.affected_components,
        estimated_effort_hours=assessment.estimated_effort_hours,
        risk_score=assessment.risk_score,
        preparation_timeline=assessment.preparation_timeline,
    )


@router.get("/v2/accuracy", response_model=AccuracyMetricsSchema, summary="Prediction accuracy")
async def get_prediction_accuracy(db: DB) -> AccuracyMetricsSchema:
    """Get prediction accuracy metrics."""
    from app.services.predictions.prediction_engine import PredictionEngine

    engine = PredictionEngine(db=db)
    metrics = await engine.get_accuracy_metrics()
    return AccuracyMetricsSchema(
        total_predictions=metrics.total_predictions,
        correct_predictions=metrics.correct_predictions,
        partially_correct=metrics.partially_correct,
        incorrect_predictions=metrics.incorrect_predictions,
        accuracy_rate=metrics.accuracy_rate,
        avg_lead_time_days=metrics.avg_lead_time_days,
    )
