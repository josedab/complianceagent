"""Background tasks for Pattern Marketplace service."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog

from app.core.database import get_db_context
from app.workers import celery_app


logger = structlog.get_logger()


@celery_app.task(name="app.workers.pattern_marketplace_tasks.update_pattern_metrics")
def update_pattern_metrics(pattern_id: str):
    """Update metrics for a pattern (downloads, ratings, etc.).

    Called when patterns are installed or rated.
    """
    logger.info(f"Updating metrics for pattern: {pattern_id}")
    asyncio.run(_update_pattern_metrics_async(pattern_id))


async def _update_pattern_metrics_async(pattern_id: str):
    """Async implementation of pattern metrics update."""
    from sqlalchemy import func, select

    from app.models.pattern_marketplace import (
        CompliancePattern,
        PatternInstallation,
        PatternRating,
    )

    async with get_db_context() as db:
        # Get pattern
        result = await db.execute(
            select(CompliancePattern).where(CompliancePattern.id == UUID(pattern_id))
        )
        pattern = result.scalar_one_or_none()

        if not pattern:
            logger.warning(f"Pattern not found: {pattern_id}")
            return

        # Count installations (downloads)
        install_result = await db.execute(
            select(func.count(PatternInstallation.id)).where(
                PatternInstallation.pattern_id == UUID(pattern_id)
            )
        )
        pattern.downloads = install_result.scalar() or 0

        # Count active users (enabled installations)
        active_result = await db.execute(
            select(func.count(PatternInstallation.id)).where(
                PatternInstallation.pattern_id == UUID(pattern_id),
                PatternInstallation.enabled == True,
            )
        )
        pattern.active_users = active_result.scalar() or 0

        # Calculate average rating
        rating_result = await db.execute(
            select(
                func.avg(PatternRating.rating),
                func.count(PatternRating.id),
            ).where(PatternRating.pattern_id == UUID(pattern_id))
        )
        avg_rating, rating_count = rating_result.one()
        pattern.avg_rating = float(avg_rating) if avg_rating else 0.0
        pattern.rating_count = rating_count or 0

        await db.commit()

        logger.info(
            f"Pattern metrics updated: {pattern_id}",
            downloads=pattern.downloads,
            active_users=pattern.active_users,
            avg_rating=pattern.avg_rating,
        )


@celery_app.task(name="app.workers.pattern_marketplace_tasks.process_publisher_payout")
def process_publisher_payout(organization_id: str):
    """Process payout for a publisher.

    Calculates earnings from recent purchases and initiates transfer.
    """
    logger.info(f"Processing payout for publisher: {organization_id}")
    asyncio.run(_process_publisher_payout_async(organization_id))


async def _process_publisher_payout_async(organization_id: str):
    """Async implementation of publisher payout processing."""
    from sqlalchemy import select

    from app.models.pattern_marketplace import (
        CompliancePattern,
        PatternPurchase,
        PublisherProfile,
    )

    async with get_db_context() as db:
        # Get publisher profile
        result = await db.execute(
            select(PublisherProfile).where(
                PublisherProfile.organization_id == UUID(organization_id)
            )
        )
        profile = result.scalar_one_or_none()

        if not profile or not profile.stripe_connect_account_id:
            logger.warning(f"Publisher not configured for payouts: {organization_id}")
            return

        # Get patterns by this publisher
        patterns_result = await db.execute(
            select(CompliancePattern).where(
                CompliancePattern.publisher_org_id == UUID(organization_id)
            )
        )
        patterns = list(patterns_result.scalars().all())
        pattern_ids = [p.id for p in patterns]

        if not pattern_ids:
            return

        # Get unpaid purchases (not already transferred)
        # In production, you'd track which purchases have been paid out
        purchases_result = await db.execute(
            select(PatternPurchase).where(
                PatternPurchase.pattern_id.in_(pattern_ids),
                PatternPurchase.refunded == False,
            )
        )
        purchases = list(purchases_result.scalars().all())

        # Calculate total earnings (publisher gets 70%)
        total_earnings = sum(p.price_paid * 0.7 for p in purchases)

        # Update profile
        profile.total_earnings = total_earnings
        profile.pending_payout = total_earnings  # Would track actual payouts

        await db.commit()

        logger.info(
            f"Payout calculated for publisher: {organization_id}",
            total_earnings=total_earnings,
            purchase_count=len(purchases),
        )


@celery_app.task(name="app.workers.pattern_marketplace_tasks.check_pattern_updates")
def check_pattern_updates(organization_id: str):
    """Check for pattern updates for an organization's installed patterns.

    Notifies organization when updates are available for installed patterns.
    """
    logger.info(f"Checking pattern updates for organization: {organization_id}")
    asyncio.run(_check_pattern_updates_async(organization_id))


async def _check_pattern_updates_async(organization_id: str):
    """Async implementation of pattern update checking."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.pattern_marketplace import (
        CompliancePattern,
        PatternInstallation,
    )

    async with get_db_context() as db:
        # Get installations with auto_update enabled
        result = await db.execute(
            select(PatternInstallation)
            .options(selectinload(PatternInstallation.pattern))
            .where(
                PatternInstallation.organization_id == UUID(organization_id),
                PatternInstallation.auto_update == True,
                PatternInstallation.enabled == True,
            )
        )
        installations = list(result.scalars().all())

        updates_available = []
        for installation in installations:
            pattern = installation.pattern
            if pattern and installation.installed_version != pattern.current_version:
                updates_available.append({
                    "pattern_id": str(pattern.id),
                    "pattern_name": pattern.name,
                    "installed_version": installation.installed_version,
                    "latest_version": pattern.current_version,
                })

                # Auto-update if enabled
                installation.installed_version = pattern.current_version
                installation.updated_at = datetime.now(UTC)

        if updates_available:
            await db.commit()
            logger.info(
                f"Auto-updated {len(updates_available)} patterns for org: {organization_id}",
                updates=updates_available,
            )

            # Queue notification
            notify_pattern_updates.delay(organization_id, updates_available)


