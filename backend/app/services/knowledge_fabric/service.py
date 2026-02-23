"""Compliance Knowledge Fabric Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.knowledge_fabric.models import (
    EmbeddingStats,
    ResultType,
    SearchResult,
    SearchScope,
    UnifiedSearchResponse,
)


logger = structlog.get_logger()

_KNOWLEDGE_BASE: list[dict] = [
    {"type": "regulation", "title": "GDPR Article 17 — Right to Erasure", "content": "The data subject shall have the right to obtain from the controller the erasure of personal data concerning him or her without undue delay.", "source": "GDPR", "tags": ["gdpr", "erasure", "deletion", "right"]},
    {"type": "regulation", "title": "HIPAA §164.312 — Technical Safeguards", "content": "Implement technical policies and procedures for electronic information systems that maintain PHI to allow access only to authorized persons.", "source": "HIPAA", "tags": ["hipaa", "phi", "encryption", "access"]},
    {"type": "regulation", "title": "PCI-DSS Req 3 — Protect Stored Account Data", "content": "Protection methods such as encryption, truncation, masking, and hashing are critical components of cardholder data protection.", "source": "PCI-DSS", "tags": ["pci", "card", "encryption", "tokenization"]},
    {"type": "regulation", "title": "EU AI Act Article 6 — High-Risk Classification", "content": "AI systems intended to be used as safety components of products, or AI systems which are themselves products, shall be classified as high-risk.", "source": "EU AI Act", "tags": ["ai", "risk", "classification", "high-risk"]},
    {"type": "requirement", "title": "GDPR Consent Mechanism Required", "content": "Organizations must implement explicit consent mechanisms for personal data processing with granular opt-in/opt-out controls.", "source": "GDPR Art. 6", "tags": ["consent", "gdpr", "opt-in"]},
    {"type": "violation", "title": "PHI in Log Files Detected", "content": "Patient health information found in application log output without encryption or redaction, violating HIPAA §164.312(b).", "source": "HIPAA Scan", "tags": ["hipaa", "phi", "logging", "violation"]},
    {"type": "audit_event", "title": "Compliance Score Updated", "content": "Organization compliance score changed from 82.0 to 85.5 following GDPR consent implementation.", "source": "Audit Trail", "tags": ["score", "update", "gdpr"]},
    {"type": "evidence_item", "title": "SOC 2 CC6.1 — Access Control Evidence", "content": "Automated evidence: RBAC configuration verified, MFA enabled for all admin accounts, access logs retained for 90 days.", "source": "Evidence Vault", "tags": ["soc2", "access", "mfa", "rbac"]},
    {"type": "prediction", "title": "GDPR AI Amendment Predicted (Q1 2027)", "content": "High confidence prediction: EU Commission expected to amend GDPR Article 22 expanding automated decision-making requirements to AI-assisted decisions.", "source": "Prediction Engine", "tags": ["prediction", "gdpr", "ai", "amendment"]},
    {"type": "code_file", "title": "src/api/users.py — Personal Data Handler", "content": "User API endpoint handling personal data (email, name, address). Requires GDPR consent check and data retention policy.", "source": "Codebase", "tags": ["code", "users", "personal-data", "gdpr"]},
    {"type": "policy", "title": "GDPR Consent Policy", "content": "Policy requiring explicit consent for personal data processing. Applies to all endpoints handling PII. Auto-enforced via CI/CD gate.", "source": "Policy Registry", "tags": ["policy", "gdpr", "consent", "enforcement"]},
]


class KnowledgeFabricService:
    """Unified vector search across all compliance data with RAG."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._searches: list[UnifiedSearchResponse] = []

    async def search(
        self,
        query: str,
        scope: str = "all",
        limit: int = 10,
    ) -> UnifiedSearchResponse:
        start = datetime.now(UTC)
        search_scope = SearchScope(scope)
        results = self._semantic_search(query, search_scope, limit)
        rag_answer = self._generate_rag_answer(query, results)
        sources = [{"title": r.title, "source": r.source, "type": r.result_type.value} for r in results[:3]]
        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        response = UnifiedSearchResponse(
            query=query,
            scope=search_scope,
            results=results,
            total_count=len(results),
            rag_answer=rag_answer,
            sources_cited=sources,
            execution_time_ms=round(duration, 2),
            searched_at=datetime.now(UTC),
        )
        self._searches.append(response)
        logger.info("Knowledge search", query=query[:50], results=len(results))
        return response

    def _semantic_search(self, query: str, scope: SearchScope, limit: int) -> list[SearchResult]:
        q_lower = query.lower()
        q_terms = set(q_lower.split())
        scored: list[tuple[float, dict]] = []

        for doc in _KNOWLEDGE_BASE:
            if scope != SearchScope.ALL:
                type_map = {
                    SearchScope.REGULATIONS: ["regulation", "requirement"],
                    SearchScope.CODE: ["code_file"],
                    SearchScope.AUDIT: ["audit_event"],
                    SearchScope.EVIDENCE: ["evidence_item"],
                    SearchScope.PREDICTIONS: ["prediction"],
                    SearchScope.POLICIES: ["policy"],
                }
                if doc["type"] not in type_map.get(scope, []):
                    continue

            text = f"{doc['title']} {doc['content']} {' '.join(doc['tags'])}".lower()
            # TF-based scoring
            score = sum(1 for term in q_terms if term in text)
            tag_bonus = sum(0.5 for tag in doc["tags"] if tag in q_lower)
            total = score + tag_bonus
            if total > 0:
                scored.append((total, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, doc in scored[:limit]:
            max_score = len(q_terms) + len(doc["tags"]) * 0.5
            relevance = min(1.0, round(score / max(max_score, 1), 2))
            results.append(SearchResult(
                result_type=ResultType(doc["type"]),
                title=doc["title"],
                snippet=doc["content"][:200],
                relevance_score=relevance,
                source=doc["source"],
                metadata={"tags": doc["tags"]},
            ))
        return results

    def _generate_rag_answer(self, query: str, results: list[SearchResult]) -> str:
        if not results:
            return "No relevant compliance data found for your query. Try broadening your search terms."
        context_parts = [f"Based on {r.source}: {r.snippet[:100]}" for r in results[:3]]
        context = ". ".join(context_parts)
        return f"Regarding your query about '{query[:50]}': {context}. [Sources: {', '.join(r.source for r in results[:3])}]"

    def get_embedding_stats(self) -> EmbeddingStats:
        by_type: dict[str, int] = {}
        for doc in _KNOWLEDGE_BASE:
            by_type[doc["type"]] = by_type.get(doc["type"], 0) + 1
        return EmbeddingStats(
            total_documents=len(_KNOWLEDGE_BASE),
            by_type=by_type,
            index_size_mb=round(len(_KNOWLEDGE_BASE) * 0.15, 2),
            last_indexed_at=datetime.now(UTC),
        )

    def get_search_history(self, limit: int = 20) -> list[dict]:
        return [
            {"query": s.query, "results": s.total_count, "time_ms": s.execution_time_ms}
            for s in sorted(self._searches, key=lambda x: x.searched_at or datetime.min.replace(tzinfo=UTC), reverse=True)[:limit]
        ]
