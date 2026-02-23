"""API endpoints for Natural Language Compliance Queries."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.nl_compliance_query import NLComplianceQueryService


logger = structlog.get_logger()
router = APIRouter()


class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query")


class QueryResultSchema(BaseModel):
    id: str
    answer: str
    structured_data: list[dict[str, Any]]
    sources: list[dict[str, str]]
    confidence: str
    follow_up_suggestions: list[str]
    execution_time_ms: float


class FeedbackRequest(BaseModel):
    query_id: str = Field(...)
    helpful: bool = Field(...)
    comment: str = Field(default="")


class QueryStatsSchema(BaseModel):
    total_queries: int
    by_intent: dict[str, int]
    avg_execution_time_ms: float
    positive_feedback_rate: float
    most_common_topics: list[str]


@router.post("/query", response_model=QueryResultSchema, summary="Execute natural language query")
async def execute_query(request: QueryRequest, db: DB) -> QueryResultSchema:
    service = NLComplianceQueryService(db=db)
    r = await service.query(request.query)
    return QueryResultSchema(
        id=str(r.id),
        answer=r.answer,
        structured_data=r.structured_data,
        sources=r.sources,
        confidence=r.confidence.value,
        follow_up_suggestions=r.follow_up_suggestions,
        execution_time_ms=r.execution_time_ms,
    )


@router.post("/feedback", status_code=status.HTTP_201_CREATED, summary="Submit query feedback")
async def submit_feedback(request: FeedbackRequest, db: DB) -> dict:
    service = NLComplianceQueryService(db=db)
    await service.submit_feedback(UUID(request.query_id), request.helpful, request.comment)
    return {"status": "recorded"}


@router.get("/history", summary="Get query history")
async def get_history(db: DB, limit: int = 20) -> list[dict]:
    service = NLComplianceQueryService(db=db)
    return service.get_query_history(limit=limit)


@router.get("/stats", response_model=QueryStatsSchema, summary="Get query stats")
async def get_stats(db: DB) -> QueryStatsSchema:
    service = NLComplianceQueryService(db=db)
    s = service.get_stats()
    return QueryStatsSchema(
        total_queries=s.total_queries,
        by_intent=s.by_intent,
        avg_execution_time_ms=s.avg_execution_time_ms,
        positive_feedback_rate=s.positive_feedback_rate,
        most_common_topics=s.most_common_topics,
    )
