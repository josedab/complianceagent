"""RAG Pipeline - Retrieval-Augmented Generation for compliance context."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID

import structlog

logger = structlog.get_logger()


class RAGSource(str, Enum):
    """Types of sources for RAG context."""
    REGULATION = "regulation"
    REQUIREMENT = "requirement"
    CODEBASE = "codebase"
    MAPPING = "mapping"
    DOCUMENTATION = "documentation"
    AUDIT = "audit"
    KNOWLEDGE_GRAPH = "knowledge_graph"


@dataclass
class RAGDocument:
    """A document retrieved for RAG context."""
    id: str
    source: RAGSource
    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    relevance_score: float = 0.0
    
    # For citations
    url: str | None = None
    section: str | None = None
    
    def to_context_string(self, max_length: int = 2000) -> str:
        """Convert to context string for prompt."""
        content = self.content[:max_length]
        header = f"[{self.source.value.upper()}] {self.title}"
        if self.section:
            header += f" - {self.section}"
        return f"{header}\n{content}"


@dataclass
class RAGContext:
    """Context assembled for a query."""
    query: str
    documents: list[RAGDocument] = field(default_factory=list)
    total_tokens: int = 0
    
    # Query understanding
    detected_intent: str | None = None
    detected_entities: list[dict[str, Any]] = field(default_factory=list)
    
    def get_context_string(self, max_documents: int = 10, max_total_length: int = 10000) -> str:
        """Get combined context string for prompt."""
        contexts = []
        total_length = 0
        
        for doc in self.documents[:max_documents]:
            doc_context = doc.to_context_string()
            if total_length + len(doc_context) > max_total_length:
                break
            contexts.append(doc_context)
            total_length += len(doc_context)
        
        return "\n\n---\n\n".join(contexts)
    
    def get_citations(self) -> list[dict[str, Any]]:
        """Get citation info for all documents."""
        return [
            {
                "id": doc.id,
                "source": doc.source.value,
                "title": doc.title,
                "section": doc.section,
                "url": doc.url,
            }
            for doc in self.documents
        ]


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline for compliance queries."""

    def __init__(
        self,
        elasticsearch_client=None,
        db_session=None,
    ):
        self.es = elasticsearch_client
        self.db = db_session

    async def retrieve(
        self,
        query: str,
        organization_id: UUID,
        repository: str | None = None,
        regulations: list[str] | None = None,
        max_documents: int = 10,
    ) -> RAGContext:
        """Retrieve relevant context for a query."""
        context = RAGContext(query=query)
        
        # Analyze query to understand intent
        context.detected_intent = self._detect_intent(query)
        context.detected_entities = self._extract_entities(query)
        
        # Retrieve from multiple sources based on intent
        documents = []
        
        # Always search regulations if relevant
        if self._should_search_regulations(context):
            reg_docs = await self._search_regulations(
                query, organization_id, regulations
            )
            documents.extend(reg_docs)
        
        # Search requirements
        if self._should_search_requirements(context):
            req_docs = await self._search_requirements(
                query, organization_id, regulations
            )
            documents.extend(req_docs)
        
        # Search codebase if repository context
        if repository and self._should_search_codebase(context):
            code_docs = await self._search_codebase(
                query, organization_id, repository
            )
            documents.extend(code_docs)
        
        # Search mappings
        if self._should_search_mappings(context):
            mapping_docs = await self._search_mappings(
                query, organization_id, repository
            )
            documents.extend(mapping_docs)
        
        # Sort by relevance and limit
        documents.sort(key=lambda d: d.relevance_score, reverse=True)
        context.documents = documents[:max_documents]
        
        logger.info(
            "RAG retrieval completed",
            query=query[:100],
            documents_found=len(context.documents),
            intent=context.detected_intent,
        )
        
        return context

    def _detect_intent(self, query: str) -> str:
        """Detect the intent of the query."""
        query_lower = query.lower()
        
        # Check for compliance status queries
        if any(phrase in query_lower for phrase in [
            "am i compliant", "is my code compliant", "compliance status",
            "are we compliant", "compliance check"
        ]):
            return "compliance_status"
        
        # Check for explanation queries
        if any(phrase in query_lower for phrase in [
            "explain", "what is", "what does", "how does", "why",
            "tell me about", "describe"
        ]):
            return "explanation"
        
        # Check for action queries
        if any(phrase in query_lower for phrase in [
            "fix", "generate", "create", "make", "implement",
            "add", "remove", "update", "change"
        ]):
            return "action"
        
        # Check for finding/locating queries
        if any(phrase in query_lower for phrase in [
            "where is", "find", "show me", "which files",
            "affected", "impacted", "related"
        ]):
            return "locate"
        
        # Check for comparison queries
        if any(phrase in query_lower for phrase in [
            "compare", "difference", "between", "versus",
            "vs", "differ"
        ]):
            return "comparison"
        
        return "general"

    def _extract_entities(self, query: str) -> list[dict[str, Any]]:
        """Extract entities from the query."""
        entities = []
        query_lower = query.lower()
        
        # Extract regulation mentions
        regulations = {
            "gdpr": "GDPR",
            "ccpa": "CCPA",
            "hipaa": "HIPAA",
            "pci-dss": "PCI-DSS",
            "pci dss": "PCI-DSS",
            "eu ai act": "EU AI Act",
            "sox": "SOX",
            "iso 27001": "ISO 27001",
            "soc 2": "SOC 2",
        }
        
        for pattern, name in regulations.items():
            if pattern in query_lower:
                entities.append({"type": "regulation", "value": name})
        
        # Extract article references
        import re
        article_pattern = r"article\s+(\d+)"
        for match in re.finditer(article_pattern, query_lower):
            entities.append({"type": "article", "value": match.group(1)})
        
        # Extract file paths
        path_pattern = r"[\w/\\.-]+\.(py|js|ts|java|go|rb|php|cs)"
        for match in re.finditer(path_pattern, query):
            entities.append({"type": "file_path", "value": match.group(0)})
        
        return entities

    def _should_search_regulations(self, context: RAGContext) -> bool:
        """Determine if we should search regulations."""
        intents_needing_regs = ["explanation", "compliance_status", "comparison", "general"]
        return context.detected_intent in intents_needing_regs or any(
            e["type"] == "regulation" for e in context.detected_entities
        )

    def _should_search_requirements(self, context: RAGContext) -> bool:
        """Determine if we should search requirements."""
        return context.detected_intent in ["compliance_status", "locate", "action", "general"]

    def _should_search_codebase(self, context: RAGContext) -> bool:
        """Determine if we should search codebase."""
        return context.detected_intent in ["compliance_status", "locate", "action"] or any(
            e["type"] == "file_path" for e in context.detected_entities
        )

    def _should_search_mappings(self, context: RAGContext) -> bool:
        """Determine if we should search mappings."""
        return context.detected_intent in ["compliance_status", "locate"]

    async def _search_regulations(
        self,
        query: str,
        organization_id: UUID,
        regulations: list[str] | None,
    ) -> list[RAGDocument]:
        """Search regulations using Elasticsearch."""
        documents = []
        
        if self.es:
            # Build Elasticsearch query
            es_query = {
                "bool": {
                    "must": [
                        {"multi_match": {
                            "query": query,
                            "fields": ["name^3", "description^2", "content"],
                        }},
                    ]
                }
            }
            
            if regulations:
                es_query["bool"]["filter"] = [
                    {"terms": {"framework": regulations}}
                ]
            
            try:
                response = await self.es.search(
                    index="regulations",
                    body={"query": es_query, "size": 5},
                )
                
                for hit in response.get("hits", {}).get("hits", []):
                    source = hit["_source"]
                    documents.append(RAGDocument(
                        id=hit["_id"],
                        source=RAGSource.REGULATION,
                        title=source.get("name", "Unknown Regulation"),
                        content=source.get("description", "") + "\n" + source.get("content", "")[:1500],
                        relevance_score=hit["_score"],
                        metadata={"framework": source.get("framework")},
                    ))
            except Exception as e:
                logger.warning(f"Elasticsearch search failed: {e}")
        
        # Fallback to database search if no ES results
        if not documents and self.db:
            documents = await self._db_search_regulations(query, regulations)
        
        return documents

    async def _db_search_regulations(
        self,
        query: str,
        regulations: list[str] | None,
    ) -> list[RAGDocument]:
        """Database fallback for regulation search."""
        if not self.db:
            return []
        
        from sqlalchemy import select, or_
        from app.models.regulation import Regulation
        
        stmt = select(Regulation).where(
            or_(
                Regulation.name.ilike(f"%{query}%"),
                Regulation.description.ilike(f"%{query}%"),
            )
        ).limit(5)
        
        if regulations:
            stmt = stmt.where(Regulation.framework.in_(regulations))
        
        result = await self.db.execute(stmt)
        regs = list(result.scalars().all())
        
        return [
            RAGDocument(
                id=str(reg.id),
                source=RAGSource.REGULATION,
                title=reg.name,
                content=reg.description or "",
                relevance_score=0.8,
                metadata={"framework": reg.framework.value if reg.framework else None},
            )
            for reg in regs
        ]

    async def _search_requirements(
        self,
        query: str,
        organization_id: UUID,
        regulations: list[str] | None,
    ) -> list[RAGDocument]:
        """Search requirements."""
        documents = []
        
        if self.db:
            from sqlalchemy import select, or_
            from sqlalchemy.orm import selectinload
            from app.models.requirement import Requirement
            from app.models.regulation import Regulation
            
            stmt = (
                select(Requirement)
                .options(selectinload(Requirement.regulation))
                .where(
                    or_(
                        Requirement.title.ilike(f"%{query}%"),
                        Requirement.description.ilike(f"%{query}%"),
                    )
                )
                .limit(5)
            )
            
            result = await self.db.execute(stmt)
            requirements = list(result.scalars().all())
            
            for req in requirements:
                documents.append(RAGDocument(
                    id=str(req.id),
                    source=RAGSource.REQUIREMENT,
                    title=f"[{req.reference_id}] {req.title}",
                    content=req.description,
                    relevance_score=0.75,
                    section=req.reference_id,
                    metadata={
                        "regulation": req.regulation.name if req.regulation else None,
                        "category": req.category,
                        "obligation_type": req.obligation_type,
                    },
                ))
        
        return documents

    async def _search_codebase(
        self,
        query: str,
        organization_id: UUID,
        repository: str,
    ) -> list[RAGDocument]:
        """Search codebase for relevant code."""
        documents = []
        
        if self.es:
            try:
                es_query = {
                    "bool": {
                        "must": [
                            {"match": {"content": query}},
                            {"term": {"repository": repository}},
                        ]
                    }
                }
                
                response = await self.es.search(
                    index="codebase_files",
                    body={"query": es_query, "size": 5},
                )
                
                for hit in response.get("hits", {}).get("hits", []):
                    source = hit["_source"]
                    documents.append(RAGDocument(
                        id=hit["_id"],
                        source=RAGSource.CODEBASE,
                        title=source.get("path", "Unknown File"),
                        content=source.get("content", "")[:1500],
                        relevance_score=hit["_score"],
                        metadata={
                            "language": source.get("language"),
                            "repository": source.get("repository"),
                        },
                    ))
            except Exception as e:
                logger.warning(f"Codebase search failed: {e}")
        
        return documents

    async def _search_mappings(
        self,
        query: str,
        organization_id: UUID,
        repository: str | None,
    ) -> list[RAGDocument]:
        """Search compliance mappings."""
        documents = []
        
        if self.db:
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            from app.models.codebase import CodebaseMapping
            
            stmt = (
                select(CodebaseMapping)
                .options(
                    selectinload(CodebaseMapping.requirement),
                    selectinload(CodebaseMapping.repository),
                )
                .limit(5)
            )
            
            if repository:
                from app.models.codebase import Repository
                stmt = stmt.join(Repository).where(Repository.full_name == repository)
            
            result = await self.db.execute(stmt)
            mappings = list(result.scalars().all())
            
            for mapping in mappings:
                if mapping.requirement:
                    content = f"Requirement: {mapping.requirement.title}\n"
                    content += f"Status: {mapping.compliance_status.value if mapping.compliance_status else 'unknown'}\n"
                    content += f"Affected files: {', '.join(mapping.affected_files or [])}\n"
                    if mapping.gaps:
                        content += f"Gaps: {len(mapping.gaps)} identified\n"
                    
                    documents.append(RAGDocument(
                        id=str(mapping.id),
                        source=RAGSource.MAPPING,
                        title=f"Mapping: {mapping.requirement.title}",
                        content=content,
                        relevance_score=0.7,
                        metadata={
                            "compliance_status": mapping.compliance_status.value if mapping.compliance_status else None,
                            "repository": mapping.repository.full_name if mapping.repository else None,
                        },
                    ))
        
        return documents

    async def search_similar(
        self,
        document_id: str,
        source: RAGSource,
        max_results: int = 5,
    ) -> list[RAGDocument]:
        """Find similar documents to a given document."""
        if self.es:
            try:
                response = await self.es.search(
                    index=f"{source.value}s",
                    body={
                        "query": {
                            "more_like_this": {
                                "fields": ["title", "content"],
                                "like": [{"_index": f"{source.value}s", "_id": document_id}],
                                "min_term_freq": 1,
                                "max_query_terms": 12,
                            }
                        },
                        "size": max_results,
                    },
                )
                
                return [
                    RAGDocument(
                        id=hit["_id"],
                        source=source,
                        title=hit["_source"].get("title", ""),
                        content=hit["_source"].get("content", "")[:1000],
                        relevance_score=hit["_score"],
                    )
                    for hit in response.get("hits", {}).get("hits", [])
                ]
            except Exception as e:
                logger.warning(f"Similar search failed: {e}")
        
        return []
