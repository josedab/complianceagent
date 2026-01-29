"""Analysis and processing background tasks."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog

from app.core.database import get_db_context
from app.workers import celery_app


logger = structlog.get_logger()


@celery_app.task(name="app.workers.analysis_tasks.analyze_repository")
def analyze_repository(repository_id: str, organization_id: str):
    """Analyze a repository for compliance."""
    logger.info(f"Analyzing repository: {repository_id}")
    asyncio.run(_analyze_repository_async(repository_id, organization_id))


async def _analyze_repository_async(repository_id: str, organization_id: str):
    """Async implementation of repository analysis."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.agents.orchestrator import ComplianceOrchestrator
    from app.models.codebase import Repository
    from app.models.requirement import Requirement

    async with get_db_context() as db:
        # Get repository
        result = await db.execute(
            select(Repository)
            .options(selectinload(Repository.customer_profile))
            .where(Repository.id == UUID(repository_id))
        )
        repository = result.scalar_one_or_none()

        if not repository:
            logger.warning(f"Repository not found: {repository_id}")
            return

        # Update status
        repository.analysis_status = "in_progress"
        await db.flush()

        try:
            # Get applicable frameworks
            profile = repository.customer_profile
            frameworks = profile.get_applicable_frameworks()

            # Get requirements for applicable frameworks
            from app.models.regulation import Regulation

            req_result = await db.execute(
                select(Requirement)
                .join(Regulation)
                .where(Regulation.framework.in_([f.value for f in frameworks]))
            )
            requirements = list(req_result.scalars().all())

            if not requirements:
                logger.info("No applicable requirements found")
                repository.analysis_status = "completed"
                await db.commit()
                return

            # Run analysis
            orchestrator = ComplianceOrchestrator(db, UUID(organization_id))
            mappings = await orchestrator.analyze_repository(repository, requirements)

            # Update repository stats
            repository.last_analyzed_at = datetime.now(UTC)
            repository.analysis_status = "completed"
            repository.total_requirements = len(requirements)
            repository.compliant_requirements = sum(
                1 for m in mappings if m.compliance_status.value == "compliant"
            )
            repository.gaps_critical = sum(m.critical_gaps for m in mappings)
            repository.gaps_major = sum(m.major_gaps for m in mappings)
            repository.gaps_minor = sum(m.minor_gaps for m in mappings)

            if repository.total_requirements > 0:
                repository.compliance_score = (
                    repository.compliant_requirements / repository.total_requirements * 100
                )

            await db.commit()
            logger.info(f"Repository analysis complete: {repository.full_name}")

        except Exception as e:
            logger.exception(f"Repository analysis failed: {e}")
            repository.analysis_status = "failed"
            await db.commit()
            raise


@celery_app.task(name="app.workers.analysis_tasks.generate_compliance_fix")
def generate_compliance_fix(mapping_id: str, organization_id: str):
    """Generate compliance fix for a mapping."""
    logger.info(f"Generating fix for mapping: {mapping_id}")
    asyncio.run(_generate_fix_async(mapping_id, organization_id))


