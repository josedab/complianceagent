"""Intelligence Feed - Real-time streaming of regulatory updates."""

import asyncio
import hashlib
import time
from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import structlog

from app.services.intelligence.models import (
    CustomerProfile,
    IntelligenceAlert,
    IntelligenceDigest,
    RegulatorySource,
    RegulatoryUpdate,
    UpdateSeverity,
    UpdateType,
)


logger = structlog.get_logger()


# Default regulatory sources to monitor
DEFAULT_SOURCES = [
    # US Federal
    RegulatorySource(name="SEC EDGAR", url="https://www.sec.gov/cgi-bin/browse-edgar", jurisdiction="US", framework="Securities", category="financial"),
    RegulatorySource(name="FTC Press", url="https://www.ftc.gov/news-events/news/press-releases", jurisdiction="US", framework="Consumer Protection", category="privacy"),
    RegulatorySource(name="HHS OCR", url="https://www.hhs.gov/hipaa/index.html", jurisdiction="US", framework="HIPAA", category="healthcare"),
    RegulatorySource(name="NIST Cybersecurity", url="https://www.nist.gov/cyberframework", jurisdiction="US", framework="NIST", category="security"),
    
    # US State
    RegulatorySource(name="California AG", url="https://oag.ca.gov/privacy", jurisdiction="US-CA", framework="CCPA/CPRA", category="privacy"),
    RegulatorySource(name="Colorado AG", url="https://coag.gov/resources/colorado-privacy-act/", jurisdiction="US-CO", framework="CPA", category="privacy"),
    
    # EU
    RegulatorySource(name="EUR-Lex", url="https://eur-lex.europa.eu/", jurisdiction="EU", framework="GDPR", category="privacy"),
    RegulatorySource(name="EDPB", url="https://edpb.europa.eu/edpb_en", jurisdiction="EU", framework="GDPR", category="privacy"),
    RegulatorySource(name="EU AI Act Portal", url="https://artificialintelligenceact.eu/", jurisdiction="EU", framework="EU AI Act", category="ai"),
    RegulatorySource(name="ENISA", url="https://www.enisa.europa.eu/", jurisdiction="EU", framework="NIS2", category="security"),
    
    # UK
    RegulatorySource(name="ICO UK", url="https://ico.org.uk/for-organisations/", jurisdiction="UK", framework="UK GDPR", category="privacy"),
    RegulatorySource(name="FCA", url="https://www.fca.org.uk/news", jurisdiction="UK", framework="Financial", category="financial"),
    
    # APAC
    RegulatorySource(name="PDPC Singapore", url="https://www.pdpc.gov.sg/", jurisdiction="SG", framework="PDPA", category="privacy"),
    RegulatorySource(name="PIPC Korea", url="https://www.pipc.go.kr/", jurisdiction="KR", framework="PIPA", category="privacy"),
    RegulatorySource(name="MeitY India", url="https://www.meity.gov.in/", jurisdiction="IN", framework="DPDP", category="privacy"),
    
    # Industry
    RegulatorySource(name="PCI SSC", url="https://www.pcisecuritystandards.org/", jurisdiction="Global", framework="PCI-DSS", category="payment"),
    RegulatorySource(name="ISO Standards", url="https://www.iso.org/standards.html", jurisdiction="Global", framework="ISO", category="standards"),
]


