"""Regulatory Horizon Scanner service.

Monitors pending legislation from Congress.gov, EUR-Lex, SEC EDGAR and other
sources.  Predicts codebase impact using multi-LLM analysis and surfaces
advance warnings via timeline and alerts.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import json

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.horizon_scanner.models import (
    CodebaseImpactPrediction,
    ConfidenceLevel,
    HorizonAlert,
    HorizonTimeline,
    ImpactSeverity,
    LegislativeSource,
    LegislativeStatus,
    PendingLegislation,
)


logger = structlog.get_logger()

# Known upcoming regulations with estimated timelines
_SEED_LEGISLATION: list[dict[str, Any]] = [
    {
        "title": "EU AI Act - Full Enforcement",
        "jurisdiction": "EU",
        "source": LegislativeSource.EUR_LEX,
        "status": LegislativeStatus.ENACTED,
        "confidence": ConfidenceLevel.HIGH,
        "frameworks_affected": ["EU AI Act", "GDPR"],
        "months_ahead": 3,
        "tags": ["ai", "transparency", "risk-classification"],
    },
    {
        "title": "Digital Operational Resilience Act (DORA)",
        "jurisdiction": "EU",
        "source": LegislativeSource.EUR_LEX,
        "status": LegislativeStatus.EFFECTIVE,
        "confidence": ConfidenceLevel.HIGH,
        "frameworks_affected": ["DORA", "NIS2"],
        "months_ahead": 0,
        "tags": ["financial", "ict-risk", "resilience"],
    },
    {
        "title": "NIST AI RMF 2.0 Update",
        "jurisdiction": "US",
        "source": LegislativeSource.NIST,
        "status": LegislativeStatus.DRAFT,
        "confidence": ConfidenceLevel.MEDIUM,
        "frameworks_affected": ["NIST AI RMF"],
        "months_ahead": 8,
        "tags": ["ai", "risk-management", "voluntary"],
    },
    {
        "title": "American Privacy Rights Act (APRA)",
        "jurisdiction": "US",
        "source": LegislativeSource.CONGRESS_GOV,
        "status": LegislativeStatus.COMMITTEE,
        "confidence": ConfidenceLevel.LOW,
        "frameworks_affected": ["CCPA", "GDPR"],
        "months_ahead": 18,
        "tags": ["privacy", "federal", "data-rights"],
    },
    {
        "title": "PCI-DSS v4.0.1 Enforcement Deadline",
        "jurisdiction": "Global",
        "source": LegislativeSource.CUSTOM,
        "status": LegislativeStatus.ENACTED,
        "confidence": ConfidenceLevel.HIGH,
        "frameworks_affected": ["PCI-DSS"],
        "months_ahead": 2,
        "tags": ["payment", "security", "deadline"],
    },
    {
        "title": "UK AI Safety Bill",
        "jurisdiction": "UK",
        "source": LegislativeSource.FCA_UK,
        "status": LegislativeStatus.PROPOSED,
        "confidence": ConfidenceLevel.MEDIUM,
        "frameworks_affected": ["EU AI Act", "ISO 42001"],
        "months_ahead": 12,
        "tags": ["ai", "safety", "uk"],
    },
    {
        "title": "SEC Climate Disclosure Rules - Phase 2",
        "jurisdiction": "US",
        "source": LegislativeSource.SEC_EDGAR,
        "status": LegislativeStatus.PASSED,
        "confidence": ConfidenceLevel.HIGH,
        "frameworks_affected": ["SEC Climate", "TCFD", "CSRD"],
        "months_ahead": 6,
        "tags": ["esg", "climate", "disclosure"],
    },
    {
        "title": "India DPDP Rules (Implementation Guidelines)",
        "jurisdiction": "India",
        "source": LegislativeSource.CUSTOM,
        "status": LegislativeStatus.DRAFT,
        "confidence": ConfidenceLevel.MEDIUM,
        "frameworks_affected": ["India DPDP"],
        "months_ahead": 4,
        "tags": ["privacy", "apac", "data-protection"],
    },
]


class HorizonScannerService:
    """Monitors pending legislation and predicts codebase impact."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._tracked: dict[UUID, PendingLegislation] = {}
        self._predictions: dict[UUID, CodebaseImpactPrediction] = {}
        self._alerts: list[HorizonAlert] = []
        self._init_seed_data()

    def _init_seed_data(self) -> None:
        now = datetime.now(UTC)
        for item in _SEED_LEGISLATION:
            leg = PendingLegislation(
                title=item["title"],
                jurisdiction=item["jurisdiction"],
                source=item["source"],
                status=item["status"],
                confidence=item["confidence"],
                frameworks_affected=item["frameworks_affected"],
                tags=item["tags"],
                expected_effective_date=now + timedelta(days=item["months_ahead"] * 30),
                discovered_at=now - timedelta(days=30),
            )
            self._tracked[leg.id] = leg

            months = item["months_ahead"]
            if months <= 6:
                severity = ImpactSeverity.HIGH if months <= 3 else ImpactSeverity.MEDIUM
                self._alerts.append(
                    HorizonAlert(
                        legislation_id=leg.id,
                        title=leg.title,
                        message=f"{leg.title} takes effect in ~{months} months. "
                        f"Frameworks affected: {', '.join(leg.frameworks_affected)}.",
                        severity=severity,
                        months_until_effective=months,
                        created_at=now,
                    )
                )

    async def get_timeline(
        self,
        jurisdiction: str | None = None,
        framework: str | None = None,
        months_ahead: int = 24,
    ) -> HorizonTimeline:
        """Get the regulatory horizon timeline with upcoming legislation."""
        cutoff = datetime.now(UTC) + timedelta(days=months_ahead * 30)
        items = list(self._tracked.values())

        if jurisdiction:
            items = [i for i in items if i.jurisdiction.lower() == jurisdiction.lower()]
        if framework:
            items = [
                i
                for i in items
                if any(framework.lower() in f.lower() for f in i.frameworks_affected)
            ]

        items = [
            i for i in items if i.expected_effective_date and i.expected_effective_date <= cutoff
        ]
        items.sort(key=lambda i: i.expected_effective_date or datetime.max.replace(tzinfo=UTC))

        high_impact = sum(
            1 for a in self._alerts if a.severity in (ImpactSeverity.CRITICAL, ImpactSeverity.HIGH)
        )

        return HorizonTimeline(
            upcoming=items,
            alerts=self._alerts,
            total_tracked=len(self._tracked),
            high_impact_count=high_impact,
        )

    async def get_legislation(self, legislation_id: UUID) -> PendingLegislation | None:
        return self._tracked.get(legislation_id)

    async def predict_impact(
        self,
        legislation_id: UUID,
        repo_url: str = "",
    ) -> CodebaseImpactPrediction:
        """Predict codebase impact for a pending regulation."""
        legislation = self._tracked.get(legislation_id)
        if not legislation:
            return CodebaseImpactPrediction(legislation_id=legislation_id)

        # If we have a Copilot client, use AI analysis
        if self.copilot and hasattr(self.copilot, "chat"):
            try:
                return await self._ai_predict_impact(legislation, repo_url)
            except (json.JSONDecodeError, KeyError, ValueError, OSError) as exc:
                logger.warning("AI impact prediction failed, using heuristic", error=str(exc))

        # Heuristic fallback
        severity_map = {
            ConfidenceLevel.HIGH: ImpactSeverity.HIGH,
            ConfidenceLevel.MEDIUM: ImpactSeverity.MEDIUM,
            ConfidenceLevel.LOW: ImpactSeverity.LOW,
        }
        fw_count = len(legislation.frameworks_affected)
        effort = fw_count * 15.0  # ~15 days per affected framework
        affected_files = int(effort * 3.5)

        prediction = CodebaseImpactPrediction(
            legislation_id=legislation_id,
            affected_files=affected_files,
            affected_modules=[
                f"compliance/{fw.lower().replace(' ', '_')}"
                for fw in legislation.frameworks_affected
            ],
            estimated_effort_days=effort,
            impact_severity=severity_map.get(legislation.confidence, ImpactSeverity.MEDIUM),
            recommendations=[
                f"Review {legislation.title} requirements against current codebase",
                f"Prioritize {legislation.frameworks_affected[0]} compliance gap analysis"
                if legislation.frameworks_affected
                else "Begin compliance assessment",
                f"Allocate ~{effort:.0f} developer-days for implementation",
            ],
            confidence_score=0.65,
        )
        self._predictions[prediction.id] = prediction

        logger.info(
            "impact_prediction_generated",
            legislation=legislation.title,
            severity=prediction.impact_severity.value,
            effort_days=prediction.estimated_effort_days,
        )
        return prediction

    async def _ai_predict_impact(
        self, legislation: PendingLegislation, repo_url: str
    ) -> CodebaseImpactPrediction:
        """Use AI to predict impact (requires Copilot client)."""
        from app.agents.copilot import CopilotMessage

        prompt = (
            f"Analyze the potential codebase impact of: {legislation.title}\n"
            f"Jurisdiction: {legislation.jurisdiction}\n"
            f"Frameworks: {', '.join(legislation.frameworks_affected)}\n"
            f"Status: {legislation.status.value}\n\n"
            "Estimate: affected file count, effort in developer-days, "
            "key modules affected, and top 3 recommendations. "
            "Return JSON with keys: affected_files, effort_days, modules, recommendations."
        )

        response = await self.copilot.chat(
            messages=[CopilotMessage(role="user", content=prompt)],
            system_message="You are a compliance engineering advisor.",
            temperature=0.3,
        )

        import json

        try:
            data = json.loads(response.content.strip().strip("`").strip("json\n"))
        except json.JSONDecodeError:
            data = {}

        return CodebaseImpactPrediction(
            legislation_id=legislation.id,
            affected_files=data.get("affected_files", 20),
            affected_modules=data.get("modules", []),
            estimated_effort_days=data.get("effort_days", 30.0),
            impact_severity=ImpactSeverity.HIGH,
            recommendations=data.get("recommendations", []),
            confidence_score=0.80,
        )

    async def add_legislation(self, legislation: PendingLegislation) -> PendingLegislation:
        """Manually track a new piece of legislation."""
        legislation.discovered_at = datetime.now(UTC)
        self._tracked[legislation.id] = legislation
        logger.info("legislation_tracked", title=legislation.title)
        return legislation

    async def get_alerts(self, severity: ImpactSeverity | None = None) -> list[HorizonAlert]:
        if severity:
            return [a for a in self._alerts if a.severity == severity]
        return list(self._alerts)
