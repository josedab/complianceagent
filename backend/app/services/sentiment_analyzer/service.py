"""Regulatory Change Sentiment Analyzer Service."""

import random
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.sentiment_analyzer.models import (
    EnforcementAction,
    EnforcementTrend,
    PrioritizationRecommendation,
    RegulatorySentiment,
    RiskHeatmapCell,
    SentimentReport,
    SentimentScore,
)


logger = structlog.get_logger()

_JURISDICTIONS = ["US", "EU", "UK", "Singapore", "Australia", "Canada", "Brazil"]
_REGULATIONS = ["GDPR", "HIPAA", "SOX", "PCI-DSS", "CCPA", "DORA", "NIS2"]

_MOCK_ENFORCEMENT_ACTIONS = [
    {
        "regulation": "GDPR",
        "jurisdiction": "EU",
        "entity": "TechCorp Ltd",
        "amount": 746000000,
        "violation": "Insufficient consent mechanisms",
        "date": "2024-07-15",
        "summary": "Major fine for tracking users without proper consent",
    },
    {
        "regulation": "GDPR",
        "jurisdiction": "EU",
        "entity": "DataFlow Inc",
        "amount": 405000000,
        "violation": "Unlawful data processing",
        "date": "2024-05-22",
        "summary": "Behavioral advertising without legal basis",
    },
    {
        "regulation": "HIPAA",
        "jurisdiction": "US",
        "entity": "HealthNet Systems",
        "amount": 5100000,
        "violation": "PHI exposure",
        "date": "2024-08-10",
        "summary": "Unencrypted patient records accessible online",
    },
    {
        "regulation": "CCPA",
        "jurisdiction": "US",
        "entity": "RetailData Corp",
        "amount": 1200000,
        "violation": "Failure to honor opt-out",
        "date": "2024-06-30",
        "summary": "Continued selling consumer data after opt-out requests",
    },
    {
        "regulation": "PCI-DSS",
        "jurisdiction": "US",
        "entity": "PayQuick LLC",
        "amount": 3500000,
        "violation": "Cardholder data exposure",
        "date": "2024-04-18",
        "summary": "Stored CVV data in plaintext",
    },
    {
        "regulation": "SOX",
        "jurisdiction": "US",
        "entity": "FinanceGroup Inc",
        "amount": 8000000,
        "violation": "Internal control failures",
        "date": "2024-03-12",
        "summary": "Material weakness in financial reporting controls",
    },
    {
        "regulation": "DORA",
        "jurisdiction": "EU",
        "entity": "EuroBank AG",
        "amount": 2500000,
        "violation": "ICT risk management gaps",
        "date": "2024-09-01",
        "summary": "Inadequate digital operational resilience testing",
    },
    {
        "regulation": "NIS2",
        "jurisdiction": "EU",
        "entity": "InfraNet GmbH",
        "amount": 1800000,
        "violation": "Incident reporting delay",
        "date": "2024-08-25",
        "summary": "Failed to report critical incident within 24 hours",
    },
]


