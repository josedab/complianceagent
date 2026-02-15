"""API endpoints for Compliance Impact Prediction Market."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.prediction_market import MarketStatus, PredictionMarketService

logger = structlog.get_logger()
router = APIRouter()


# --- Response Models ---

class MarketSchema(BaseModel):
    id: str
    title: str
    description: str
    market_type: str
    status: str
    regulation: str
    jurisdiction: str
    current_probability: float
    total_volume: float
    total_participants: int
    resolution_criteria: str
    closes_at: str | None


class PositionSchema(BaseModel):
    id: str
    market_id: str
    position: str
    shares: float
    cost_basis: float
    current_value: float


class PredictionRecordSchema(BaseModel):
    display_name: str
    total_predictions: int
    correct_predictions: int
    brier_score: float
    accuracy_rate: float
    total_pnl: float
    rank: int
    is_superforecaster: bool


class MarketStatsSchema(BaseModel):
    total_markets: int
    active_markets: int
    resolved_markets: int
    total_participants: int
    total_volume: float
    forecast_accuracy: float
    avg_participants_per_market: float


class PlacePredictionRequest(BaseModel):
    position: str = Field(..., min_length=1, description="Position: yes or no")
    shares: float = Field(..., gt=0, description="Number of shares to buy")


# --- Endpoints ---

@router.get("/markets", response_model=list[MarketSchema])
async def list_markets(
    status_filter: str | None = Query(None, alias="status"),
    jurisdiction: str | None = Query(None),
) -> list[dict]:
    svc = PredictionMarketService()
    try:
        st = MarketStatus(status_filter) if status_filter else None
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid status: {status_filter}")
    markets = await svc.list_markets(status=st, jurisdiction=jurisdiction)
    return [
        {"id": str(m.id), "title": m.title, "description": m.description,
         "market_type": m.market_type.value, "status": m.status.value,
         "regulation": m.regulation, "jurisdiction": m.jurisdiction,
         "current_probability": m.current_probability, "total_volume": m.total_volume,
         "total_participants": m.total_participants,
         "resolution_criteria": m.resolution_criteria,
         "closes_at": m.closes_at.isoformat() if m.closes_at else None}
        for m in markets
    ]


@router.post("/markets/{market_id}/predict", response_model=PositionSchema)
async def place_prediction(market_id: UUID, req: PlacePredictionRequest) -> dict:
    svc = PredictionMarketService()
    from uuid import uuid4
    try:
        pos = await svc.place_prediction(market_id, uuid4(), req.position, req.shares)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "id": str(pos.id), "market_id": str(pos.market_id),
        "position": pos.position, "shares": pos.shares,
        "cost_basis": pos.cost_basis, "current_value": pos.current_value,
    }


@router.get("/leaderboard", response_model=list[PredictionRecordSchema])
async def get_leaderboard(limit: int = Query(10, ge=1, le=100)) -> list[dict]:
    svc = PredictionMarketService()
    records = await svc.get_leaderboard(limit=limit)
    return [
        {"display_name": r.display_name, "total_predictions": r.total_predictions,
         "correct_predictions": r.correct_predictions, "brier_score": r.brier_score,
         "accuracy_rate": r.accuracy_rate, "total_pnl": r.total_pnl,
         "rank": r.rank, "is_superforecaster": r.is_superforecaster}
        for r in records
    ]


@router.get("/stats", response_model=MarketStatsSchema)
async def get_stats() -> dict:
    svc = PredictionMarketService()
    s = await svc.get_stats()
    return {
        "total_markets": s.total_markets, "active_markets": s.active_markets,
        "resolved_markets": s.resolved_markets, "total_participants": s.total_participants,
        "total_volume": s.total_volume, "forecast_accuracy": s.forecast_accuracy,
        "avg_participants_per_market": s.avg_participants_per_market,
    }
