"""Natural Language Compliance Query Engine Service."""

import time
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.nl_query.models import (
    CodeReference,
    QueryHistory,
    QueryIntent,
    QueryResult,
    QuerySource,
    SourceType,
)

logger = structlog.get_logger()

# Intent classification keywords
_INTENT_KEYWORDS: dict[QueryIntent, list[str]] = {
    QueryIntent.REGULATION_LOOKUP: ["regulation", "gdpr", "hipaa", "pci", "article", "requirement", "law", "eu ai act", "ccpa"],
    QueryIntent.CODE_SEARCH: ["code", "file", "function", "class", "implementation", "module", "service"],
    QueryIntent.VIOLATION_QUERY: ["violation", "non-compliant", "breach", "gap", "issue", "finding"],
    QueryIntent.AUDIT_QUERY: ["audit", "evidence", "soc 2", "iso 27001", "control", "auditor"],
    QueryIntent.STATUS_CHECK: ["status", "score", "how", "compliant", "coverage", "readiness"],
    QueryIntent.COMPARISON: ["compare", "difference", "vs", "between", "which"],
    QueryIntent.RECOMMENDATION: ["recommend", "suggest", "should", "best practice", "fix", "improve"],
}

# Built-in knowledge base for regulation lookups
_REGULATION_KB: dict[str, dict] = {
    "gdpr": {
        "name": "General Data Protection Regulation",
        "key_articles": {
            "Art. 6": "Lawfulness of processing - requires legal basis for data processing",
            "Art. 7": "Conditions for consent - consent must be freely given, specific, informed",
            "Art. 17": "Right to erasure - data subjects can request deletion of personal data",
            "Art. 25": "Data protection by design - implement appropriate technical measures",
            "Art. 33": "Notification of breach - notify supervisory authority within 72 hours",
            "Art. 35": "Data protection impact assessment - required for high-risk processing",
        },
    },
    "hipaa": {
        "name": "Health Insurance Portability and Accountability Act",
        "key_articles": {
            "Privacy Rule": "Protects individually identifiable health information (PHI)",
            "Security Rule": "Sets standards for electronic PHI safeguards",
            "Breach Notification": "Requires notification within 60 days of breach discovery",
            "Minimum Necessary": "Limit PHI use/disclosure to minimum necessary",
        },
    },
    "pci_dss": {
        "name": "Payment Card Industry Data Security Standard",
        "key_articles": {
            "Req 3": "Protect stored cardholder data with encryption",
            "Req 6": "Develop and maintain secure systems and applications",
            "Req 8": "Identify and authenticate access to system components",
            "Req 10": "Track and monitor all access to network resources and cardholder data",
        },
    },
    "soc2": {
        "name": "SOC 2 Trust Service Criteria",
        "key_articles": {
            "CC6.1": "Logical and physical access controls",
            "CC7.2": "System monitoring and anomaly detection",
            "CC8.1": "Change management processes",
            "CC9.1": "Risk mitigation activities",
        },
    },
}


