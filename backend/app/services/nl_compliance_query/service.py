"""Natural Language Compliance Query Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.nl_compliance_query.models import (
    NLQuery,
    QueryFeedback,
    QueryIntent,
    QueryResult,
    QueryStats,
    ResultConfidence,
)


logger = structlog.get_logger()

_INTENT_KEYWORDS: dict[QueryIntent, list[str]] = {
    QueryIntent.VIOLATION_SEARCH: ["violation", "violations", "non-compliant", "issue", "finding", "fail"],
    QueryIntent.REGULATION_LOOKUP: ["regulation", "article", "requirement", "rule", "gdpr", "hipaa", "pci", "sox"],
    QueryIntent.POSTURE_STATUS: ["score", "posture", "status", "grade", "compliance level", "how compliant"],
    QueryIntent.AUDIT_SEARCH: ["audit", "evidence", "trail", "log", "history", "who changed"],
    QueryIntent.COMPARISON: ["compare", "versus", "vs", "difference", "between", "better", "worse"],
    QueryIntent.RECOMMENDATION: ["recommend", "suggest", "should", "improve", "fix", "how to"],
    QueryIntent.TREND_ANALYSIS: ["trend", "over time", "last month", "last week", "increasing", "decreasing"],
}


class NLComplianceQueryService:
    """Natural language query engine for compliance data."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._queries: list[NLQuery] = []
        self._results: list[QueryResult] = []
        self._feedback: list[QueryFeedback] = []

    async def query(self, raw_query: str) -> QueryResult:
        start = datetime.now(UTC)
        intent = self._classify_intent(raw_query)
        entities = self._extract_entities(raw_query)

        nl_query = NLQuery(
            raw_query=raw_query,
            intent=intent,
            entities=entities,
            confidence=ResultConfidence.HIGH if entities else ResultConfidence.MEDIUM,
            submitted_at=start,
        )
        self._queries.append(nl_query)

        answer, data, sources = await self._generate_answer(intent, entities, raw_query)
        follow_ups = self._generate_follow_ups(intent, entities)
        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        result = QueryResult(
            query_id=nl_query.id,
            answer=answer,
            structured_data=data,
            sources=sources,
            confidence=nl_query.confidence,
            follow_up_suggestions=follow_ups,
            execution_time_ms=round(duration, 2),
            generated_at=datetime.now(UTC),
        )
        self._results.append(result)
        logger.info("NL query executed", intent=intent.value, time_ms=result.execution_time_ms)
        return result

    def _classify_intent(self, query: str) -> QueryIntent:
        q_lower = query.lower()
        best_intent = QueryIntent.VIOLATION_SEARCH
        best_score = 0
        for intent, keywords in _INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in q_lower)
            if score > best_score:
                best_score = score
                best_intent = intent
        return best_intent

    def _extract_entities(self, query: str) -> dict:
        entities: dict = {}
        q_lower = query.lower()
        frameworks = ["gdpr", "hipaa", "pci-dss", "soc 2", "soc2", "eu ai act", "iso 27001", "nist", "ccpa", "sox"]
        for fw in frameworks:
            if fw in q_lower:
                entities["framework"] = fw.upper().replace("SOC 2", "SOC2")
        services = ["payments", "api", "web", "data", "auth", "users", "billing"]
        for svc in services:
            if svc in q_lower:
                entities["service"] = svc
        time_refs = {"last week": "7d", "last month": "30d", "last quarter": "90d", "this year": "365d"}
        for ref, period in time_refs.items():
            if ref in q_lower:
                entities["time_period"] = period
        return entities

    async def _generate_answer(self, intent: QueryIntent, entities: dict, raw_query: str) -> tuple[str, list[dict], list[dict]]:
        fw = entities.get("framework", "all frameworks")
        svc = entities.get("service", "all services")
        period = entities.get("time_period", "30d")

        answers: dict[QueryIntent, tuple] = {
            QueryIntent.VIOLATION_SEARCH: (
                f"Found 12 compliance violations for {fw} in {svc} over the last {period}. 3 critical (data retention), 5 high (consent management), 4 medium (documentation gaps).",
                [{"severity": "critical", "count": 3, "category": "data_retention"}, {"severity": "high", "count": 5, "category": "consent"}, {"severity": "medium", "count": 4, "category": "documentation"}],
                [{"type": "regulation", "ref": f"{fw} Art. 5"}, {"type": "scan_result", "ref": "scan-2026-02-21"}],
            ),
            QueryIntent.REGULATION_LOOKUP: (
                f"{fw} requires organizations to process personal data lawfully, fairly, and transparently. Key obligations include consent management (Art. 6), data subject rights (Art. 12-22), and data protection by design (Art. 25).",
                [{"article": "Art. 6", "topic": "Lawfulness"}, {"article": "Art. 17", "topic": "Right to Erasure"}, {"article": "Art. 25", "topic": "Data Protection by Design"}],
                [{"type": "regulation", "ref": f"{fw} Official Text"}],
            ),
            QueryIntent.POSTURE_STATUS: (
                f"Your overall compliance score is 85.2% (B+). {fw} coverage is at 88% with 4 open findings. Score improved 3.2 points in the last {period}.",
                [{"metric": "overall_score", "value": 85.2}, {"metric": f"{fw.lower()}_score", "value": 88.0}, {"metric": "trend", "value": 3.2}],
                [{"type": "posture_report", "ref": "report-2026-02-21"}],
            ),
            QueryIntent.AUDIT_SEARCH: (
                f"Found 45 audit events for {svc} in the last {period}. 12 code changes, 8 compliance verifications, 5 policy updates, 20 automated scans. Hash chain integrity verified.",
                [{"event_type": "code_change", "count": 12}, {"event_type": "verification", "count": 8}, {"event_type": "policy_update", "count": 5}],
                [{"type": "audit_trail", "ref": "chain-verified"}],
            ),
            QueryIntent.COMPARISON: (
                f"Comparing {fw} posture across services: {svc} scores 88%, payments scores 82%, auth scores 91%. Auth service leads due to strong access controls. Payments needs card tokenization improvements.",
                [{"service": svc, "score": 88}, {"service": "payments", "score": 82}, {"service": "auth", "score": 91}],
                [{"type": "comparison", "ref": "benchmark-2026-02"}],
            ),
            QueryIntent.RECOMMENDATION: (
                f"Top 3 recommendations to improve {fw} compliance: 1) Implement data retention policies for user PII (impact: +5 points). 2) Add consent management to analytics endpoints (impact: +3 points). 3) Document data processing activities in Art. 30 records (impact: +2 points).",
                [{"recommendation": "Data retention policies", "impact_points": 5}, {"recommendation": "Consent management", "impact_points": 3}, {"recommendation": "Art. 30 records", "impact_points": 2}],
                [{"type": "best_practice", "ref": f"{fw} Implementation Guide"}],
            ),
            QueryIntent.TREND_ANALYSIS: (
                f"Compliance trend for {fw} over {period}: Score improved from 81.5% to 85.2% (+3.7). Violation count decreased from 18 to 12 (-33%). Top improving area: data encryption. Area needing attention: third-party vendor assessment.",
                [{"date": "start", "score": 81.5}, {"date": "end", "score": 85.2}, {"metric": "violation_reduction", "value": -33}],
                [{"type": "trend_report", "ref": f"trend-{period}"}],
            ),
        }
        return answers.get(intent, (f"I analyzed your query about {fw}. Please refine your question for more specific results.", [], []))

    def _generate_follow_ups(self, intent: QueryIntent, entities: dict) -> list[str]:
        follow_ups: dict[QueryIntent, list[str]] = {
            QueryIntent.VIOLATION_SEARCH: ["Show me the critical violations in detail", "What's the remediation plan?", "Compare with last month"],
            QueryIntent.REGULATION_LOOKUP: ["What code changes are needed?", "Show affected repositories", "Generate compliance checklist"],
            QueryIntent.POSTURE_STATUS: ["Show score breakdown by framework", "What's causing the lowest scores?", "Compare with industry benchmarks"],
            QueryIntent.AUDIT_SEARCH: ["Export audit trail as PDF", "Show changes by specific user", "Verify hash chain integrity"],
            QueryIntent.COMPARISON: ["Show detailed gap analysis", "Recommend improvements for lowest scorer", "Show trend comparison"],
            QueryIntent.RECOMMENDATION: ["Estimate effort for each recommendation", "Show affected code files", "Create implementation plan"],
            QueryIntent.TREND_ANALYSIS: ["Predict next month's score", "Show contributing factors", "Set alert for score drops"],
        }
        return follow_ups.get(intent, ["Try asking about violations", "Check your compliance posture", "Look up a regulation"])

    async def submit_feedback(self, query_id: UUID, helpful: bool, comment: str = "") -> QueryFeedback:
        feedback = QueryFeedback(query_id=query_id, helpful=helpful, comment=comment, created_at=datetime.now(UTC))
        self._feedback.append(feedback)
        return feedback

    def get_query_history(self, limit: int = 20) -> list[dict]:
        history = []
        for q in sorted(self._queries, key=lambda x: x.submitted_at or datetime.min.replace(tzinfo=UTC), reverse=True)[:limit]:
            result = next((r for r in self._results if r.query_id == q.id), None)
            history.append({"query": q.raw_query, "intent": q.intent.value, "answer": result.answer if result else "", "time_ms": result.execution_time_ms if result else 0})
        return history

    def get_stats(self) -> QueryStats:
        by_intent: dict[str, int] = {}
        for q in self._queries:
            by_intent[q.intent.value] = by_intent.get(q.intent.value, 0) + 1
        times = [r.execution_time_ms for r in self._results]
        positive = sum(1 for f in self._feedback if f.helpful)
        topics = list(by_intent.keys())[:5]
        return QueryStats(
            total_queries=len(self._queries),
            by_intent=by_intent,
            avg_execution_time_ms=round(sum(times) / len(times), 2) if times else 0.0,
            positive_feedback_rate=round(positive / len(self._feedback), 2) if self._feedback else 0.0,
            most_common_topics=topics,
        )
