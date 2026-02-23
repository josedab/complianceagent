"""API endpoints for Regulatory Impact Prediction."""

from typing import Any

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.reg_prediction import PredictionConfidence, RegPredictionService, SignalType


logger = structlog.get_logger()
router = APIRouter()


class PredictionSchema(BaseModel):
    id: str
    title: str
    description: str
    jurisdiction: str
    affected_frameworks: list[str]
    confidence: str
    confidence_score: float
    impact_severity: str
    predicted_effective_date: str
    prediction_horizon_months: int
    supporting_signals: list[str]
    preparation_tasks: list[dict[str, Any]]
    predicted_at: str | None


class SignalSchema(BaseModel):
    id: str
    signal_type: str
    source: str
    jurisdiction: str
    title: str
    relevance_score: float
    detected_at: str | None


class WarningSchema(BaseModel):
    id: str
    title: str
    urgency: str
    days_until_predicted: int
    recommended_actions: list[str]
    created_at: str | None


class AccuracySchema(BaseModel):
    total_predictions: int
    verified_correct: int
    pending_verification: int
    accuracy_rate: float
    avg_lead_time_months: float


class AddSignalRequest(BaseModel):
    signal_type: str = Field(...)
    source: str = Field(...)
    jurisdiction: str = Field(...)
    title: str = Field(...)
    relevance_score: float = Field(default=0.5)


@router.get("/predictions", response_model=list[PredictionSchema], summary="List predictions")
async def list_predictions(
    db: DB,
    jurisdiction: str | None = None,
    confidence: str | None = None,
    framework: str | None = None,
) -> list[PredictionSchema]:
    service = RegPredictionService(db=db)
    conf = PredictionConfidence(confidence) if confidence else None
    preds = service.list_predictions(
        jurisdiction=jurisdiction, confidence=conf, framework=framework
    )
    return [
        PredictionSchema(
            id=str(p.id),
            title=p.title,
            description=p.description,
            jurisdiction=p.jurisdiction,
            affected_frameworks=p.affected_frameworks,
            confidence=p.confidence.value,
            confidence_score=p.confidence_score,
            impact_severity=p.impact_severity.value,
            predicted_effective_date=p.predicted_effective_date,
            prediction_horizon_months=p.prediction_horizon_months,
            supporting_signals=p.supporting_signals,
            preparation_tasks=p.preparation_tasks,
            predicted_at=p.predicted_at.isoformat() if p.predicted_at else None,
        )
        for p in preds
    ]


@router.get("/signals", response_model=list[SignalSchema], summary="List signals")
async def list_signals(
    db: DB, jurisdiction: str | None = None, signal_type: str | None = None
) -> list[SignalSchema]:
    service = RegPredictionService(db=db)
    st = SignalType(signal_type) if signal_type else None
    signals = service.list_signals(jurisdiction=jurisdiction, signal_type=st)
    return [
        SignalSchema(
            id=str(s.id),
            signal_type=s.signal_type.value,
            source=s.source,
            jurisdiction=s.jurisdiction,
            title=s.title,
            relevance_score=s.relevance_score,
            detected_at=s.detected_at.isoformat() if s.detected_at else None,
        )
        for s in signals
    ]


@router.post(
    "/signals",
    response_model=SignalSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Add signal",
)
async def add_signal(request: AddSignalRequest, db: DB) -> SignalSchema:
    service = RegPredictionService(db=db)
    s = await service.add_signal(
        signal_type=request.signal_type,
        source=request.source,
        jurisdiction=request.jurisdiction,
        title=request.title,
        relevance_score=request.relevance_score,
    )
    return SignalSchema(
        id=str(s.id),
        signal_type=s.signal_type.value,
        source=s.source,
        jurisdiction=s.jurisdiction,
        title=s.title,
        relevance_score=s.relevance_score,
        detected_at=s.detected_at.isoformat() if s.detected_at else None,
    )


@router.post(
    "/early-warnings",
    response_model=list[WarningSchema],
    summary="Generate early warnings",
)
async def generate_warnings(db: DB) -> list[WarningSchema]:
    service = RegPredictionService(db=db)
    warnings = await service.generate_early_warnings()
    return [
        WarningSchema(
            id=str(w.id),
            title=w.title,
            urgency=w.urgency,
            days_until_predicted=w.days_until_predicted,
            recommended_actions=w.recommended_actions,
            created_at=w.created_at.isoformat() if w.created_at else None,
        )
        for w in warnings
    ]


@router.get("/accuracy", response_model=AccuracySchema, summary="Get prediction accuracy")
async def get_accuracy(db: DB) -> AccuracySchema:
    service = RegPredictionService(db=db)
    a = service.get_accuracy()
    return AccuracySchema(
        total_predictions=a.total_predictions,
        verified_correct=a.verified_correct,
        pending_verification=a.pending_verification,
        accuracy_rate=a.accuracy_rate,
        avg_lead_time_months=a.avg_lead_time_months,
    )
