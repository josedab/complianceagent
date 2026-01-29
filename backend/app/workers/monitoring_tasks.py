"""Regulatory monitoring background tasks."""

import asyncio
from datetime import UTC, datetime

import structlog

from app.core.database import get_db_context
from app.models.regulation import RegulatorySource
from app.services.monitoring.gdpr_sources import GDPRSourceMonitor
from app.services.monitoring.service import monitoring_service
from app.workers import celery_app


logger = structlog.get_logger()


@celery_app.task(name="app.workers.monitoring_tasks.check_all_sources")
def check_all_sources():
    """Check all regulatory sources for updates."""
    logger.info("Starting regulatory source check")
    asyncio.run(_check_all_sources_async())
    logger.info("Completed regulatory source check")


async def _check_all_sources_async():
    """Async implementation of source checking."""
    await monitoring_service.check_all_sources()


@celery_app.task(name="app.workers.monitoring_tasks.check_single_source")
def check_single_source(source_id: str):
    """Check a single regulatory source for updates."""
    logger.info(f"Checking source: {source_id}")
    asyncio.run(_check_single_source_async(source_id))


async def _check_single_source_async(source_id: str):
    """Async implementation of single source check."""
    async with get_db_context() as db:
        from uuid import UUID

        from sqlalchemy import select

        result = await db.execute(
            select(RegulatorySource).where(RegulatorySource.id == UUID(source_id))
        )
        source = result.scalar_one_or_none()

        if source:
            await monitoring_service.check_source(source)
        else:
            logger.warning(f"Source not found: {source_id}")


@celery_app.task(name="app.workers.monitoring_tasks.check_gdpr_sources")
def check_gdpr_sources():
    """Check all GDPR regulatory sources."""
    logger.info("Checking GDPR sources")
    asyncio.run(_check_gdpr_sources_async())


async def _check_gdpr_sources_async():
    """Async implementation of GDPR source checking."""
    from sqlalchemy import select

    from app.models.regulation import RegulatoryFramework

    async with get_db_context() as db:
        result = await db.execute(
            select(RegulatorySource).where(
                RegulatorySource.framework == RegulatoryFramework.GDPR,
                RegulatorySource.is_active,
            )
        )
        sources = list(result.scalars().all())

    monitor = GDPRSourceMonitor()

    for source in sources:
        try:
            if "eur-lex" in source.url.lower():
                result = await monitor.check_eur_lex(source)
            elif "edpb" in source.url.lower():
                result = await monitor.check_edpb(source)
            else:
                await monitoring_service.check_source(source)
                continue

            if result.get("changed"):
                logger.info(f"Changes detected in {source.name}", result=result)
                # Trigger processing
                process_regulatory_change.delay(str(source.id), result)

        except Exception as e:
            logger.exception(f"Error checking source {source.name}: {e}")


@celery_app.task(name="app.workers.monitoring_tasks.process_regulatory_change")
def process_regulatory_change(source_id: str, change_data: dict):
    """Process a detected regulatory change."""
    logger.info(f"Processing regulatory change from source: {source_id}")
    asyncio.run(_process_change_async(source_id, change_data))


async def _process_change_async(source_id: str, change_data: dict):
    """Async implementation of change processing."""
    from uuid import UUID

    from sqlalchemy import select

    from app.models.customer_profile import CustomerProfile
    from app.models.regulation import ChangeType, Regulation, RegulatorySource

    async with get_db_context() as db:
        # Get source
        result = await db.execute(
            select(RegulatorySource).where(RegulatorySource.id == UUID(source_id))
        )
        source = result.scalar_one_or_none()

        if not source:
            logger.warning(f"Source not found: {source_id}")
            return

        # Create regulation record
        regulation = Regulation(
            source_id=source.id,
            name=f"Update: {source.name} - {datetime.now(UTC).strftime('%Y-%m-%d')}",
            jurisdiction=source.jurisdiction,
            framework=source.framework,
            change_type=ChangeType.AMENDMENT,
            source_url=source.url,
            metadata=change_data,
        )
        db.add(regulation)
        await db.flush()

        # Get all organizations with relevant customer profiles
        from app.models.organization import Organization

        org_result = await db.execute(select(Organization))
        organizations = list(org_result.scalars().all())

        for org in organizations:
            # Get customer profiles
            profile_result = await db.execute(
                select(CustomerProfile).where(
                    CustomerProfile.organization_id == org.id
                )
            )
            profiles = list(profile_result.scalars().all())

            for profile in profiles:
                # Check if framework is relevant
                applicable = profile.get_applicable_frameworks()
                if source.framework in applicable:
                    # Queue analysis for this organization
                    analyze_regulation_for_org.delay(
                        str(regulation.id),
                        str(org.id),
                        str(profile.id),
                    )

        await db.commit()


@celery_app.task(name="app.workers.monitoring_tasks.analyze_regulation_for_org")
def analyze_regulation_for_org(regulation_id: str, organization_id: str, profile_id: str):
    """Analyze a regulation for a specific organization."""
    logger.info(
        f"Analyzing regulation {regulation_id} for org {organization_id}"
    )
    asyncio.run(_analyze_for_org_async(regulation_id, organization_id, profile_id))


async def _analyze_for_org_async(regulation_id: str, organization_id: str, profile_id: str):
    """Async implementation of organization-specific analysis."""
    from uuid import UUID

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.agents.orchestrator import ComplianceOrchestrator
    from app.models.customer_profile import CustomerProfile
    from app.models.regulation import Regulation

    async with get_db_context() as db:
        # Get regulation
        reg_result = await db.execute(
            select(Regulation).where(Regulation.id == UUID(regulation_id))
        )
        regulation = reg_result.scalar_one_or_none()

        # Get customer profile
        profile_result = await db.execute(
            select(CustomerProfile)
            .options(selectinload(CustomerProfile.repositories))
            .where(CustomerProfile.id == UUID(profile_id))
        )
        profile = profile_result.scalar_one_or_none()

        if not regulation or not profile:
            logger.warning("Regulation or profile not found")
            return

        # Initialize orchestrator
        orchestrator = ComplianceOrchestrator(db, UUID(organization_id))

        # Process the regulation
        content = regulation.extra_metadata.get("parsed", {}).get("content", "")
        if not content and regulation.content_summary:
            content = regulation.content_summary

        result = await orchestrator.process_regulatory_change(
            regulation=regulation,
            content=content,
            customer_profile=profile,
        )

        logger.info(f"Analysis complete: {result}")

        # If requirements were extracted, analyze repositories
        if result.get("saved_requirements"):
            from app.models.requirement import Requirement

            req_result = await db.execute(
                select(Requirement).where(
                    Requirement.regulation_id == regulation.id
                )
            )
            requirements = list(req_result.scalars().all())

            for repo in profile.repositories:
                if repo.is_active:
                    await orchestrator.analyze_repository(repo, requirements)

        await db.commit()
