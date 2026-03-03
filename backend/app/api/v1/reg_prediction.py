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


# --- New Production Endpoints ---


class CreatePredictionRequest(BaseModel):
    title: str = Field(...)
    description: str = Field(...)
    jurisdiction: str = Field(...)
    affected_frameworks: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.5)
    impact_severity: str = Field(default="moderate")
    predicted_effective_date: str = Field(default="")
    prediction_horizon_months: int = Field(default=12)
    preparation_tasks: list[dict[str, Any]] = Field(default_factory=list)


class LegislativeActivityRequest(BaseModel):
    committee: str = Field(...)
    jurisdiction: str = Field(...)
    activity_type: str = Field(...)
    title: str = Field(...)
    related_bills: list[str] = Field(default_factory=list)
    outcome: str = Field(default="")


class GlobalPrecedentRequest(BaseModel):
    origin_jurisdiction: str = Field(...)
    regulation_name: str = Field(...)
    adopted_by: list[str] = Field(default_factory=list)
    adoption_lag_months: float = Field(default=0.0)
    adaptation_level: str = Field(default="direct")
    key_differences: list[str] = Field(default_factory=list)


@router.get("/predictions/{prediction_id}", summary="Get prediction by ID")
async def get_prediction(prediction_id: str, db: DB) -> dict:
    service = RegPredictionService(db=db)
    p = service.get_prediction(prediction_id)
    if not p:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prediction not found")
    return {
        "id": str(p.id), "title": p.title, "description": p.description,
        "jurisdiction": p.jurisdiction, "affected_frameworks": p.affected_frameworks,
        "confidence": p.confidence.value, "confidence_score": p.confidence_score,
        "impact_severity": p.impact_severity.value, "momentum": p.momentum.value,
        "predicted_effective_date": p.predicted_effective_date,
        "prediction_horizon_months": p.prediction_horizon_months,
        "time_series": [{"date": ts.prediction_date, "value": ts.value, "lower": ts.lower_bound, "upper": ts.upper_bound} for ts in p.time_series],
        "feature_importance": p.feature_importance,
        "preparation_tasks": p.preparation_tasks,
    }


@router.post("/predictions", status_code=status.HTTP_201_CREATED, summary="Create prediction")
async def create_prediction(request: CreatePredictionRequest, db: DB) -> dict:
    service = RegPredictionService(db=db)
    p = await service.create_prediction(
        title=request.title, description=request.description,
        jurisdiction=request.jurisdiction, affected_frameworks=request.affected_frameworks,
        confidence_score=request.confidence_score, impact_severity=request.impact_severity,
        predicted_effective_date=request.predicted_effective_date,
        prediction_horizon_months=request.prediction_horizon_months,
        preparation_tasks=request.preparation_tasks,
    )
    return {"id": str(p.id), "title": p.title, "confidence_score": p.confidence_score, "momentum": p.momentum.value}


@router.post("/legislative-activities", status_code=status.HTTP_201_CREATED, summary="Ingest legislative activity")
async def ingest_legislative_activity(request: LegislativeActivityRequest, db: DB) -> dict:
    service = RegPredictionService(db=db)
    activity = await service.ingest_legislative_activity(
        committee=request.committee, jurisdiction=request.jurisdiction,
        activity_type=request.activity_type, title=request.title,
        related_bills=request.related_bills, outcome=request.outcome,
    )
    return {"id": str(activity.id), "committee": activity.committee, "signal_strength": activity.signal_strength}


@router.get("/legislative-activities", summary="List legislative activities")
async def list_activities(db: DB, jurisdiction: str | None = None, committee: str | None = None) -> list[dict]:
    service = RegPredictionService(db=db)
    activities = service.list_activities(jurisdiction=jurisdiction, committee=committee)
    return [{"id": str(a.id), "committee": a.committee, "jurisdiction": a.jurisdiction, "title": a.title, "activity_type": a.activity_type, "signal_strength": a.signal_strength} for a in activities]


@router.post("/global-precedents", status_code=status.HTTP_201_CREATED, summary="Add global precedent")
async def add_global_precedent(request: GlobalPrecedentRequest, db: DB) -> dict:
    service = RegPredictionService(db=db)
    prec = await service.add_global_precedent(
        origin_jurisdiction=request.origin_jurisdiction, regulation_name=request.regulation_name,
        adopted_by=request.adopted_by, adoption_lag_months=request.adoption_lag_months,
        adaptation_level=request.adaptation_level, key_differences=request.key_differences,
    )
    return {"id": str(prec.id), "regulation": prec.regulation_name, "adopted_by": prec.adopted_by}


@router.get("/global-precedents", summary="List global precedents")
async def list_precedents(db: DB, origin: str | None = None) -> list[dict]:
    service = RegPredictionService(db=db)
    precs = service.list_precedents(origin=origin)
    return [{"id": str(p.id), "origin": p.origin_jurisdiction, "regulation": p.regulation_name, "adopted_by": p.adopted_by, "lag_months": p.adoption_lag_months} for p in precs]
