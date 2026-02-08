"""Natural Language Compliance Query Engine models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class QueryIntent(str, Enum):
    """Classified intent of a natural language query."""

    REGULATION_LOOKUP = "regulation_lookup"
    CODE_SEARCH = "code_search"
    VIOLATION_QUERY = "violation_query"
    AUDIT_QUERY = "audit_query"
    STATUS_CHECK = "status_check"
    COMPARISON = "comparison"
    RECOMMENDATION = "recommendation"
    GENERAL = "general"


class SourceType(str, Enum):
    """Types of context sources for RAG."""

    REGULATION = "regulation"
    CODEBASE = "codebase"
    EVIDENCE = "evidence"
    POLICY = "policy"
    AUDIT_LOG = "audit_log"


@dataclass
class QuerySource:
    """A source used to answer a query."""

    source_type: SourceType = SourceType.REGULATION
    title: str = ""
    reference: str = ""
    relevance_score: float = 0.0
    snippet: str = ""


@dataclass
class CodeReference:
    """A code reference in a query result."""

    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    snippet: str = ""
    language: str = ""
    relevance: float = 0.0


@dataclass
class QueryResult:
    """Result of a natural language query."""

    id: UUID = field(default_factory=uuid4)
    query: str = ""
    intent: QueryIntent = QueryIntent.GENERAL
    answer: str = ""
    confidence: float = 0.0
    sources: list[QuerySource] = field(default_factory=list)
    code_references: list[CodeReference] = field(default_factory=list)
    follow_up_suggestions: list[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    timestamp: datetime | None = None


@dataclass
class QueryHistory:
    """A stored query for history/analytics."""

    id: UUID = field(default_factory=uuid4)
    query: str = ""
    intent: QueryIntent = QueryIntent.GENERAL
    answer_preview: str = ""
    was_helpful: bool | None = None
    timestamp: datetime | None = None
