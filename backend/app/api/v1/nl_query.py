"""API endpoints for Natural Language Compliance Query Engine."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.nl_query import NLQueryService

logger = structlog.get_logger()
router = APIRouter()


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="Natural language query")
    context: dict[str, Any] | None = Field(default=None, description="Additional context")


class FeedbackRequest(BaseModel):
    query_id: str = Field(...)
    helpful: bool = Field(...)


class SourceSchema(BaseModel):
    source_type: str
    title: str
    reference: str
    relevance_score: float
    snippet: str


class CodeRefSchema(BaseModel):
    file_path: str
    line_start: int
    line_end: int
    snippet: str
    language: str
    relevance: float


class QueryResultSchema(BaseModel):
    id: str
    query: str
    intent: str
    answer: str
    confidence: float
    sources: list[SourceSchema]
    code_references: list[CodeRefSchema]
    follow_up_suggestions: list[str]
    processing_time_ms: float


class QueryHistorySchema(BaseModel):
    id: str
    query: str
    intent: str
    answer_preview: str
    was_helpful: bool | None
    timestamp: str | None


@router.post(
    "/query",
    response_model=QueryResultSchema,
    summary="Execute natural language compliance query",
    description="Ask compliance questions in natural language with RAG-powered answers",
)
async def execute_query(request: QueryRequest, db: DB, copilot: CopilotDep) -> QueryResultSchema:
    service = NLQueryService(db=db, copilot_client=copilot)
    result = await service.query(text=request.query, context=request.context)
    return QueryResultSchema(
        id=str(result.id),
        query=result.query,
        intent=result.intent.value,
        answer=result.answer,
        confidence=result.confidence,
        sources=[SourceSchema(
            source_type=s.source_type.value, title=s.title, reference=s.reference,
            relevance_score=s.relevance_score, snippet=s.snippet,
        ) for s in result.sources],
        code_references=[CodeRefSchema(
            file_path=c.file_path, line_start=c.line_start, line_end=c.line_end,
            snippet=c.snippet, language=c.language, relevance=c.relevance,
        ) for c in result.code_references],
        follow_up_suggestions=result.follow_up_suggestions,
        processing_time_ms=result.processing_time_ms,
    )


@router.get(
    "/history",
    response_model=list[QueryHistorySchema],
    summary="Get query history",
)
async def get_history(db: DB, copilot: CopilotDep, limit: int = 20) -> list[QueryHistorySchema]:
    service = NLQueryService(db=db, copilot_client=copilot)
    history = await service.get_history(limit=limit)
    return [QueryHistorySchema(
        id=str(h.id), query=h.query, intent=h.intent.value,
        answer_preview=h.answer_preview, was_helpful=h.was_helpful,
        timestamp=h.timestamp.isoformat() if h.timestamp else None,
    ) for h in history]


@router.post(
    "/feedback",
    summary="Submit query feedback",
)
async def submit_feedback(request: FeedbackRequest, db: DB, copilot: CopilotDep) -> dict:
    service = NLQueryService(db=db, copilot_client=copilot)
    success = await service.submit_feedback(UUID(request.query_id), request.helpful)
    if not success:
        raise HTTPException(status_code=404, detail="Query not found")
    return {"status": "recorded"}


@router.get(
    "/intents",
    summary="List supported query intents",
)
async def list_intents() -> list[dict]:
    from app.services.nl_query.models import QueryIntent
    return [{"intent": i.value, "description": i.value.replace("_", " ").title()} for i in QueryIntent]
