"""Notification background tasks."""

import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import httpx
import structlog

from app.core.database import get_db_context
from app.workers import celery_app


logger = structlog.get_logger()


@celery_app.task(name="app.workers.notification_tasks.send_email")
def send_email(to: str, subject: str, body: str, html_body: str | None = None):
    """Send an email notification."""
    logger.info(f"Sending email to {to}: {subject}")
    asyncio.run(_send_email_async(to, subject, body, html_body))


async def _send_email_async(to: str, subject: str, body: str, html_body: str | None):
    """Async implementation of email sending."""
    # Placeholder - would integrate with email service (SendGrid, SES, etc.)
    logger.info(f"Email sent to {to}")


@celery_app.task(name="app.workers.notification_tasks.send_slack_notification")
def send_slack_notification(webhook_url: str, message: dict[str, Any]):
    """Send a Slack notification."""
    logger.info("Sending Slack notification")
    asyncio.run(_send_slack_async(webhook_url, message))


async def _send_slack_async(webhook_url: str, message: dict[str, Any]):
    """Async implementation of Slack notification."""
    async with httpx.AsyncClient() as client:
        response = await client.post(webhook_url, json=message)
        response.raise_for_status()
    logger.info("Slack notification sent")


@celery_app.task(name="app.workers.notification_tasks.notify_regulatory_change")
def notify_regulatory_change(organization_id: str, regulation_data: dict[str, Any]):
    """Notify organization of a regulatory change."""
    logger.info(f"Notifying org {organization_id} of regulatory change")
    asyncio.run(_notify_change_async(organization_id, regulation_data))


async def _notify_change_async(organization_id: str, regulation_data: dict[str, Any]):
    """Async implementation of regulatory change notification."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.organization import OrganizationMember

    async with get_db_context() as db:
        # Get organization members
        result = await db.execute(
            select(OrganizationMember)
            .options(selectinload(OrganizationMember.user))
            .where(OrganizationMember.organization_id == UUID(organization_id))
        )
        members = list(result.scalars().all())

        # Send notifications to admins
        for member in members:
            if member.role in ["owner", "admin"]:
                user = member.user
                # Queue email notification
                send_email.delay(
                    to=user.email,
                    subject=f"Regulatory Change Detected: {regulation_data.get('name', 'Unknown')}",
                    body=f"""
A new regulatory change has been detected that may affect your compliance status.

Regulation: {regulation_data.get('name')}
Jurisdiction: {regulation_data.get('jurisdiction')}
Framework: {regulation_data.get('framework')}

Please review the changes in your ComplianceAgent dashboard.
                    """.strip(),
                )


@celery_app.task(name="app.workers.notification_tasks.notify_compliance_gap")
def notify_compliance_gap(organization_id: str, gap_data: dict[str, Any]):
    """Notify organization of a compliance gap."""
    logger.info(f"Notifying org {organization_id} of compliance gap")
    asyncio.run(_notify_gap_async(organization_id, gap_data))


async def _notify_gap_async(organization_id: str, gap_data: dict[str, Any]):
    """Async implementation of compliance gap notification."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.organization import OrganizationMember

    severity = gap_data.get("severity", "unknown")

    # Only notify for critical gaps
    if severity != "critical":
        return

    async with get_db_context() as db:
        result = await db.execute(
            select(OrganizationMember)
            .options(selectinload(OrganizationMember.user))
            .where(OrganizationMember.organization_id == UUID(organization_id))
        )
        members = list(result.scalars().all())

        for member in members:
            if member.role in ["owner", "admin"]:
                user = member.user
                send_email.delay(
                    to=user.email,
                    subject="⚠️ Critical Compliance Gap Detected",
                    body=f"""
A critical compliance gap has been identified in your codebase.

Requirement: {gap_data.get('requirement_title')}
Repository: {gap_data.get('repository_name')}
Gap: {gap_data.get('description')}

Immediate action is recommended. Review in your ComplianceAgent dashboard.
                    """.strip(),
                )


@celery_app.task(name="app.workers.notification_tasks.send_daily_digest")
def send_daily_digest():
    """Send daily compliance digest to all organizations."""
    logger.info("Sending daily compliance digests")
    asyncio.run(_send_digest_async())


