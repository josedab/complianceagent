"""Background tasks for Risk Quantification service."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID

import structlog

from app.core.database import get_db_context
from app.workers import celery_app


logger = structlog.get_logger()


@celery_app.task(name="app.workers.risk_quantification_tasks.calculate_repository_risk")
def calculate_repository_risk(repository_id: str, organization_id: str):
    """Calculate and update risk profile for a repository.

    This task runs the full risk assessment for a repository,
    aggregating violation risks and generating a risk profile.
    """
    logger.info(f"Calculating risk for repository: {repository_id}")
    asyncio.run(_calculate_repository_risk_async(repository_id, organization_id))


async def _calculate_repository_risk_async(repository_id: str, organization_id: str):
    """Async implementation of repository risk calculation."""
    from sqlalchemy import select

    from app.models.codebase import Repository
    from app.models.risk_quantification import RepositoryRiskProfile, ViolationRisk
    from app.services.risk_quantification import get_risk_quantification_service

    async with get_db_context() as db:
        # Get repository
        result = await db.execute(
            select(Repository).where(Repository.id == UUID(repository_id))
        )
        repository = result.scalar_one_or_none()

        if not repository:
            logger.warning(f"Repository not found: {repository_id}")
            return

        # Get service and generate profile
        service = get_risk_quantification_service(
            db=db,
            organization_id=UUID(organization_id),
        )

        profile = await service.generate_repository_profile(
            repository_id=UUID(repository_id),
            repository_name=repository.full_name,
        )

        # Store profile in database
        existing = await db.execute(
            select(RepositoryRiskProfile).where(
                RepositoryRiskProfile.repository_id == UUID(repository_id)
            )
        )
        db_profile = existing.scalar_one_or_none()

        if db_profile:
            # Update existing profile
            db_profile.total_violations = profile.total_violations
            db_profile.critical_violations = profile.critical_violations
            db_profile.high_violations = profile.high_violations
            db_profile.medium_violations = profile.medium_violations
            db_profile.low_violations = profile.low_violations
            db_profile.total_min_exposure = profile.total_min_exposure
            db_profile.total_max_exposure = profile.total_max_exposure
            db_profile.total_expected_exposure = profile.total_expected_exposure
            db_profile.exposure_by_regulation = profile.exposure_by_regulation
            db_profile.exposure_by_category = profile.exposure_by_category
            db_profile.overall_risk_score = profile.overall_risk_score
            db_profile.data_privacy_score = profile.data_privacy_score
            db_profile.security_score = profile.security_score
            db_profile.compliance_score = profile.compliance_score
            db_profile.last_full_scan_at = datetime.now(UTC)
        else:
            # Create new profile
            db_profile = RepositoryRiskProfile(
                organization_id=UUID(organization_id),
                repository_id=UUID(repository_id),
                repository_name=repository.full_name,
                total_violations=profile.total_violations,
                critical_violations=profile.critical_violations,
                high_violations=profile.high_violations,
                medium_violations=profile.medium_violations,
                low_violations=profile.low_violations,
                total_min_exposure=profile.total_min_exposure,
                total_max_exposure=profile.total_max_exposure,
                total_expected_exposure=profile.total_expected_exposure,
                exposure_by_regulation=profile.exposure_by_regulation,
                exposure_by_category=profile.exposure_by_category,
                overall_risk_score=profile.overall_risk_score,
                data_privacy_score=profile.data_privacy_score,
                security_score=profile.security_score,
                compliance_score=profile.compliance_score,
                last_full_scan_at=datetime.now(UTC),
            )
            db.add(db_profile)

        await db.commit()
        logger.info(
            f"Risk profile updated for repository: {repository_id}",
            risk_score=profile.overall_risk_score,
            expected_exposure=profile.total_expected_exposure,
        )


@celery_app.task(name="app.workers.risk_quantification_tasks.generate_org_risk_snapshot")
def generate_org_risk_snapshot(organization_id: str):
    """Generate and store a risk snapshot for an organization.

    This task aggregates risk data across all repositories
    and creates a point-in-time snapshot.
    """
    logger.info(f"Generating risk snapshot for organization: {organization_id}")
    asyncio.run(_generate_org_risk_snapshot_async(organization_id))


async def _generate_org_risk_snapshot_async(organization_id: str):
    """Async implementation of org risk snapshot generation."""
    from sqlalchemy import func, select

    from app.models.organization import Organization
    from app.models.risk_quantification import (
        OrganizationRiskSnapshot,
        RepositoryRiskProfile,
        RiskTrend,
    )

    async with get_db_context() as db:
        # Get organization
        result = await db.execute(
            select(Organization).where(Organization.id == UUID(organization_id))
        )
        org = result.scalar_one_or_none()

        if not org:
            logger.warning(f"Organization not found: {organization_id}")
            return

        # Aggregate risk profiles
        profiles_result = await db.execute(
            select(RepositoryRiskProfile).where(
                RepositoryRiskProfile.organization_id == UUID(organization_id)
            )
        )
        profiles = list(profiles_result.scalars().all())

        # Calculate aggregates
        total_min = sum(p.total_min_exposure for p in profiles)
        total_max = sum(p.total_max_exposure for p in profiles)
        total_expected = sum(p.total_expected_exposure for p in profiles)

        # Aggregate by regulation
        exposure_by_regulation: dict[str, float] = {}
        for profile in profiles:
            for reg, amount in (profile.exposure_by_regulation or {}).items():
                exposure_by_regulation[reg] = exposure_by_regulation.get(reg, 0) + amount

        # Aggregate by repository
        exposure_by_repository = {
            p.repository_name: p.total_expected_exposure for p in profiles
        }

        # Calculate overall risk score
        if profiles:
            overall_score = sum(p.overall_risk_score for p in profiles) / len(profiles)
        else:
            overall_score = 0

        # Determine grade
        if overall_score >= 90:
            grade = "A"
        elif overall_score >= 80:
            grade = "B"
        elif overall_score >= 70:
            grade = "C"
        elif overall_score >= 60:
            grade = "D"
        else:
            grade = "F"

        # Determine trend by comparing to previous snapshot
        prev_result = await db.execute(
            select(OrganizationRiskSnapshot)
            .where(OrganizationRiskSnapshot.organization_id == UUID(organization_id))
            .order_by(OrganizationRiskSnapshot.snapshot_date.desc())
            .limit(1)
        )
        prev_snapshot = prev_result.scalar_one_or_none()

        if prev_snapshot:
            if total_expected > prev_snapshot.total_expected_exposure * 1.1:
                trend = RiskTrend.INCREASING
            elif total_expected < prev_snapshot.total_expected_exposure * 0.9:
                trend = RiskTrend.DECREASING
            else:
                trend = RiskTrend.STABLE
        else:
            trend = RiskTrend.STABLE

        # Create snapshot
        snapshot = OrganizationRiskSnapshot(
            organization_id=UUID(organization_id),
            total_min_exposure=total_min,
            total_max_exposure=total_max,
            total_expected_exposure=total_expected,
            exposure_by_regulation=exposure_by_regulation,
            exposure_by_repository=exposure_by_repository,
            overall_risk_score=overall_score,
            risk_grade=grade,
            risk_trend=trend,
            snapshot_date=datetime.now(UTC),
        )

        db.add(snapshot)
        await db.commit()

        logger.info(
            f"Risk snapshot created for organization: {organization_id}",
            grade=grade,
            expected_exposure=total_expected,
            trend=trend.value,
        )


@celery_app.task(name="app.workers.risk_quantification_tasks.generate_executive_report")
def generate_executive_report(
    organization_id: str,
    report_type: str = "monthly",
    user_id: str | None = None,
):
    """Generate an executive risk report.

    Creates a comprehensive report with analysis, findings,
    and recommendations.
    """
    logger.info(
        f"Generating {report_type} executive report for organization: {organization_id}"
    )
    asyncio.run(_generate_executive_report_async(organization_id, report_type, user_id))


async def _generate_executive_report_async(
    organization_id: str,
    report_type: str,
    user_id: str | None,
):
    """Async implementation of executive report generation."""
    from datetime import timedelta

    from app.models.risk_quantification import RiskReport
    from app.services.risk_quantification import get_risk_quantification_service

    async with get_db_context() as db:
        service = get_risk_quantification_service(
            db=db,
            organization_id=UUID(organization_id),
        )

        # Generate report
        report = await service.generate_executive_report()

        # Determine report period
        now = datetime.now(UTC)
        if report_type == "weekly":
            period_start = now - timedelta(days=7)
        elif report_type == "monthly":
            period_start = now - timedelta(days=30)
        elif report_type == "quarterly":
            period_start = now - timedelta(days=90)
        else:
            period_start = now - timedelta(days=365)

        # Store report in database
        db_report = RiskReport(
            organization_id=UUID(organization_id),
            report_type=report_type,
            period_start=period_start,
            period_end=now,
            title=f"Risk Assessment Report - {report_type.title()}",
            summary=report.executive_summary,
            key_findings=report.key_findings,
            key_recommendations=report.recommendations,
            total_exposure=report.total_expected_exposure,
            risk_score=report.overall_risk_score,
            risk_grade=report.risk_grade,
            report_data=report.to_dict(),
            generated_by=UUID(user_id) if user_id else None,
        )

        db.add(db_report)
        await db.commit()

        logger.info(
            f"Executive report generated: {db_report.id}",
            report_type=report_type,
            grade=report.risk_grade,
        )


@celery_app.task(name="app.workers.risk_quantification_tasks.update_all_risk_scores")
def update_all_risk_scores():
    """Periodic task to update risk scores for all organizations.

    Should be scheduled to run daily.
    """
    logger.info("Updating risk scores for all organizations")
    asyncio.run(_update_all_risk_scores_async())


async def _update_all_risk_scores_async():
    """Async implementation of bulk risk score updates."""
    from sqlalchemy import select

    from app.models.organization import Organization
    from app.models.codebase import Repository

    async with get_db_context() as db:
        # Get all active organizations
        result = await db.execute(
            select(Organization).where(Organization.is_active == True)
        )
        organizations = list(result.scalars().all())

        for org in organizations:
            # Get all repositories for the organization
            repos_result = await db.execute(
                select(Repository).where(
                    Repository.organization_id == org.id,
                    Repository.is_active == True,
                )
            )
            repositories = list(repos_result.scalars().all())

            # Queue risk calculation for each repository
            for repo in repositories:
                calculate_repository_risk.delay(str(repo.id), str(org.id))

            # Queue organization snapshot after a delay to allow repo calculations
            generate_org_risk_snapshot.apply_async(
                args=[str(org.id)],
                countdown=300,  # 5 minutes delay
            )

        logger.info(f"Queued risk updates for {len(organizations)} organizations")
