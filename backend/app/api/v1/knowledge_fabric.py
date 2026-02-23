"""API endpoints for Compliance Knowledge Fabric."""


import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.knowledge_fabric import KnowledgeFabricService


logger = structlog.get_logger()
router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(...)
    scope: str = Field(default="all")
    limit: int = Field(default=10)


class SearchResultSchema(BaseModel):
    result_type: str
    title: str
    snippet: str
    relevance_score: float
    source: str


class SearchResponseSchema(BaseModel):
    id: str
    query: str
    results: list[SearchResultSchema]
    total_count: int
    rag_answer: str
    sources_cited: list[dict[str, str]]
    execution_time_ms: float


class EmbeddingStatsSchema(BaseModel):
    total_documents: int
    by_type: dict[str, int]
    index_size_mb: float
    embedding_model: str


@router.post("/search", response_model=SearchResponseSchema, summary="Unified compliance search")
async def search(request: SearchRequest, db: DB) -> SearchResponseSchema:
    service = KnowledgeFabricService(db=db)
    r = await service.search(query=request.query, scope=request.scope, limit=request.limit)
    return SearchResponseSchema(
        id=str(r.id), query=r.query,
        results=[SearchResultSchema(result_type=s.result_type.value, title=s.title, snippet=s.snippet, relevance_score=s.relevance_score, source=s.source) for s in r.results],
        total_count=r.total_count, rag_answer=r.rag_answer, sources_cited=r.sources_cited, execution_time_ms=r.execution_time_ms,
    )


@router.get("/stats", response_model=EmbeddingStatsSchema, summary="Get embedding stats")
async def get_stats(db: DB) -> EmbeddingStatsSchema:
    service = KnowledgeFabricService(db=db)
    s = service.get_embedding_stats()
    return EmbeddingStatsSchema(total_documents=s.total_documents, by_type=s.by_type, index_size_mb=s.index_size_mb, embedding_model=s.embedding_model)


@router.get("/history", summary="Get search history")
async def get_history(db: DB, limit: int = 20) -> list[dict]:
    service = KnowledgeFabricService(db=db)
    return service.get_search_history(limit=limit)