class IntelligenceFeed:
    """Real-time regulatory intelligence feed with streaming updates."""

    def __init__(
        self,
        sources: list[RegulatorySource] | None = None,
        check_interval_seconds: int = 3600,  # 1 hour default
    ):
        self.sources = sources or DEFAULT_SOURCES
        self.check_interval = check_interval_seconds
        self._running = False
        self._update_cache: dict[str, RegulatoryUpdate] = {}
        self._subscribers: dict[UUID, asyncio.Queue] = {}
        self._last_check: dict[str, datetime] = {}

    async def start(self) -> None:
        """Start the intelligence feed monitoring."""
        self._running = True
        logger.info("Starting regulatory intelligence feed", sources=len(self.sources))
        
        while self._running:
            try:
                updates = await self._check_all_sources()
                for update in updates:
                    await self._broadcast_update(update)
                    
            except Exception as e:
                logger.error(f"Feed check error: {e}")
            
            await asyncio.sleep(self.check_interval)

    async def stop(self) -> None:
        """Stop the intelligence feed."""
        self._running = False
        logger.info("Stopping regulatory intelligence feed")

    def subscribe(self, subscriber_id: UUID) -> asyncio.Queue:
        """Subscribe to receive real-time updates.
        
        Returns a queue that will receive RegulatoryUpdate objects.
        """
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[subscriber_id] = queue
        logger.info(f"Subscriber added: {subscriber_id}")
        return queue

    def unsubscribe(self, subscriber_id: UUID) -> None:
        """Unsubscribe from updates."""
        self._subscribers.pop(subscriber_id, None)
        logger.info(f"Subscriber removed: {subscriber_id}")

    async def get_recent_updates(
        self,
        hours: int = 24,
        jurisdictions: list[str] | None = None,
        frameworks: list[str] | None = None,
        min_severity: UpdateSeverity | None = None,
    ) -> list[RegulatoryUpdate]:
        """Get recent updates with optional filters."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        updates = [
            u for u in self._update_cache.values()
            if u.detected_at >= cutoff
        ]
        
        if jurisdictions:
            updates = [u for u in updates if u.jurisdiction in jurisdictions]
        
        if frameworks:
            updates = [u for u in updates if u.framework in frameworks]
        
        if min_severity:
            severity_order = [UpdateSeverity.CRITICAL, UpdateSeverity.HIGH, UpdateSeverity.MEDIUM, UpdateSeverity.LOW, UpdateSeverity.INFO]
            min_idx = severity_order.index(min_severity)
            updates = [u for u in updates if severity_order.index(u.severity) <= min_idx]
        
        return sorted(updates, key=lambda u: u.detected_at, reverse=True)

    async def get_updates_stream(
        self,
        subscriber_id: UUID | None = None,
    ) -> AsyncIterator[RegulatoryUpdate]:
        """Async generator for streaming updates.
        
        Usage:
            async for update in feed.get_updates_stream():
                process(update)
        """
        sub_id = subscriber_id or uuid4()
        queue = self.subscribe(sub_id)
        
        try:
            while True:
                update = await queue.get()
                yield update
        finally:
            self.unsubscribe(sub_id)

    async def simulate_update(self, update: RegulatoryUpdate) -> None:
        """Simulate a regulatory update for testing."""
        update.detected_at = datetime.utcnow()
        update.content_hash = self._hash_content(update.content)
        self._update_cache[str(update.id)] = update
        await self._broadcast_update(update)

    async def _check_all_sources(self) -> list[RegulatoryUpdate]:
        """Check all sources for updates."""
        updates = []
        
        for source in self.sources:
            if not source.is_active:
                continue
            
            # Check if source needs to be checked
            last = self._last_check.get(source.name)
            if last and (datetime.utcnow() - last).total_seconds() < source.check_frequency_hours * 3600:
                continue
            
            try:
                source_updates = await self._check_source(source)
                updates.extend(source_updates)
                self._last_check[source.name] = datetime.utcnow()
            except Exception as e:
                logger.warning(f"Failed to check source {source.name}: {e}")
        
        return updates

    async def _check_source(self, source: RegulatorySource) -> list[RegulatoryUpdate]:
        """Check a single source for updates.
        
        In production, this would use web crawling (Playwright/HTTPX).
        For now, returns empty list (actual crawling implemented elsewhere).
        """
        # This would integrate with the monitoring service
        # For the API, we expose endpoints to receive updates
        return []

    async def _broadcast_update(self, update: RegulatoryUpdate) -> None:
        """Broadcast an update to all subscribers."""
        for subscriber_id, queue in list(self._subscribers.items()):
            try:
                await queue.put(update)
            except Exception as e:
                logger.warning(f"Failed to broadcast to {subscriber_id}: {e}")
                self.unsubscribe(subscriber_id)

    def _hash_content(self, content: str) -> str:
        """Generate hash of content for change detection."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def ingest_update(self, update_data: dict[str, Any]) -> RegulatoryUpdate:
        """Ingest an update from external source (webhook, crawler, etc.)."""
        update = RegulatoryUpdate(
            source_name=update_data.get("source", "Unknown"),
            title=update_data.get("title", ""),
            summary=update_data.get("summary", ""),
            content=update_data.get("content", ""),
            url=update_data.get("url", ""),
            jurisdiction=update_data.get("jurisdiction", ""),
            framework=update_data.get("framework", ""),
            update_type=UpdateType(update_data.get("type", "new_regulation")),
            severity=UpdateSeverity(update_data.get("severity", "medium")),
            keywords=update_data.get("keywords", []),
            metadata=update_data.get("metadata", {}),
        )
        
        if update_data.get("effective_date"):
            update.effective_date = datetime.fromisoformat(update_data["effective_date"])
        if update_data.get("published_date"):
            update.published_date = datetime.fromisoformat(update_data["published_date"])
        
        update.content_hash = self._hash_content(update.content)
        self._update_cache[str(update.id)] = update
        
        return update

    def generate_digest(
        self,
        updates: list[RegulatoryUpdate],
        organization_id: UUID | None = None,
    ) -> IntelligenceDigest:
        """Generate a digest from a list of updates."""
        digest = IntelligenceDigest(
            organization_id=organization_id,
            period_start=min(u.detected_at for u in updates) if updates else datetime.utcnow(),
            period_end=max(u.detected_at for u in updates) if updates else datetime.utcnow(),
            total_updates=len(updates),
            critical_count=sum(1 for u in updates if u.severity == UpdateSeverity.CRITICAL),
            high_count=sum(1 for u in updates if u.severity == UpdateSeverity.HIGH),
            medium_count=sum(1 for u in updates if u.severity == UpdateSeverity.MEDIUM),
            updates=updates,
        )
        
        # Generate summary
        if updates:
            digest.summary = self._generate_digest_summary(updates)
        else:
            digest.summary = "No regulatory updates during this period."
        
        return digest

    def _generate_digest_summary(self, updates: list[RegulatoryUpdate]) -> str:
        """Generate a human-readable summary for a digest."""
        by_framework: dict[str, int] = {}
        by_jurisdiction: dict[str, int] = {}
        
        for u in updates:
            by_framework[u.framework] = by_framework.get(u.framework, 0) + 1
            by_jurisdiction[u.jurisdiction] = by_jurisdiction.get(u.jurisdiction, 0) + 1
        
        summary = f"## Regulatory Update Summary\n\n"
        summary += f"**{len(updates)}** updates detected.\n\n"
        
        # Top frameworks
        summary += "### By Framework\n"
        for fw, count in sorted(by_framework.items(), key=lambda x: -x[1])[:5]:
            summary += f"- {fw}: {count}\n"
        
        # Top jurisdictions
        summary += "\n### By Jurisdiction\n"
        for jur, count in sorted(by_jurisdiction.items(), key=lambda x: -x[1])[:5]:
            summary += f"- {jur}: {count}\n"
        
        # Critical updates
        critical = [u for u in updates if u.severity == UpdateSeverity.CRITICAL]
        if critical:
            summary += f"\n### ⚠️ Critical Updates ({len(critical)})\n"
            for u in critical[:3]:
                summary += f"- **{u.title}** ({u.framework})\n"
        
        return summary

    def get_available_sources(self) -> list[dict[str, Any]]:
        """Get list of available regulatory sources."""
        return [
            {
                "id": str(s.id),
                "name": s.name,
                "url": s.url,
                "jurisdiction": s.jurisdiction,
                "framework": s.framework,
                "category": s.category,
                "check_frequency_hours": s.check_frequency_hours,
                "is_active": s.is_active,
            }
            for s in self.sources
        ]


# Global feed instance
_feed_instance: IntelligenceFeed | None = None


def get_intelligence_feed() -> IntelligenceFeed:
    """Get or create the intelligence feed instance."""
    global _feed_instance
    if _feed_instance is None:
        _feed_instance = IntelligenceFeed()
    return _feed_instance
