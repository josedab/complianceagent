"""Draft legislation and regulatory signal monitoring sources."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog

from app.services.prediction.models import RegulatorySignal, SignalType


logger = structlog.get_logger()


@dataclass
class RegulatorySource:
    """A source of regulatory signals."""

    name: str
    url: str
    jurisdiction: str
    signal_types: list[SignalType]
    update_frequency_hours: int = 24
    enabled: bool = True


# Pre-configured regulatory sources for monitoring
REGULATORY_SOURCES = [
    # EU Sources
    RegulatorySource(
        name="EUR-Lex Preparatory Acts",
        url="https://eur-lex.europa.eu/collection/eu-law/pre-acts.html",
        jurisdiction="EU",
        signal_types=[SignalType.DRAFT_LEGISLATION, SignalType.REGULATORY_PROPOSAL],
        update_frequency_hours=12,
    ),
    RegulatorySource(
        name="European Commission Consultations",
        url="https://ec.europa.eu/info/law/better-regulation/have-your-say_en",
        jurisdiction="EU",
        signal_types=[SignalType.PUBLIC_CONSULTATION],
        update_frequency_hours=24,
    ),
    RegulatorySource(
        name="EDPB News",
        url="https://edpb.europa.eu/news_en",
        jurisdiction="EU",
        signal_types=[SignalType.REGULATORY_GUIDANCE, SignalType.ENFORCEMENT_ACTION],
        update_frequency_hours=24,
    ),
    RegulatorySource(
        name="European Parliament Legislative Observatory",
        url="https://oeil.secure.europarl.europa.eu/oeil/home/home.do",
        jurisdiction="EU",
        signal_types=[SignalType.DRAFT_LEGISLATION],
        update_frequency_hours=12,
    ),
    # US Sources
    RegulatorySource(
        name="Congress.gov",
        url="https://www.congress.gov/",
        jurisdiction="US-Federal",
        signal_types=[SignalType.DRAFT_LEGISLATION],
        update_frequency_hours=24,
    ),
    RegulatorySource(
        name="Federal Register",
        url="https://www.federalregister.gov/",
        jurisdiction="US-Federal",
        signal_types=[SignalType.REGULATORY_PROPOSAL, SignalType.PUBLIC_CONSULTATION],
        update_frequency_hours=24,
    ),
    RegulatorySource(
        name="FTC News",
        url="https://www.ftc.gov/news-events/news",
        jurisdiction="US-Federal",
        signal_types=[SignalType.ENFORCEMENT_ACTION, SignalType.REGULATORY_GUIDANCE],
        update_frequency_hours=24,
    ),
    RegulatorySource(
        name="SEC Proposed Rules",
        url="https://www.sec.gov/rules/proposed.shtml",
        jurisdiction="US-Federal",
        signal_types=[SignalType.REGULATORY_PROPOSAL],
        update_frequency_hours=24,
    ),
    RegulatorySource(
        name="California Legislature",
        url="https://leginfo.legislature.ca.gov/",
        jurisdiction="US-CA",
        signal_types=[SignalType.DRAFT_LEGISLATION],
        update_frequency_hours=24,
    ),
    # UK Sources
    RegulatorySource(
        name="UK Parliament Bills",
        url="https://bills.parliament.uk/",
        jurisdiction="UK",
        signal_types=[SignalType.DRAFT_LEGISLATION],
        update_frequency_hours=24,
    ),
    RegulatorySource(
        name="ICO News",
        url="https://ico.org.uk/about-the-ico/news-and-events/",
        jurisdiction="UK",
        signal_types=[SignalType.ENFORCEMENT_ACTION, SignalType.REGULATORY_GUIDANCE],
        update_frequency_hours=24,
    ),
    # International Standards
    RegulatorySource(
        name="ISO Standards Development",
        url="https://www.iso.org/developing-standards.html",
        jurisdiction="Global",
        signal_types=[SignalType.INDUSTRY_STANDARD],
        update_frequency_hours=168,  # Weekly
    ),
    RegulatorySource(
        name="NIST Publications",
        url="https://www.nist.gov/publications",
        jurisdiction="Global",
        signal_types=[SignalType.INDUSTRY_STANDARD, SignalType.REGULATORY_GUIDANCE],
        update_frequency_hours=168,
    ),
    # Asia-Pacific Sources
    RegulatorySource(
        name="Singapore PDPC News",
        url="https://www.pdpc.gov.sg/news-and-events",
        jurisdiction="Singapore",
        signal_types=[SignalType.REGULATORY_GUIDANCE, SignalType.ENFORCEMENT_ACTION],
        update_frequency_hours=24,
    ),
    RegulatorySource(
        name="Australia OAIC",
        url="https://www.oaic.gov.au/news-and-resources",
        jurisdiction="Australia",
        signal_types=[SignalType.REGULATORY_GUIDANCE, SignalType.ENFORCEMENT_ACTION],
        update_frequency_hours=24,
    ),
]


class DraftLegislationMonitor:
    """Monitors regulatory sources for draft legislation and signals."""

    def __init__(self, sources: list[RegulatorySource] | None = None):
        self.sources = sources or REGULATORY_SOURCES
        self._http_client: httpx.AsyncClient | None = None
        self._last_check: dict[str, datetime] = {}
        self._cached_signals: dict[str, list[RegulatorySignal]] = {}

    async def __aenter__(self):
        self._http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._http_client:
            await self._http_client.aclose()

    async def fetch_signals(
        self,
        jurisdictions: list[str] | None = None,
        signal_types: list[SignalType] | None = None,
        force_refresh: bool = False,
    ) -> list[RegulatorySignal]:
        """Fetch regulatory signals from configured sources.

        Args:
            jurisdictions: Filter by jurisdictions (e.g., ["EU", "US-Federal"])
            signal_types: Filter by signal types
            force_refresh: Force refresh even if recently checked

        Returns:
            List of regulatory signals
        """
        signals = []
        sources_to_check = self.sources

        if jurisdictions:
            sources_to_check = [s for s in sources_to_check if s.jurisdiction in jurisdictions]

        if signal_types:
            sources_to_check = [
                s for s in sources_to_check
                if any(st in s.signal_types for st in signal_types)
            ]

        for source in sources_to_check:
            if not source.enabled:
                continue

            # Check if we need to refresh
            last_check = self._last_check.get(source.name)
            if not force_refresh and last_check:
                hours_since = (datetime.now(UTC) - last_check).total_seconds() / 3600
                if hours_since < source.update_frequency_hours:
                    # Use cached signals
                    cached = self._cached_signals.get(source.name, [])
                    signals.extend(cached)
                    continue

            try:
                source_signals = await self._fetch_from_source(source)
                self._cached_signals[source.name] = source_signals
                self._last_check[source.name] = datetime.now(UTC)
                signals.extend(source_signals)
            except Exception as e:
                logger.warning(f"Failed to fetch from {source.name}: {e}")

        return signals

    async def _fetch_from_source(self, source: RegulatorySource) -> list[RegulatorySignal]:
        """Fetch signals from a specific source.

        Note: In a production system, this would implement actual web scraping
        or API calls. Here we return mock data for demonstration.
        """
        # Mock implementation - in production would scrape/call actual sources
        logger.info(f"Fetching signals from {source.name}")

        # Return simulated signals based on source type
        signals = []

        if SignalType.DRAFT_LEGISLATION in source.signal_types:
            signals.append(RegulatorySignal(
                signal_type=SignalType.DRAFT_LEGISLATION,
                title=f"[{source.jurisdiction}] Draft Data Protection Amendment",
                description="Proposed amendments to strengthen data subject rights",
                source_url=source.url,
                source_name=source.name,
                jurisdiction=source.jurisdiction,
                relevance_score=0.85,
                affected_regulations=["GDPR", "Data Protection"],
                affected_industries=["Technology", "Finance", "Healthcare"],
                affected_data_types=["Personal Data", "Biometric Data"],
                key_requirements=[
                    "Enhanced consent requirements",
                    "Stricter data retention limits",
                    "Expanded data subject rights",
                ],
                timeline_indicators=["Q2 2026 expected vote", "2027 effective date"],
            ))

        if SignalType.PUBLIC_CONSULTATION in source.signal_types:
            signals.append(RegulatorySignal(
                signal_type=SignalType.PUBLIC_CONSULTATION,
                title=f"[{source.jurisdiction}] Public Consultation on AI Regulation",
                description="Stakeholder input requested on AI governance framework",
                source_url=source.url,
                source_name=source.name,
                jurisdiction=source.jurisdiction,
                relevance_score=0.75,
                affected_regulations=["AI Act", "AI Governance"],
                affected_industries=["Technology", "AI/ML"],
                key_requirements=[
                    "AI risk assessment requirements",
                    "Algorithmic transparency",
                    "Human oversight mechanisms",
                ],
                timeline_indicators=["Consultation closes March 2026"],
            ))

        return signals

    async def analyze_signal_implications(
        self,
        signal: RegulatorySignal,
    ) -> dict[str, Any]:
        """Analyze a signal for regulatory implications using AI.

        This would use the Copilot SDK to analyze the signal content
        and extract regulatory implications.
        """
        from app.agents.copilot import CopilotClient, CopilotMessage

        analysis = {
            "signal_id": str(signal.id),
            "signal_type": signal.signal_type.value,
            "jurisdiction": signal.jurisdiction,
            "implications": [],
            "affected_code_patterns": [],
            "preparation_actions": [],
            "confidence": 0.0,
        }

        try:
            async with CopilotClient() as client:
                system_prompt = """You are a regulatory analyst specializing in technology compliance.
