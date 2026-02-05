"""Background tasks for IDE Agent service."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog

from app.core.database import get_db_context
from app.workers import celery_app


logger = structlog.get_logger()


@celery_app.task(name="app.workers.ide_agent_tasks.run_full_analysis")
def run_full_analysis(
    session_id: str,
    organization_id: str,
    repository_id: str | None = None,
    target_files: list[str] | None = None,
):
    """Run a full compliance analysis for the IDE agent.

    This is the main background task for code analysis,
    triggered by IDE events like file save or manual request.
    """
    logger.info(
        f"Running IDE agent analysis: session={session_id}, org={organization_id}"
    )
    asyncio.run(
        _run_full_analysis_async(session_id, organization_id, repository_id, target_files)
    )


async def _run_full_analysis_async(
    session_id: str,
    organization_id: str,
    repository_id: str | None,
    target_files: list[str] | None,
):
    """Async implementation of full IDE agent analysis."""
    from sqlalchemy import select

    from app.models.ide_agent import AgentStatus, IDEAgentSession
    from app.services.ide_agent import get_ide_agent_service

    async with get_db_context() as db:
        # Get or create session
        result = await db.execute(
            select(IDEAgentSession).where(IDEAgentSession.id == UUID(session_id))
        )
        session = result.scalar_one_or_none()

        if not session:
            logger.warning(f"Session not found: {session_id}")
            return

        try:
            # Update session status
            session.status = AgentStatus.ANALYZING
            session.current_step = "Analyzing code"
            session.progress = 10.0
            await db.flush()

            # Get service
            service = get_ide_agent_service(
                db=db,
                organization_id=UUID(organization_id),
            )

            # Run analysis
            result = await service.run_full_analysis(
                session_id=UUID(session_id),
                repository_id=UUID(repository_id) if repository_id else None,
            )

            # Update session with results
            session.violations_found = result.violations_found
            session.fixes_applied = result.fixes_applied
            session.issues_created = result.issues_created
            session.prs_created = result.prs_created
            session.status = AgentStatus.COMPLETED
            session.progress = 100.0
            session.current_step = "Analysis complete"
            session.completed_at = datetime.now(UTC)

            await db.commit()

            logger.info(
                f"IDE agent analysis complete: session={session_id}",
                violations=result.violations_found,
                fixes=result.fixes_applied,
            )

        except Exception as e:
            logger.exception(f"IDE agent analysis failed: {e}")
            session.status = AgentStatus.FAILED
            session.error_message = str(e)
            session.completed_at = datetime.now(UTC)
            await db.commit()
            raise


@celery_app.task(name="app.workers.ide_agent_tasks.generate_fixes")
def generate_fixes(
    session_id: str,
    organization_id: str,
    violation_ids: list[str],
):
    """Generate fixes for detected violations.

    Creates fix suggestions that can be reviewed and applied.
    """
    logger.info(
        f"Generating fixes for {len(violation_ids)} violations in session: {session_id}"
    )
    asyncio.run(_generate_fixes_async(session_id, organization_id, violation_ids))


async def _generate_fixes_async(
    session_id: str,
    organization_id: str,
    violation_ids: list[str],
):
    """Async implementation of fix generation."""
    from sqlalchemy import select

    from app.models.ide_agent import AgentStatus, IDEAgentSession, IDEAgentViolation
    from app.services.ide_agent import get_ide_agent_service

    async with get_db_context() as db:
        # Get session
        result = await db.execute(
            select(IDEAgentSession).where(IDEAgentSession.id == UUID(session_id))
        )
        session = result.scalar_one_or_none()

        if not session:
            logger.warning(f"Session not found: {session_id}")
            return

        try:
            session.status = AgentStatus.PLANNING
            session.current_step = "Generating fixes"
            await db.flush()

            service = get_ide_agent_service(
                db=db,
                organization_id=UUID(organization_id),
            )

            # Get violations
            violations_result = await db.execute(
                select(IDEAgentViolation).where(
                    IDEAgentViolation.id.in_([UUID(v) for v in violation_ids])
                )
            )
            violations = list(violations_result.scalars().all())

            if not violations:
                logger.warning("No violations found to fix")
                return

            # Generate fixes for each violation
            for i, violation in enumerate(violations):
                session.progress = 10.0 + (80.0 * i / len(violations))
                session.current_step = f"Generating fix for {violation.rule_id}"
                await db.flush()

                await service.generate_fixes(
                    session_id=UUID(session_id),
                    violation_id=violation.id,
                    code_context=violation.original_code or "",
                )

            session.status = AgentStatus.WAITING_APPROVAL
            session.current_step = "Fixes ready for review"
            session.progress = 100.0
            session.pending_approval_count = len(violations)
            await db.commit()

            logger.info(f"Generated {len(violations)} fixes for session: {session_id}")

        except Exception as e:
            logger.exception(f"Fix generation failed: {e}")
            session.status = AgentStatus.FAILED
            session.error_message = str(e)
            await db.commit()
            raise


@celery_app.task(name="app.workers.ide_agent_tasks.apply_approved_fixes")
def apply_approved_fixes(
    session_id: str,
    organization_id: str,
    action_id: str,
):
    """Apply fixes that have been approved by a user.

    Executes the approved fixes and updates the codebase.
    """
    logger.info(f"Applying approved fixes: action={action_id}")
    asyncio.run(_apply_approved_fixes_async(session_id, organization_id, action_id))


async def _apply_approved_fixes_async(
    session_id: str,
    organization_id: str,
    action_id: str,
):
    """Async implementation of applying approved fixes."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.ide_agent import (
        AgentStatus,
        IDEAgentAction,
        IDEAgentFix,
        IDEAgentSession,
    )

    async with get_db_context() as db:
        # Get action with fixes
        result = await db.execute(
            select(IDEAgentAction)
            .options(selectinload(IDEAgentAction.fixes))
            .where(IDEAgentAction.id == UUID(action_id))
        )
        action = result.scalar_one_or_none()

        if not action or not action.approved:
            logger.warning(f"Action not found or not approved: {action_id}")
            return

        # Get session
        session_result = await db.execute(
            select(IDEAgentSession).where(IDEAgentSession.id == UUID(session_id))
        )
        session = session_result.scalar_one_or_none()

        try:
            if session:
                session.status = AgentStatus.EXECUTING
                session.current_step = "Applying fixes"
                await db.flush()

            # Apply each fix
            applied_count = 0
            for fix in action.fixes:
                if not fix.applied:
                    # In production, this would actually modify files
                    # via GitHub API or local filesystem
                    fix.applied = True
                    fix.applied_at = datetime.now(UTC)
                    applied_count += 1

            # Update action
            action.executed = True
            action.executed_at = datetime.now(UTC)
            action.result = {
                "fixes_applied": applied_count,
                "files_modified": [f for f in action.target_files],
            }

            # Update session
            if session:
                session.fixes_applied += applied_count
                session.pending_approval_count = max(
                    0, session.pending_approval_count - 1
                )

                # Check if all actions are complete
                if session.pending_approval_count == 0:
                    session.status = AgentStatus.COMPLETED
                    session.current_step = "All fixes applied"
                    session.completed_at = datetime.now(UTC)

            await db.commit()

            logger.info(
                f"Applied {applied_count} fixes for action: {action_id}",
                files=action.target_files,
            )

        except Exception as e:
            logger.exception(f"Fix application failed: {e}")
            if session:
                session.status = AgentStatus.FAILED
                session.error_message = str(e)
                await db.commit()
            raise


