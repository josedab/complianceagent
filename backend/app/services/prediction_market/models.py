"""Compliance Impact Prediction Market models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID


class MarketType(str, Enum):
    """Type of prediction market."""

    BINARY = "binary"
    SCALAR = "scalar"


class MarketStatus(str, Enum):
    """Status of a prediction market."""

    OPEN = "open"
    CLOSED = "closed"
    RESOLVED = "resolved"
    DISPUTED = "disputed"


@dataclass
class PredictionMarket:
    """A prediction market for a regulatory event."""

    id: UUID
    title: str
    description: str
    market_type: MarketType = MarketType.BINARY
    status: MarketStatus = MarketStatus.OPEN
    regulation: str = ""
    jurisdiction: str = ""
    current_probability: float = 0.5
    total_volume: float = 0.0
    total_participants: int = 0
    resolution_criteria: str = ""
    resolution_date: datetime | None = None
    resolved_outcome: bool | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    closes_at: datetime | None = None


@dataclass
class MarketPosition:
    """A participant's position in a market."""

    id: UUID
    market_id: UUID
    participant_id: UUID
    position: str = "yes"
    shares: float = 0.0
    cost_basis: float = 0.0
    current_value: float = 0.0
    pnl: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PredictionRecord:
    """Historical prediction accuracy record."""

    participant_id: UUID
    display_name: str
    total_predictions: int = 0
    correct_predictions: int = 0
    brier_score: float = 0.0
    accuracy_rate: float = 0.0
    total_pnl: float = 0.0
    rank: int = 0
    is_superforecaster: bool = False


@dataclass
class MarketStats:
    """Aggregate market statistics."""

    total_markets: int = 0
    active_markets: int = 0
    resolved_markets: int = 0
    total_participants: int = 0
    total_volume: float = 0.0
    forecast_accuracy: float = 0.0
    avg_participants_per_market: float = 0.0