Analyze this regulatory signal and provide:
1. Key implications for software systems
2. Code patterns that would be affected
3. Recommended preparation actions
4. Confidence in the regulatory change occurring

Return JSON with: implications (array), affected_code_patterns (array), preparation_actions (array), confidence (0-1)"""

                user_prompt = f"""Analyze this regulatory signal:

Title: {signal.title}
Description: {signal.description}
Jurisdiction: {signal.jurisdiction}
Type: {signal.signal_type.value}
Key Requirements: {', '.join(signal.key_requirements)}
Timeline: {', '.join(signal.timeline_indicators)}

Return JSON only."""

                response = await client.chat(
                    messages=[CopilotMessage(role="user", content=user_prompt)],
                    system_message=system_prompt,
                    temperature=0.3,
                    max_tokens=2048,
                )

                import json
                content = response.content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                content = content.rstrip("`")
                result = json.loads(content)

                analysis.update(result)

        except Exception as e:
            logger.warning(f"Failed to analyze signal: {e}")
            # Return basic analysis based on signal data
            analysis["implications"] = signal.key_requirements
            analysis["confidence"] = signal.relevance_score

        return analysis

    def get_source_status(self) -> list[dict[str, Any]]:
        """Get status of all configured sources."""
        status = []
        for source in self.sources:
            last_check = self._last_check.get(source.name)
            cached_count = len(self._cached_signals.get(source.name, []))

            status.append({
                "name": source.name,
                "jurisdiction": source.jurisdiction,
                "enabled": source.enabled,
                "signal_types": [st.value for st in source.signal_types],
                "last_check": last_check.isoformat() if last_check else None,
                "cached_signals": cached_count,
                "update_frequency_hours": source.update_frequency_hours,
            })

        return status
