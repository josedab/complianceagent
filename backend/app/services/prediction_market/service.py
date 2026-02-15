"""Compliance Impact Prediction Market service."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import structlog

from app.services.prediction_market.models import (
    MarketPosition,
    MarketStats,
    MarketStatus,
    MarketType,
    PredictionMarket,
    PredictionRecord,
)

logger = structlog.get_logger()

_MARKETS: list[PredictionMarket] = [
    PredictionMarket(
        id=uuid4(), title="EU AI Act Enforcement by Feb 2026",
        description="Will the EU AI Act be fully enforceable (all provisions) by February 2, 2026?",
        regulation="EU AI Act", jurisdiction="EU", current_probability=0.72,
        total_volume=15400, total_participants=89,
        resolution_criteria="Official EU gazette publication of enforcement date",
        closes_at=datetime.utcnow() + timedelta(days=180),
    ),
    PredictionMarket(
        id=uuid4(), title="US Federal Privacy Law by 2025",
        description="Will the US pass a comprehensive federal privacy law (ADPPA or equivalent) by end of 2025?",
        regulation="ADPPA", jurisdiction="US", current_probability=0.18,
        total_volume=8900, total_participants=67,
        resolution_criteria="Bill signed into law by US President",
        closes_at=datetime.utcnow() + timedelta(days=120),
    ),
    PredictionMarket(
        id=uuid4(), title="GDPR Fine >€100M in 2025",
        description="Will any single GDPR fine exceed €100 million in 2025?",
        regulation="GDPR", jurisdiction="EU", current_probability=0.45,
        total_volume=12300, total_participants=112,
        resolution_criteria="Official EDPB/national DPA announcement of fine",
        closes_at=datetime.utcnow() + timedelta(days=200),
    ),
    PredictionMarket(
        id=uuid4(), title="California AI Transparency Law",
        description="Will California enact AI transparency requirements for automated decision-making by 2026?",
        regulation="CA AI Act", jurisdiction="US-CA", current_probability=0.63,
        total_volume=5600, total_participants=41,
        resolution_criteria="Governor signature or veto deadline passage",
        closes_at=datetime.utcnow() + timedelta(days=300),
    ),
]

_LEADERBOARD: list[PredictionRecord] = [
    PredictionRecord(participant_id=uuid4(), display_name="RegOracle", total_predictions=45, correct_predictions=38, brier_score=0.12, accuracy_rate=0.844, total_pnl=2340.0, rank=1, is_superforecaster=True),
    PredictionRecord(participant_id=uuid4(), display_name="PolicyPredictor", total_predictions=38, correct_predictions=30, brier_score=0.18, accuracy_rate=0.789, total_pnl=1560.0, rank=2, is_superforecaster=True),
    PredictionRecord(participant_id=uuid4(), display_name="ComplianceSeer", total_predictions=52, correct_predictions=39, brier_score=0.21, accuracy_rate=0.75, total_pnl=980.0, rank=3),
    PredictionRecord(participant_id=uuid4(), display_name="GRCGuru", total_predictions=28, correct_predictions=20, brier_score=0.25, accuracy_rate=0.714, total_pnl=450.0, rank=4),
]


class PredictionMarketService:
    """Service for compliance impact prediction markets."""

    async def list_markets(
        self, status: MarketStatus | None = None, jurisdiction: str | None = None,
    ) -> list[PredictionMarket]:
        result = list(_MARKETS)
        if status:
            result = [m for m in result if m.status == status]
        if jurisdiction:
            result = [m for m in result if m.jurisdiction == jurisdiction]
        return result

    async def get_market(self, market_id: UUID) -> PredictionMarket | None:
        return next((m for m in _MARKETS if m.id == market_id), None)

    async def place_prediction(
        self, market_id: UUID, participant_id: UUID,
        position: str, shares: float,
    ) -> MarketPosition:
        market = await self.get_market(market_id)
        if not market:
            raise ValueError(f"Market {market_id} not found")
        if position not in ("yes", "no"):
            raise ValueError(f"Position must be 'yes' or 'no', got '{position}'")
        if market.status != MarketStatus.OPEN:
            raise ValueError(f"Market {market_id} is not open (status: {market.status.value})")
        if shares <= 0:
            raise ValueError("Shares must be greater than 0")
        cost = shares * (market.current_probability if position == "yes" else 1 - market.current_probability)
        pos = MarketPosition(
            id=uuid4(), market_id=market_id, participant_id=participant_id,
            position=position, shares=shares, cost_basis=cost, current_value=cost,
        )
        market.total_participants += 1
        market.total_volume += cost
        logger.info("market.prediction_placed", market_id=str(market_id), position=position)
        return pos

    async def get_leaderboard(self, limit: int = 10) -> list[PredictionRecord]:
        return sorted(_LEADERBOARD, key=lambda r: r.brier_score)[:limit]

    async def get_stats(self) -> MarketStats:
        active = sum(1 for m in _MARKETS if m.status == MarketStatus.OPEN)
        resolved = sum(1 for m in _MARKETS if m.status == MarketStatus.RESOLVED)
        total_vol = sum(m.total_volume for m in _MARKETS)
        total_part = sum(m.total_participants for m in _MARKETS)
        return MarketStats(
            total_markets=len(_MARKETS), active_markets=active, resolved_markets=resolved,
            total_participants=total_part, total_volume=total_vol,
            forecast_accuracy=0.78,
            avg_participants_per_market=total_part / max(len(_MARKETS), 1),
        )