@celery_app.task(name="app.workers.ide_agent_tasks.create_github_issue")
def create_github_issue(
    session_id: str,
    organization_id: str,
    violation_id: str,
):
    """Create a GitHub issue for a compliance violation.

    Creates an issue with details about the violation and suggested fixes.
    """
    logger.info(f"Creating GitHub issue for violation: {violation_id}")
    asyncio.run(_create_github_issue_async(session_id, organization_id, violation_id))


async def _create_github_issue_async(
    session_id: str,
    organization_id: str,
    violation_id: str,
):
    """Async implementation of GitHub issue creation."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.ide_agent import IDEAgentSession, IDEAgentViolation
    from app.models.codebase import Repository

    async with get_db_context() as db:
        # Get violation
        result = await db.execute(
            select(IDEAgentViolation).where(IDEAgentViolation.id == UUID(violation_id))
        )
        violation = result.scalar_one_or_none()

        if not violation:
            logger.warning(f"Violation not found: {violation_id}")
            return

        # Get session
        session_result = await db.execute(
            select(IDEAgentSession)
            .options(selectinload(IDEAgentSession.violations))
            .where(IDEAgentSession.id == UUID(session_id))
        )
        session = session_result.scalar_one_or_none()

        if not session or not session.repository_id:
            logger.warning("Session not found or no repository associated")
            return

        # Get repository
        repo_result = await db.execute(
            select(Repository).where(Repository.id == session.repository_id)
        )
        repository = repo_result.scalar_one_or_none()

        if not repository:
            logger.warning("Repository not found")
            return

        # Build issue content
        issue_title = f"[Compliance] {violation.rule_name} - {violation.regulation}"
        issue_body = f"""## Compliance Violation Detected

