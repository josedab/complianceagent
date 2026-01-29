"""Regulatory source monitoring service."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime

import structlog
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db_context
from app.core.exceptions import MonitoringError, SourceFetchError, SourceParseError
from app.models.regulation import ChangeType, Regulation, RegulatorySource
from app.services.monitoring.crawler import ChangeDetector, CrawlerResult, RegulatoryCrawler


logger = structlog.get_logger()


class MonitoringService:
    """Service for monitoring regulatory sources."""

    def __init__(self):
        self.crawler: RegulatoryCrawler | None = None
        self.change_detector = ChangeDetector()
        self.on_change_callbacks: list[Callable] = []
        self._shutdown_event = asyncio.Event()

    def on_change(self, callback: Callable):
        """Register a callback for when changes are detected."""
        self.on_change_callbacks.append(callback)

    def stop(self):
        """Signal the monitoring loop to stop gracefully."""
        self._shutdown_event.set()

    async def start(self):
        """Start the monitoring service."""
        logger.info("Starting regulatory monitoring service")

        while not self._shutdown_event.is_set():
            try:
                await self.check_all_sources()
            except (SourceFetchError, SourceParseError) as e:
                # Known monitoring errors - log and continue
                logger.warning(
                    "Source monitoring error",
                    error_type=type(e).__name__,
                    error=str(e),
                )
            except MonitoringError as e:
                # Other monitoring errors - log and continue
                logger.error(
                    "Monitoring service error",
                    error_type=type(e).__name__,
                    error=str(e),
                )
            except asyncio.CancelledError:
                # Clean shutdown requested
                logger.info("Monitoring service shutdown requested")
                break
            except Exception as e:
                # Unexpected errors - log with full traceback but continue
                logger.exception(
                    "Unexpected error in monitoring loop",
                    error_type=type(e).__name__,
                    error=str(e),
                )

            # Wait for next check interval or shutdown signal
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=settings.monitoring_interval_hours * 3600,
                )
            except asyncio.TimeoutError:
                # Normal timeout - continue to next check
                pass

        logger.info("Monitoring service stopped")

    async def check_all_sources(self):
        """Check all active regulatory sources for changes."""
        async with get_db_context() as db:
            result = await db.execute(
                select(RegulatorySource)
                .where(RegulatorySource.is_active)
                .order_by(RegulatorySource.last_checked_at.asc().nullsfirst())
            )
            sources = list(result.scalars().all())

        logger.info(f"Checking {len(sources)} regulatory sources")

        # Process sources with concurrency limit
        semaphore = asyncio.Semaphore(settings.max_concurrent_crawlers)

        async def check_with_limit(source: RegulatorySource):
            async with semaphore:
                return await self.check_source(source)

        results = await asyncio.gather(
            *[check_with_limit(source) for source in sources],
            return_exceptions=True,
        )

        # Log results
        changes_detected = sum(1 for r in results if isinstance(r, CrawlerResult) and r.has_changed)
        errors = sum(1 for r in results if isinstance(r, Exception))

        logger.info(
            "Monitoring cycle complete",
            sources_checked=len(sources),
            changes_detected=changes_detected,
            errors=errors,
        )

    async def check_source(self, source: RegulatorySource) -> CrawlerResult | None:
        """Check a single regulatory source for changes."""
        logger.info(f"Checking source: {source.name}", url=source.url)

        try:
            async with RegulatoryCrawler() as crawler:
                result = await crawler.crawl(source)

            # Update source tracking
            async with get_db_context() as db:
                db_source = await db.get(RegulatorySource, source.id)
                db_source.last_checked_at = datetime.now(UTC)
                db_source.total_checks += 1
                db_source.successful_checks += 1
                db_source.consecutive_failures = 0

                if result.has_changed:
                    db_source.last_change_detected_at = datetime.now(UTC)
                    db_source.last_content_hash = result.content_hash

                if result.etag:
                    db_source.last_etag = result.etag

                await db.commit()

            # Process changes
            if result.has_changed:
                await self._process_change(source, result)

            return result

        except Exception as e:
            logger.exception(f"Error checking source: {source.name}", error=str(e))

            # Update failure tracking
            async with get_db_context() as db:
                db_source = await db.get(RegulatorySource, source.id)
                db_source.last_checked_at = datetime.now(UTC)
                db_source.total_checks += 1
                db_source.consecutive_failures += 1
                await db.commit()

            raise

    async def _process_change(self, source: RegulatorySource, result: CrawlerResult):
        """Process a detected change."""
        logger.info(f"Change detected in source: {source.name}")

        # Create regulation record for the change
        async with get_db_context() as db:
            regulation = Regulation(
                source_id=source.id,
                name=f"Update from {source.name} - {datetime.now(UTC).strftime('%Y-%m-%d')}",
                jurisdiction=source.jurisdiction,
                framework=source.framework,
                change_type=ChangeType.AMENDMENT,
                source_url=source.url,
                metadata={
                    "crawl_result": result.metadata,
                    "content_hash": result.content_hash,
                },
            )
            db.add(regulation)
            await db.commit()
            await db.refresh(regulation)

        # Notify callbacks
        for callback in self.on_change_callbacks:
            try:
                await callback(regulation, result)
            except Exception as e:
                logger.exception("Error in change callback", error=str(e))


# Global service instance
monitoring_service = MonitoringService()
