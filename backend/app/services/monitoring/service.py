"""Regulatory source monitoring service."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

import structlog
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db_context
from app.core.exceptions import MonitoringError, SourceFetchError, SourceParseError
from app.models.regulation import ChangeType, Regulation, RegulatorySource
from app.services.monitoring.crawler import ChangeDetector, CrawlerResult, RegulatoryCrawler


logger = structlog.get_logger()


@dataclass
class MonitoringHealth:
    """Health snapshot for the monitoring service."""

    is_running: bool = False
    last_cycle_at: datetime | None = None
    last_cycle_duration_seconds: float = 0.0
    total_cycles: int = 0
    sources_checked: int = 0
    changes_detected: int = 0
    errors_total: int = 0
    consecutive_cycle_failures: int = 0
    backpressure_paused_sources: int = 0
    uptime_seconds: float = 0.0
    started_at: datetime | None = None


@dataclass
class SourceBackpressure:
    """Per-source backpressure tracking — exponentially backs off failing sources."""

    consecutive_failures: int = 0
    next_eligible_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    skip_count: int = 0

    @property
    def is_paused(self) -> bool:
        return datetime.now(UTC) < self.next_eligible_at

    def record_failure(self) -> None:
        self.consecutive_failures += 1
        # Exponential backoff: 5m, 15m, 1h, 4h, 12h, max 24h
        backoff_minutes = min(5 * (3 ** (self.consecutive_failures - 1)), 1440)
        from datetime import timedelta
        self.next_eligible_at = datetime.now(UTC) + timedelta(minutes=backoff_minutes)
        self.skip_count += 1
        logger.warning(
            "Source backpressure activated",
            failures=self.consecutive_failures,
            backoff_minutes=backoff_minutes,
        )

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.next_eligible_at = datetime.now(UTC)


MAX_CONSECUTIVE_SOURCE_FAILURES = 10


class MonitoringService:
    """Service for monitoring regulatory sources."""

    def __init__(self):
        self.crawler: RegulatoryCrawler | None = None
        self.change_detector = ChangeDetector()
        self.on_change_callbacks: list[Callable] = []
        self._shutdown_event = asyncio.Event()
        self._health = MonitoringHealth()
        self._backpressure: dict[str, SourceBackpressure] = {}

    def get_health(self) -> MonitoringHealth:
        """Return current health snapshot."""
        if self._health.started_at:
            self._health.uptime_seconds = (
                datetime.now(UTC) - self._health.started_at
            ).total_seconds()
        self._health.backpressure_paused_sources = sum(
            1 for bp in self._backpressure.values() if bp.is_paused
        )
        return self._health

    def on_change(self, callback: Callable):
        """Register a callback for when changes are detected."""
        self.on_change_callbacks.append(callback)

    def stop(self):
        """Signal the monitoring loop to stop gracefully."""
        self._shutdown_event.set()

    async def start(self):
        """Start the monitoring service."""
        logger.info("Starting regulatory monitoring service")
        self._health.is_running = True
        self._health.started_at = datetime.now(UTC)

        while not self._shutdown_event.is_set():
            cycle_start = datetime.now(UTC)
            try:
                await self.check_all_sources()
                self._health.consecutive_cycle_failures = 0
            except (SourceFetchError, SourceParseError) as e:
                logger.warning(
                    "Source monitoring error",
                    error_type=type(e).__name__,
                    error=str(e),
                )
                self._health.errors_total += 1
            except MonitoringError as e:
                logger.error(
                    "Monitoring service error",
                    error_type=type(e).__name__,
                    error=str(e),
                )
                self._health.errors_total += 1
                self._health.consecutive_cycle_failures += 1
            except asyncio.CancelledError:
                logger.info("Monitoring service shutdown requested")
                break
            except Exception as e:
                logger.exception(
                    "Unexpected error in monitoring loop",
                    error_type=type(e).__name__,
                    error=str(e),
                )
                self._health.errors_total += 1
                self._health.consecutive_cycle_failures += 1

            self._health.total_cycles += 1
            self._health.last_cycle_at = datetime.now(UTC)
            self._health.last_cycle_duration_seconds = (
                datetime.now(UTC) - cycle_start
            ).total_seconds()

            # Wait for next check interval or shutdown signal
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=settings.monitoring_interval_hours * 3600,
                )
            except asyncio.TimeoutError:
                pass

        self._health.is_running = False
        logger.info("Monitoring service stopped")

    async def check_all_sources(self):
        """Check all active regulatory sources for changes, respecting backpressure."""
        async with get_db_context() as db:
            result = await db.execute(
                select(RegulatorySource)
                .where(RegulatorySource.is_active)
                .order_by(RegulatorySource.last_checked_at.asc().nullsfirst())
            )
            sources = list(result.scalars().all())

        # Filter out sources under backpressure
        eligible_sources = []
        for source in sources:
            source_id = str(source.id)
            bp = self._backpressure.get(source_id)
            if bp and bp.is_paused:
                logger.debug("Skipping source (backpressure)", source=source.name)
                continue
            eligible_sources.append(source)

        logger.info(
            f"Checking {len(eligible_sources)} sources ({len(sources) - len(eligible_sources)} paused)",
        )

        # Process sources with concurrency limit
        semaphore = asyncio.Semaphore(settings.max_concurrent_crawlers)

        async def check_with_limit(source: RegulatorySource):
            async with semaphore:
                return await self.check_source(source)

        results = await asyncio.gather(
            *[check_with_limit(source) for source in eligible_sources],
            return_exceptions=True,
        )

        # Log results and update backpressure
        changes_detected = 0
        errors = 0
        for i, r in enumerate(results):
            source_id = str(eligible_sources[i].id)
            if isinstance(r, Exception):
                errors += 1
                bp = self._backpressure.setdefault(source_id, SourceBackpressure())
                bp.record_failure()
            elif isinstance(r, CrawlerResult):
                if r.has_changed:
                    changes_detected += 1
                bp = self._backpressure.get(source_id)
                if bp:
                    bp.record_success()

        self._health.sources_checked += len(eligible_sources)
        self._health.changes_detected += changes_detected
        self._health.errors_total += errors

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