@celery_app.task(name="app.workers.pattern_marketplace_tasks.notify_pattern_updates")
def notify_pattern_updates(organization_id: str, updates: list[dict]):
    """Send notification about pattern updates.

    Called by check_pattern_updates when updates are available.
    """
    logger.info(
        f"Notifying organization {organization_id} of {len(updates)} pattern updates"
    )
    # In production, this would send email/webhook notifications
    # For now, just log
    for update in updates:
        logger.info(
            f"Pattern update: {update['pattern_name']} "
            f"{update['installed_version']} -> {update['latest_version']}"
        )


@celery_app.task(name="app.workers.pattern_marketplace_tasks.update_marketplace_stats")
def update_marketplace_stats():
    """Periodic task to update global marketplace statistics.

    Should be scheduled to run hourly.
    """
    logger.info("Updating marketplace statistics")
    asyncio.run(_update_marketplace_stats_async())


async def _update_marketplace_stats_async():
    """Async implementation of marketplace stats update."""
    from sqlalchemy import func, select

    from app.models.pattern_marketplace import (
        CompliancePattern,
        PatternPurchase,
        PublishStatus,
    )

    async with get_db_context() as db:
        # Count published patterns
        pattern_count = await db.execute(
            select(func.count(CompliancePattern.id)).where(
                CompliancePattern.status == PublishStatus.PUBLISHED
            )
        )
        total_patterns = pattern_count.scalar() or 0

        # Total downloads
        download_sum = await db.execute(
            select(func.sum(CompliancePattern.downloads)).where(
                CompliancePattern.status == PublishStatus.PUBLISHED
            )
        )
        total_downloads = download_sum.scalar() or 0

        # Total revenue
        revenue_sum = await db.execute(
            select(func.sum(PatternPurchase.price_paid)).where(
                PatternPurchase.refunded == False
            )
        )
        total_revenue = revenue_sum.scalar() or 0

        # Count unique publishers
        publisher_count = await db.execute(
            select(func.count(func.distinct(CompliancePattern.publisher_org_id))).where(
                CompliancePattern.status == PublishStatus.PUBLISHED
            )
        )
        total_publishers = publisher_count.scalar() or 0

        logger.info(
            "Marketplace stats updated",
            total_patterns=total_patterns,
            total_downloads=total_downloads,
            total_revenue=total_revenue,
            total_publishers=total_publishers,
        )

        # In production, might store these in Redis for quick access


@celery_app.task(name="app.workers.pattern_marketplace_tasks.cleanup_expired_installations")
def cleanup_expired_installations():
    """Clean up expired pattern installations.

    Removes installations for patterns that have been deprecated
    or where licenses have expired.
    """
    logger.info("Cleaning up expired installations")
    asyncio.run(_cleanup_expired_installations_async())


async def _cleanup_expired_installations_async():
    """Async implementation of expired installations cleanup."""
    from sqlalchemy import select

    from app.models.pattern_marketplace import (
        CompliancePattern,
        PatternInstallation,
        PatternPurchase,
        PublishStatus,
    )

    async with get_db_context() as db:
        now = datetime.now(UTC)

        # Find installations of deprecated patterns
        result = await db.execute(
            select(PatternInstallation)
            .join(CompliancePattern)
            .where(CompliancePattern.status == PublishStatus.DEPRECATED)
        )
        deprecated_installations = list(result.scalars().all())

        disabled_count = 0
        for installation in deprecated_installations:
            installation.enabled = False
            disabled_count += 1

        # Find expired purchases (if licenses have expiration)
        expired_result = await db.execute(
            select(PatternPurchase).where(
                PatternPurchase.expires_at < now,
                PatternPurchase.refunded == False,
            )
        )
        expired_purchases = list(expired_result.scalars().all())

        for purchase in expired_purchases:
            # Disable related installations
            install_result = await db.execute(
                select(PatternInstallation).where(
                    PatternInstallation.pattern_id == purchase.pattern_id,
                    PatternInstallation.organization_id == purchase.organization_id,
                )
            )
            for installation in install_result.scalars():
                installation.enabled = False
                disabled_count += 1

        if disabled_count > 0:
            await db.commit()
            logger.info(f"Disabled {disabled_count} expired/deprecated installations")
