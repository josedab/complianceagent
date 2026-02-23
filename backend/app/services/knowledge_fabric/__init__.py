"""Compliance Knowledge Fabric service."""

from app.services.knowledge_fabric.models import (
    EmbeddingStats,
    ResultType,
    SearchResult,
    SearchScope,
    UnifiedSearchResponse,
)
from app.services.knowledge_fabric.service import KnowledgeFabricService


__all__ = [
    "EmbeddingStats",
    "KnowledgeFabricService",
    "ResultType",
    "SearchResult",
    "SearchScope",
    "UnifiedSearchResponse",
]