async def _generate_fix_async(mapping_id: str, organization_id: str):
    """Async implementation of fix generation."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.agents.orchestrator import ComplianceOrchestrator
    from app.models.codebase import CodebaseMapping

    async with get_db_context() as db:
        result = await db.execute(
            select(CodebaseMapping)
            .options(
                selectinload(CodebaseMapping.requirement),
                selectinload(CodebaseMapping.repository),
            )
            .where(CodebaseMapping.id == UUID(mapping_id))
        )
        mapping = result.scalar_one_or_none()

        if not mapping:
            logger.warning(f"Mapping not found: {mapping_id}")
            return

        orchestrator = ComplianceOrchestrator(db, UUID(organization_id))
        result = await orchestrator.generate_compliance_fix(
            mapping=mapping,
            requirement=mapping.requirement,
            repository=mapping.repository,
        )

        # Store generated code in mapping
        from app.models.audit import ComplianceAction, ComplianceActionStatus

        if result.get("files"):
            action = ComplianceAction(
                organization_id=UUID(organization_id),
                regulation_id=mapping.requirement.regulation_id,
                requirement_id=mapping.requirement_id,
                repository_id=mapping.repository_id,
                mapping_id=mapping.id,
                title=result.get("pr_title", f"Compliance: {mapping.requirement.title}"),
                description=result.get("pr_body", ""),
                status=ComplianceActionStatus.AWAITING_REVIEW,
                generated_code={"files": result.get("files", [])},
                generated_tests={"tests": result.get("tests", [])},
                affected_files_count=len(result.get("files", [])),
            )
            db.add(action)

        await db.commit()
        logger.info(f"Fix generation complete for mapping: {mapping_id}")


@celery_app.task(name="app.workers.analysis_tasks.update_all_compliance_scores")
def update_all_compliance_scores():
    """Update compliance scores for all repositories."""
    logger.info("Updating all compliance scores")
    asyncio.run(_update_scores_async())


async def _update_scores_async():
    """Async implementation of score updates."""
    from sqlalchemy import func, select

    from app.models.codebase import CodebaseMapping, ComplianceStatus, Repository

    async with get_db_context() as db:
        result = await db.execute(select(Repository).where(Repository.is_active))
        repositories = list(result.scalars().all())

        for repo in repositories:
            # Count mappings by status
            mapping_result = await db.execute(
                select(
                    CodebaseMapping.compliance_status,
                    func.count(CodebaseMapping.id)
                )
                .where(CodebaseMapping.repository_id == repo.id)
                .group_by(CodebaseMapping.compliance_status)
            )

            status_counts = {row[0]: row[1] for row in mapping_result}

            total = sum(status_counts.values())
            compliant = status_counts.get(ComplianceStatus.COMPLIANT, 0)

            repo.total_requirements = total
            repo.compliant_requirements = compliant
            if total > 0:
                repo.compliance_score = compliant / total * 100

        await db.commit()
        logger.info(f"Updated scores for {len(repositories)} repositories")


@celery_app.task(name="app.workers.analysis_tasks.cleanup_old_data")
def cleanup_old_data():
    """Cleanup old audit trail entries and temporary data."""
    logger.info("Running data cleanup")
    asyncio.run(_cleanup_async())


async def _cleanup_async():
    """Async implementation of data cleanup."""
    from sqlalchemy import delete

    from app.models.audit import AuditTrail

    cutoff_date = datetime.now(UTC) - timedelta(days=365 * 7)  # 7 years retention

    async with get_db_context() as db:
        # Note: In production, you'd archive before deleting
        result = await db.execute(
            delete(AuditTrail).where(AuditTrail.created_at < cutoff_date)
        )
        logger.info(f"Cleaned up {result.rowcount} old audit entries")
        await db.commit()


@celery_app.task(name="app.workers.analysis_tasks.create_compliance_pr")
def create_compliance_pr(action_id: str, organization_id: str):
    """Create a PR for a compliance action."""
    logger.info(f"Creating PR for action: {action_id}")
    asyncio.run(_create_pr_async(action_id, organization_id))


async def _create_pr_async(action_id: str, organization_id: str):
    """Async implementation of PR creation."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.audit import AuditEventType, ComplianceAction, ComplianceActionStatus
    from app.services.audit.service import AuditService
    from app.services.github import GitHubClient

    async with get_db_context() as db:
        result = await db.execute(
            select(ComplianceAction)
            .options(selectinload(ComplianceAction.repository))
            .where(ComplianceAction.id == UUID(action_id))
        )
        action = result.scalar_one_or_none()

        if not action or not action.generated_code:
            logger.warning(f"Action not found or no generated code: {action_id}")
            return

        repository = action.repository
        owner, repo = repository.full_name.split("/")

        # Get access token (would come from encrypted storage)
        # access_token = decrypt(repository.access_token_encrypted)
        access_token = ""  # Placeholder

        if not access_token:
            logger.warning("No access token available")
            return

        async with GitHubClient(access_token=access_token) as github:
            # Get default branch SHA
            base_sha = await github.get_default_branch_sha(owner, repo)

            # Create branch
            branch_name = f"compliance/{action.requirement_id}"
            await github.create_branch(owner, repo, branch_name, base_sha)

            # Create/update files
            for file in action.generated_code.get("files", []):
                await github.create_or_update_file(
                    owner=owner,
                    repo=repo,
                    path=file["path"],
                    content=file.get("content", ""),
                    message=f"Compliance: {action.title}",
                    branch=branch_name,
                )

            # Create PR
            pr = await github.create_pull_request(
                owner=owner,
                repo=repo,
                title=action.title,
                body=action.description,
                head=branch_name,
                base=repository.default_branch,
                draft=True,
            )

            # Add labels
            await github.add_labels_to_pr(
                owner, repo, pr.number,
                ["compliance", "auto-generated"]
            )

            # Update action
            action.pr_url = pr.html_url
            action.pr_number = pr.number
            action.pr_status = pr.state
            action.pr_created_at = datetime.now(UTC)
            action.status = ComplianceActionStatus.IN_PROGRESS

            # Log audit event
            audit_service = AuditService(db)
            await audit_service.log_event(
                organization_id=UUID(organization_id),
                event_type=AuditEventType.PR_CREATED,
                event_description=f"Created PR #{pr.number} for {action.title}",
                compliance_action_id=action.id,
                event_data={
                    "pr_number": pr.number,
                    "pr_url": pr.html_url,
                },
                actor_type="system",
            )

            await db.commit()
            logger.info(f"Created PR #{pr.number} for action {action_id}")