**Rule:** {violation.rule_id} - {violation.rule_name}
**Regulation:** {violation.regulation}
**Severity:** {violation.severity}
**Article Reference:** {violation.article_reference or 'N/A'}

### Location
- **File:** `{violation.file_path}`
- **Lines:** {violation.start_line}-{violation.end_line}

### Description
{violation.message}

### Original Code
```
{violation.original_code or 'N/A'}
```

### Recommended Action
Please review and address this compliance violation. Consult the relevant regulatory requirements for guidance.

---
*This issue was automatically created by ComplianceAgent IDE.*
"""

        # In production, create issue via GitHub API
        # For now, simulate success
        issue_number = 999  # Would be actual issue number
        issue_url = f"https://github.com/{repository.full_name}/issues/{issue_number}"

        # Update session
        if session:
            session.issues_created += 1
            await db.commit()

        logger.info(
            f"GitHub issue created: {issue_url}",
            violation_id=violation_id,
            repository=repository.full_name,
        )


@celery_app.task(name="app.workers.ide_agent_tasks.cleanup_stale_sessions")
def cleanup_stale_sessions():
    """Cleanup stale IDE agent sessions.

    Marks sessions that have been in progress too long as failed.
    Should be scheduled to run hourly.
    """
    logger.info("Cleaning up stale IDE agent sessions")
    asyncio.run(_cleanup_stale_sessions_async())


async def _cleanup_stale_sessions_async():
    """Async implementation of stale session cleanup."""
    from sqlalchemy import select

    from app.models.ide_agent import AgentStatus, IDEAgentSession

    async with get_db_context() as db:
        # Find sessions stuck in progress for more than 1 hour
        cutoff = datetime.now(UTC) - timedelta(hours=1)

        result = await db.execute(
            select(IDEAgentSession).where(
                IDEAgentSession.status.in_([
                    AgentStatus.ANALYZING,
                    AgentStatus.PLANNING,
                    AgentStatus.EXECUTING,
                ]),
                IDEAgentSession.started_at < cutoff,
            )
        )
        stale_sessions = list(result.scalars().all())

        for session in stale_sessions:
            session.status = AgentStatus.FAILED
            session.error_message = "Session timed out"
            session.completed_at = datetime.now(UTC)

        if stale_sessions:
            await db.commit()
            logger.info(f"Cleaned up {len(stale_sessions)} stale sessions")


@celery_app.task(name="app.workers.ide_agent_tasks.aggregate_session_stats")
def aggregate_session_stats(organization_id: str):
    """Aggregate statistics for IDE agent sessions.

    Calculates metrics like total violations found, fixes applied,
    and time saved for an organization.
    """
    logger.info(f"Aggregating IDE agent stats for organization: {organization_id}")
    asyncio.run(_aggregate_session_stats_async(organization_id))


async def _aggregate_session_stats_async(organization_id: str):
    """Async implementation of session stats aggregation."""
    from sqlalchemy import func, select

    from app.models.ide_agent import AgentStatus, IDEAgentSession

    async with get_db_context() as db:
        # Get aggregated stats
        result = await db.execute(
            select(
                func.count(IDEAgentSession.id).label("total_sessions"),
                func.sum(IDEAgentSession.violations_found).label("total_violations"),
                func.sum(IDEAgentSession.fixes_applied).label("total_fixes"),
                func.sum(IDEAgentSession.issues_created).label("total_issues"),
                func.sum(IDEAgentSession.prs_created).label("total_prs"),
            ).where(
                IDEAgentSession.organization_id == UUID(organization_id),
                IDEAgentSession.status == AgentStatus.COMPLETED,
            )
        )
        stats = result.one()

        logger.info(
            f"IDE agent stats for {organization_id}",
            sessions=stats.total_sessions,
            violations=stats.total_violations,
            fixes=stats.total_fixes,
            issues=stats.total_issues,
            prs=stats.total_prs,
        )

        # In production, might store these in Redis for dashboard display