class SentimentAnalyzerService:
    """Analyze regulatory enforcement sentiment and trends."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._sentiments: dict[str, RegulatorySentiment] = {}

    async def analyze_sentiment(
        self,
        regulation: str,
        jurisdiction: str | None = None,
    ) -> RegulatorySentiment:
        """Analyze enforcement sentiment for a regulation."""
        jur = jurisdiction or random.choice(_JURISDICTIONS)
        risk = random.uniform(0.2, 0.95)

        if risk > 0.7:
            trend = EnforcementTrend.HEATING_UP
            sentiment = SentimentScore.VERY_NEGATIVE
        elif risk > 0.5:
            trend = EnforcementTrend.STABLE
            sentiment = SentimentScore.NEGATIVE
        elif risk > 0.3:
            trend = EnforcementTrend.COOLING_DOWN
            sentiment = SentimentScore.NEUTRAL
        else:
            trend = EnforcementTrend.DORMANT
            sentiment = SentimentScore.POSITIVE

        topics_pool = [
            "data breach notification",
            "consent management",
            "cross-border transfers",
            "AI governance",
            "children's privacy",
            "biometric data",
            "encryption standards",
            "third-party risk",
            "incident response",
            "audit requirements",
        ]

        result = RegulatorySentiment(
            regulation=regulation,
            jurisdiction=jur,
            trend=trend,
            sentiment=sentiment,
            enforcement_probability=round(risk, 2),
            avg_fine_amount=round(random.uniform(100000, 50000000), 2),
            enforcement_count_ytd=random.randint(1, 25),
            key_topics=random.sample(topics_pool, min(4, len(topics_pool))),
            analyzed_at=datetime.now(UTC),
        )
        key = f"{regulation}:{jur}"
        self._sentiments[key] = result
        logger.info(
            "Sentiment analyzed", regulation=regulation, jurisdiction=jur, trend=trend.value
        )
        return result

    async def list_sentiments(self, jurisdiction: str | None = None) -> list[RegulatorySentiment]:
        """List all analyzed sentiments."""
        sentiments = list(self._sentiments.values())
        if jurisdiction:
            sentiments = [s for s in sentiments if s.jurisdiction == jurisdiction]
        return sentiments

    async def get_enforcement_actions(
        self,
        regulation: str | None = None,
        limit: int = 20,
    ) -> list[EnforcementAction]:
        """Get enforcement actions, optionally filtered by regulation."""
        actions = []
        for ea in _MOCK_ENFORCEMENT_ACTIONS:
            if regulation and ea["regulation"] != regulation:
                continue
            actions.append(
                EnforcementAction(
                    regulation=ea["regulation"],
                    jurisdiction=ea["jurisdiction"],
                    entity_fined=ea["entity"],
                    fine_amount=ea["amount"],
                    violation_type=ea["violation"],
                    date=ea["date"],
                    summary=ea["summary"],
                )
            )
        return actions[:limit]

    async def get_risk_heatmap(self) -> list[RiskHeatmapCell]:
        """Generate risk heatmap across regulations and jurisdictions."""
        cells: list[RiskHeatmapCell] = []
        for reg in _REGULATIONS:
            for jur in _JURISDICTIONS[:4]:
                score = round(random.uniform(0.1, 1.0), 2)
                if score > 0.7:
                    color = "red"
                    trend = EnforcementTrend.HEATING_UP
                elif score > 0.4:
                    color = "yellow"
                    trend = EnforcementTrend.STABLE
                else:
                    color = "green"
                    trend = EnforcementTrend.COOLING_DOWN

                cells.append(
                    RiskHeatmapCell(
                        regulation=reg,
                        jurisdiction=jur,
                        risk_score=score,
                        trend=trend,
                        color=color,
                    )
                )
        return cells

    async def get_prioritization(self) -> list[PrioritizationRecommendation]:
        """Get prioritized compliance recommendations."""
        recommendations: list[PrioritizationRecommendation] = []
        effort_options = ["low", "medium", "high", "very_high"]

        for rank, reg in enumerate(sorted(_REGULATIONS, key=lambda _: random.random()), 1):
            score = round(random.uniform(0.3, 0.95), 2)
            recommendations.append(
                PrioritizationRecommendation(
                    regulation=reg,
                    priority_rank=rank,
                    risk_score=score,
                    effort_estimate=random.choice(effort_options),
                    rationale=f"Enforcement activity for {reg} is {'increasing' if score > 0.6 else 'moderate'} — prioritize compliance gaps",
                    enforcement_likelihood=round(score * random.uniform(0.8, 1.0), 2),
                )
            )
        return sorted(recommendations, key=lambda r: r.risk_score, reverse=True)

    async def generate_report(self) -> SentimentReport:
        """Generate a comprehensive sentiment report."""
        heatmap = await self.get_risk_heatmap()
        priorities = await self.get_prioritization()
        high_risk = len([c for c in heatmap if c.risk_score > 0.7])

        report = SentimentReport(
            total_regulations_analyzed=len(_REGULATIONS),
            high_risk_count=high_risk,
            heatmap=heatmap,
            top_priorities=priorities[:5],
            generated_at=datetime.now(UTC),
        )
        logger.info(
            "Sentiment report generated", regulations=len(_REGULATIONS), high_risk=high_risk
        )
        return report