async def _send_digest_async():
    """Async implementation of daily digest."""
    from sqlalchemy import func, select
    from sqlalchemy.orm import selectinload

    from app.models.audit import ComplianceAction, ComplianceActionStatus
    from app.models.codebase import Repository
    from app.models.organization import Organization, OrganizationMember

    async with get_db_context() as db:
        # Get all organizations
        result = await db.execute(select(Organization))
        organizations = list(result.scalars().all())

        for org in organizations:
            # Get compliance stats
            repo_result = await db.execute(
                select(Repository)
                .join(Repository.customer_profile)
                .where(Repository.customer_profile.has(organization_id=org.id))
            )
            repos = list(repo_result.scalars().all())

            if not repos:
                continue

            # Calculate stats
            total_score = sum(r.compliance_score or 0 for r in repos)
            avg_score = total_score / len(repos) if repos else 0

            total_gaps = sum(
                (r.gaps_critical or 0) + (r.gaps_major or 0) + (r.gaps_minor or 0)
                for r in repos
            )

            # Get pending actions
            action_result = await db.execute(
                select(func.count())
                .select_from(ComplianceAction)
                .where(
                    ComplianceAction.organization_id == org.id,
                    ComplianceAction.status.in_([
                        ComplianceActionStatus.PENDING,
                        ComplianceActionStatus.AWAITING_REVIEW,
                    ])
                )
            )
            pending_actions = action_result.scalar() or 0

            # Get org admins
            member_result = await db.execute(
                select(OrganizationMember)
                .options(selectinload(OrganizationMember.user))
                .where(
                    OrganizationMember.organization_id == org.id,
                    OrganizationMember.role.in_(["owner", "admin"])
                )
            )
            members = list(member_result.scalars().all())

            for member in members:
                send_email.delay(
                    to=member.user.email,
                    subject=f"📊 Daily Compliance Digest - {org.name}",
                    body=f"""
Daily Compliance Summary for {org.name}

Overall Compliance Score: {avg_score:.1f}%
Repositories Monitored: {len(repos)}
Total Gaps: {total_gaps}
Pending Actions: {pending_actions}

Review your full dashboard at: https://app.complianceagent.ai/dashboard
                    """.strip(),
                )


@celery_app.task(name="app.workers.notification_tasks.notify_deadline_approaching")
def notify_deadline_approaching():
    """Notify organizations of approaching compliance deadlines."""
    logger.info("Checking for approaching deadlines")
    asyncio.run(_check_deadlines_async())


async def _check_deadlines_async():
    """Async implementation of deadline checking."""
    from datetime import timedelta

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.customer_profile import CustomerProfile
    from app.models.organization import OrganizationMember
    from app.models.regulation import Regulation

    warning_threshold = datetime.now(UTC).date() + timedelta(days=30)

    async with get_db_context() as db:
        # Get regulations with upcoming deadlines
        result = await db.execute(
            select(Regulation).where(
                Regulation.effective_date <= warning_threshold,
                Regulation.effective_date >= datetime.now(UTC).date(),
            )
        )
        regulations = list(result.scalars().all())

        for regulation in regulations:
            # Find affected organizations
            profile_result = await db.execute(
                select(CustomerProfile).where(
                    CustomerProfile.applicable_frameworks.contains([regulation.framework.value])
                )
            )
            profiles = list(profile_result.scalars().all())

            org_ids = {p.organization_id for p in profiles}

            for org_id in org_ids:
                # Get org admins
                member_result = await db.execute(
                    select(OrganizationMember)
                    .options(selectinload(OrganizationMember.user))
                    .where(
                        OrganizationMember.organization_id == org_id,
                        OrganizationMember.role.in_(["owner", "admin"])
                    )
                )
                members = list(member_result.scalars().all())

                days_left = (regulation.effective_date - datetime.now(UTC).date()).days

                for member in members:
                    send_email.delay(
                        to=member.user.email,
                        subject=f"⏰ Compliance Deadline: {regulation.name} - {days_left} days",
                        body=f"""
Upcoming Compliance Deadline

Regulation: {regulation.name}
Effective Date: {regulation.effective_date}
Days Remaining: {days_left}
Framework: {regulation.framework.value}
Jurisdiction: {regulation.jurisdiction.value}

Please ensure your systems are compliant before the deadline.
                        """.strip(),
                    )
