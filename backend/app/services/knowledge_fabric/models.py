"""Compliance Knowledge Fabric models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class SearchScope(str, Enum):
    ALL = "all"
    REGULATIONS = "regulations"
    CODE = "code"
    AUDIT = "audit"
    EVIDENCE = "evidence"
    PREDICTIONS = "predictions"
    POLICIES = "policies"


class ResultType(str, Enum):
    REGULATION = "regulation"
    REQUIREMENT = "requirement"
    VIOLATION = "violation"
    AUDIT_EVENT = "audit_event"
    EVIDENCE_ITEM = "evidence_item"
    CODE_FILE = "code_file"
    PREDICTION = "prediction"
    POLICY = "policy"


@dataclass
class SearchResult:
    id: UUID = field(default_factory=uuid4)
    result_type: ResultType = ResultType.REGULATION
    title: str = ""
    snippet: str = ""
    relevance_score: float = 0.0
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedSearchResponse:
    id: UUID = field(default_factory=uuid4)
    query: str = ""
    scope: SearchScope = SearchScope.ALL
    results: list[SearchResult] = field(default_factory=list)
    total_count: int = 0
    rag_answer: str = ""
    sources_cited: list[dict[str, str]] = field(default_factory=list)
    execution_time_ms: float = 0.0
    searched_at: datetime | None = None


@dataclass
class EmbeddingStats:
    total_documents: int = 0
    by_type: dict[str, int] = field(default_factory=dict)
    index_size_mb: float = 0.0
    last_indexed_at: datetime | None = None
    embedding_model: str = "text-embedding-3-small"