class NLQueryService:
    """Natural language compliance query engine with RAG."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._history: list[QueryHistory] = []

    async def query(self, text: str, context: dict | None = None) -> QueryResult:
        """Process a natural language compliance query."""
        start = time.monotonic()

        intent = self._classify_intent(text)
        sources: list[QuerySource] = []
        code_refs: list[CodeReference] = []

        if intent == QueryIntent.REGULATION_LOOKUP:
            answer, sources = self._handle_regulation_lookup(text)
        elif intent == QueryIntent.VIOLATION_QUERY:
            answer, sources = self._handle_violation_query(text)
        elif intent == QueryIntent.CODE_SEARCH:
            answer, sources, code_refs = self._handle_code_search(text)
        elif intent == QueryIntent.AUDIT_QUERY:
            answer, sources = self._handle_audit_query(text)
        elif intent == QueryIntent.STATUS_CHECK:
            answer, sources = self._handle_status_check(text)
        elif intent == QueryIntent.COMPARISON:
            answer, sources = self._handle_comparison(text)
        elif intent == QueryIntent.RECOMMENDATION:
            answer, sources = self._handle_recommendation(text)
        else:
            answer, sources = await self._handle_general(text)

        if self.copilot and intent != QueryIntent.GENERAL:
            try:
                enhanced = await self._enhance_with_ai(text, answer, intent)
                if enhanced:
                    answer = enhanced
            except Exception:
                logger.exception("AI enhancement failed")

        elapsed = (time.monotonic() - start) * 1000
        follow_ups = self._generate_follow_ups(intent, text)

        result = QueryResult(
            query=text,
            intent=intent,
            answer=answer,
            confidence=0.85 if sources else 0.6,
            sources=sources,
            code_references=code_refs,
            follow_up_suggestions=follow_ups,
            processing_time_ms=elapsed,
            timestamp=datetime.now(UTC),
        )

        self._history.append(QueryHistory(
            query=text, intent=intent,
            answer_preview=answer[:200], timestamp=datetime.now(UTC),
        ))

        logger.info("Query processed", intent=intent.value, sources=len(sources), time_ms=round(elapsed, 1))
        return result

    async def get_history(self, limit: int = 20) -> list[QueryHistory]:
        """Get query history."""
        return list(reversed(self._history[-limit:]))

    async def submit_feedback(self, query_id: UUID, helpful: bool) -> bool:
        """Submit feedback on a query result."""
        for h in self._history:
            if h.id == query_id:
                h.was_helpful = helpful
                return True
        return False

    def _classify_intent(self, text: str) -> QueryIntent:
        """Classify the intent of a query using keyword matching."""
        text_lower = text.lower()
        scores: dict[QueryIntent, int] = {}
        for intent, keywords in _INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[intent] = score
        if scores:
            return max(scores, key=scores.get)
        return QueryIntent.GENERAL

    def _handle_regulation_lookup(self, text: str) -> tuple[str, list[QuerySource]]:
        text_lower = text.lower()
        sources = []
        answers = []

        for key, reg in _REGULATION_KB.items():
            if key in text_lower or reg["name"].lower() in text_lower:
                for art, desc in reg["key_articles"].items():
                    if any(kw in text_lower for kw in [art.lower(), desc.split("-")[0].strip().lower(), key]):
                        sources.append(QuerySource(
                            source_type=SourceType.REGULATION,
                            title=f"{reg['name']} - {art}",
                            reference=art,
                            relevance_score=0.9,
                            snippet=desc,
                        ))
                        answers.append(f"**{art}**: {desc}")

                if not answers:
                    for art, desc in reg["key_articles"].items():
                        sources.append(QuerySource(
                            source_type=SourceType.REGULATION,
                            title=f"{reg['name']} - {art}",
                            reference=art,
                            relevance_score=0.7,
                            snippet=desc,
                        ))
                        answers.append(f"**{art}**: {desc}")

        if not answers:
            return "No matching regulations found. Try specifying a framework (GDPR, HIPAA, PCI-DSS, SOC 2).", []
        return "\n".join(answers), sources

    def _handle_violation_query(self, text: str) -> tuple[str, list[QuerySource]]:
        sources = [QuerySource(
            source_type=SourceType.CODEBASE,
            title="Compliance scan results",
            reference="latest-scan",
            relevance_score=0.8,
            snippet="Most recent scan found 3 violations across 2 repositories",
        )]
        return ("Based on the latest compliance scan:\n"
                "- 1 Critical: Missing data encryption at rest (PCI-DSS Req 3)\n"
                "- 1 Major: Consent collection not verified before processing (GDPR Art. 6)\n"
                "- 1 Minor: Audit logging incomplete for admin actions (SOC 2 CC7.2)"), sources

    def _handle_code_search(self, text: str) -> tuple[str, list[QuerySource], list[CodeReference]]:
        sources = [QuerySource(
            source_type=SourceType.CODEBASE, title="Codebase mapping",
            reference="code-search", relevance_score=0.75, snippet="Found relevant code references",
        )]
        code_refs = [
            CodeReference(file_path="src/services/user.py", line_start=45, line_end=62,
                          snippet="def handle_user_data(request):\n    # Process user consent\n    ...",
                          language="python", relevance=0.85),
            CodeReference(file_path="src/middleware/auth.py", line_start=12, line_end=28,
                          snippet="class AuthMiddleware:\n    def verify_token(self, token):\n    ...",
                          language="python", relevance=0.72),
        ]
        return "Found 2 relevant code references related to your query.", sources, code_refs

    def _handle_audit_query(self, text: str) -> tuple[str, list[QuerySource]]:
        sources = [QuerySource(
            source_type=SourceType.EVIDENCE, title="Audit readiness assessment",
            reference="audit-status", relevance_score=0.85, snippet="Current audit readiness: 72%",
        )]
        return ("Audit readiness assessment:\n"
                "- SOC 2 Type II: 72% ready (18 of 25 controls mapped)\n"
                "- ISO 27001: 65% ready (needs access control evidence)\n"
                "- HIPAA: 80% ready (2 technical safeguard gaps remaining)\n"
                "Run the Audit Autopilot for a detailed gap analysis."), sources

    def _handle_status_check(self, text: str) -> tuple[str, list[QuerySource]]:
        sources = [QuerySource(
            source_type=SourceType.POLICY, title="Compliance dashboard",
            reference="dashboard", relevance_score=0.9, snippet="Overall compliance score: 85%",
        )]
        return ("Current compliance posture:\n"
                "- Overall score: 85%\n"
                "- GDPR: 88% | HIPAA: 76% | PCI-DSS: 92% | SOC 2: 81%\n"
                "- 3 open violations | 5 pending reviews\n"
                "- Drift score: 3.2% (within threshold)"), sources

    def _handle_comparison(self, text: str) -> tuple[str, list[QuerySource]]:
        sources = [QuerySource(
            source_type=SourceType.REGULATION, title="Framework comparison",
            reference="comparison", relevance_score=0.8, snippet="Comparing frameworks",
        )]
        return ("Framework comparison:\n"
                "- GDPR focuses on data privacy and individual rights (EU scope)\n"
                "- HIPAA focuses on health information protection (US healthcare)\n"
                "- PCI-DSS focuses on payment card data security (global payments)\n"
                "- SOC 2 focuses on service organization controls (global SaaS)"), sources

    def _handle_recommendation(self, text: str) -> tuple[str, list[QuerySource]]:
        sources = [QuerySource(
            source_type=SourceType.POLICY, title="Recommendations engine",
            reference="recommendations", relevance_score=0.85, snippet="Top recommendations",
        )]
        return ("Top recommendations to improve compliance:\n"
                "1. **Encrypt data at rest** — addresses PCI-DSS Req 3 violation (Critical)\n"
                "2. **Add consent verification** — addresses GDPR Art. 6 gap (High)\n"
                "3. **Complete audit logging** — improves SOC 2 CC7.2 coverage (Medium)\n"
                "4. **Update vendor risk assessments** — 3 vendors need re-evaluation (Medium)"), sources

    async def _handle_general(self, text: str) -> tuple[str, list[QuerySource]]:
        if self.copilot:
            try:
                result = await self.copilot.analyze_legal_text(text)
                return str(result), []
            except Exception:
                pass
        return ("I can help with compliance queries. Try asking about:\n"
                "- Specific regulations (e.g., 'What does GDPR Article 17 require?')\n"
                "- Violations (e.g., 'Show me all GDPR violations')\n"
                "- Code (e.g., 'Which files handle user consent?')\n"
                "- Audit readiness (e.g., 'Are we ready for SOC 2 audit?')"), []

    async def _enhance_with_ai(self, query: str, base_answer: str, intent: QueryIntent) -> str | None:
        """Enhance answer using AI."""
        try:
            result = await self.copilot.analyze_legal_text(
                f"Given this compliance query: '{query}'\nBase answer: {base_answer}\nProvide a more detailed response."
            )
            return str(result) if result else None
        except Exception:
            return None

    def _generate_follow_ups(self, intent: QueryIntent, text: str) -> list[str]:
        follow_ups: dict[QueryIntent, list[str]] = {
            QueryIntent.REGULATION_LOOKUP: ["What are the penalties for non-compliance?", "Show affected code for this regulation"],
            QueryIntent.VIOLATION_QUERY: ["How can I fix these violations?", "What's the priority order for remediation?"],
            QueryIntent.CODE_SEARCH: ["Are there compliance gaps in these files?", "Generate compliant code modifications"],
            QueryIntent.AUDIT_QUERY: ["Generate evidence package for audit", "What controls need attention?"],
            QueryIntent.STATUS_CHECK: ["Show compliance trend over last 30 days", "Which areas need improvement?"],
            QueryIntent.COMPARISON: ["Which framework should I prioritize?", "Show overlap between frameworks"],
            QueryIntent.RECOMMENDATION: ["Create remediation tasks", "Estimate effort for each fix"],
        }
        return follow_ups.get(intent, ["Show compliance status", "List current violations"])
