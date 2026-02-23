"""Natural Language Compliance Query models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class QueryIntent(str, Enum):
    VIOLATION_SEARCH = "violation_search"
    REGULATION_LOOKUP = "regulation_lookup"
    POSTURE_STATUS = "posture_status"
    AUDIT_SEARCH = "audit_search"
    COMPARISON = "comparison"
    RECOMMENDATION = "recommendation"
    TREND_ANALYSIS = "trend_analysis"


class ResultConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class NLQuery:
    id: UUID = field(default_factory=uuid4)
    raw_query: str = ""
    intent: QueryIntent = QueryIntent.VIOLATION_SEARCH
    entities: dict[str, Any] = field(default_factory=dict)
    confidence: ResultConfidence = ResultConfidence.HIGH
    submitted_at: datetime | None = None


@dataclass
class QueryResult:
    id: UUID = field(default_factory=uuid4)
    query_id: UUID = field(default_factory=uuid4)
    answer: str = ""
    structured_data: list[dict[str, Any]] = field(default_factory=list)
    sources: list[dict[str, str]] = field(default_factory=list)
    confidence: ResultConfidence = ResultConfidence.HIGH
    follow_up_suggestions: list[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    generated_at: datetime | None = None


@dataclass
class QueryFeedback:
    id: UUID = field(default_factory=uuid4)
    query_id: UUID = field(default_factory=uuid4)
    helpful: bool = True
    comment: str = ""
    created_at: datetime | None = None


@dataclass
class QueryStats:
    total_queries: int = 0
    by_intent: dict[str, int] = field(default_factory=dict)
    avg_execution_time_ms: float = 0.0
    positive_feedback_rate: float = 0.0
    most_common_topics: list[str] = field(default_factory=list)
