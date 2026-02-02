"""PR Bot Celery tasks - Background processing for PR analysis."""

import asyncio
from uuid import UUID

import structlog

from app.core.database import get_db_context
from app.workers import celery_app

logger = structlog.get_logger()


@celery_app.task(
    name="app.workers.pr_bot_tasks.analyze_pr",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def analyze_pr(
    self,
    task_data: dict,
    access_token: str,
    organization_id: str | None = None,
):
    """Analyze a PR for compliance issues.
    
    Args:
        task_data: PRAnalysisTask data as dictionary
        access_token: GitHub access token
        organization_id: Optional organization ID for context
    """
    logger.info(
        "Starting PR analysis task",
        task_data=task_data,
        celery_task_id=self.request.id,
    )
    
    try:
        result = asyncio.run(
            _analyze_pr_async(task_data, access_token, organization_id)
        )
        return result
    except Exception as e:
        logger.exception("PR analysis failed", error=str(e))
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


async def _analyze_pr_async(
    task_data: dict,
    access_token: str,
    organization_id: str | None,
) -> dict:
    """Async implementation of PR analysis."""
    from app.services.pr_bot import PRBot, PRBotConfig
    from app.services.pr_bot.queue import PRAnalysisTask
    
    task = PRAnalysisTask.from_dict(task_data)
    
    # Load organization-specific config if available
    config = PRBotConfig()
    if organization_id:
        async with get_db_context() as db:
            from sqlalchemy import select
            from app.models.organization import Organization
            
            result = await db.execute(
                select(Organization).where(Organization.id == UUID(organization_id))
            )
            org = result.scalar_one_or_none()
            
            if org and org.settings:
                # Override config from organization settings
                settings = org.settings
                config.enabled_regulations = settings.get(
                    "enabled_regulations", config.enabled_regulations
                )
                config.block_on_critical = settings.get(
                    "block_on_critical", config.block_on_critical
                )
                config.block_on_high = settings.get(
                    "block_on_high", config.block_on_high
                )
                config.deep_analysis = settings.get(
                    "deep_analysis", config.deep_analysis
                )
    
    # Initialize bot and process
    bot = PRBot(config=config)
    result = await bot.process_task(task, access_token)
    
    # Store result in database
    if organization_id:
        await _store_analysis_result(result, organization_id)
    
    return result.to_dict()


async def _store_analysis_result(result, organization_id: str) -> None:
    """Store analysis result in database for tracking."""
    from datetime import UTC, datetime
    from sqlalchemy import select
    
    from app.models.audit import AuditEventType
    from app.services.audit.service import AuditService
    
    async with get_db_context() as db:
        # Find repository
        from app.models.codebase import Repository
        
        repo_result = await db.execute(
            select(Repository).where(
                Repository.full_name == f"{result.owner}/{result.repo}"
            )
        )
        repo = repo_result.scalar_one_or_none()
        
        # Log audit event
        audit_service = AuditService(db)
        await audit_service.log_event(
            organization_id=UUID(organization_id),
            event_type=AuditEventType.PR_ANALYZED,
            event_description=f"Analyzed PR #{result.pr_number} in {result.owner}/{result.repo}",
            repository_id=repo.id if repo else None,
            event_data={
                "pr_number": result.pr_number,
                "head_sha": result.head_sha,
                "files_analyzed": result.files_analyzed,
                "violations": result.total_violations,
                "critical": result.critical_count,
                "high": result.high_count,
                "medium": result.medium_count,
                "low": result.low_count,
                "passed": result.passed,
                "recommendation": result.recommendation,
                "check_run_id": result.check_run_id,
                "review_id": result.review_id,
                "labels_applied": result.labels_applied,
            },
            actor_type="system",
        )
        
        await db.commit()


@celery_app.task(name="app.workers.pr_bot_tasks.process_webhook")
def process_pr_webhook(
    event_type: str,
    event_data: dict,
    organization_id: str,
    access_token: str,
):
    """Process a GitHub webhook event for PR analysis.
    
    Args:
        event_type: GitHub event type (pull_request, etc.)
        event_data: Webhook payload
        organization_id: Organization ID
        access_token: GitHub access token
    """
    if event_type != "pull_request":
        logger.info(f"Ignoring non-PR event: {event_type}")
        return {"status": "ignored", "reason": f"Event type {event_type} not handled"}
    
    action = event_data.get("action")
    if action not in ("opened", "synchronize", "reopened"):
        logger.info(f"Ignoring PR action: {action}")
        return {"status": "ignored", "reason": f"Action {action} not handled"}
    
    # Create task and queue for processing
    return asyncio.run(
        _process_webhook_async(event_data, organization_id, access_token)
    )


async def _process_webhook_async(
    event_data: dict,
    organization_id: str,
    access_token: str,
) -> dict:
    """Async implementation of webhook processing."""
    from app.services.pr_bot import PRBot, PRBotConfig
    
    bot = PRBot(config=PRBotConfig())
    task = await bot.handle_pr_event(
        event_data, access_token, UUID(organization_id)
    )
    
    # Queue the analysis task
    analyze_pr.delay(
        task_data=task.to_dict(),
        access_token=access_token,
        organization_id=organization_id,
    )
    
    return {
        "status": "queued",
        "task_id": str(task.id),
        "pr_number": task.pr_number,
        "repo": f"{task.owner}/{task.repo}",
    }


@celery_app.task(name="app.workers.pr_bot_tasks.reanalyze_pr")
def reanalyze_pr(
    owner: str,
    repo: str,
    pr_number: int,
    access_token: str,
    organization_id: str | None = None,
):
    """Re-analyze an existing PR (e.g., after config change or fix applied)."""
    return asyncio.run(
        _reanalyze_pr_async(owner, repo, pr_number, access_token, organization_id)
    )


async def _reanalyze_pr_async(
    owner: str,
    repo: str,
    pr_number: int,
    access_token: str,
    organization_id: str | None,
) -> dict:
    """Async implementation of PR re-analysis."""
    from app.services.github.client import GitHubClient
    from app.services.pr_bot import PRBot, PRBotConfig
    from app.services.pr_bot.queue import PRAnalysisTask, PRTaskPriority
    
    # Get current PR info
    async with GitHubClient(access_token=access_token) as client:
        pr = await client.get_pull_request(owner, repo, pr_number)
    
    task = PRAnalysisTask(
        owner=owner,
        repo=repo,
        pr_number=pr_number,
        head_sha=pr.head_sha,
        organization_id=UUID(organization_id) if organization_id else None,
        priority=PRTaskPriority.HIGH,  # Re-analysis gets higher priority
    )
    
    bot = PRBot(config=PRBotConfig())
    result = await bot.process_task(task, access_token)
    
    return result.to_dict()


@celery_app.task(name="app.workers.pr_bot_tasks.create_fix_pr")
def create_fix_pr(
    owner: str,
    repo: str,
    pr_number: int,
    fixes: list[dict],
    access_token: str,
    organization_id: str | None = None,
):
    """Create a PR with automated compliance fixes."""
    return asyncio.run(
        _create_fix_pr_async(owner, repo, pr_number, fixes, access_token, organization_id)
    )


async def _create_fix_pr_async(
    owner: str,
    repo: str,
    pr_number: int,
    fixes: list[dict],
    access_token: str,
    organization_id: str | None,
) -> dict:
    """Async implementation of fix PR creation."""
    from app.services.pr_bot import PRBot, PRBotConfig
    
    bot = PRBot(config=PRBotConfig())
    result = await bot.create_fix_pr(owner, repo, pr_number, fixes, access_token)
    
    # Log audit event
    if organization_id and result.get("pr_number"):
        from app.models.audit import AuditEventType
        from app.services.audit.service import AuditService
        
        async with get_db_context() as db:
            audit_service = AuditService(db)
            await audit_service.log_event(
                organization_id=UUID(organization_id),
                event_type=AuditEventType.PR_CREATED,
                event_description=f"Created fix PR #{result['pr_number']} for PR #{pr_number}",
                event_data={
                    "source_pr": pr_number,
                    "fix_pr": result["pr_number"],
                    "fixes_count": result.get("fixes_applied", 0),
                },
                actor_type="system",
            )
            await db.commit()
    
    return result


@celery_app.task(name="app.workers.pr_bot_tasks.batch_analyze_prs")
def batch_analyze_prs(
    pr_list: list[dict],
    access_token: str,
    organization_id: str,
):
    """Analyze multiple PRs in batch (e.g., for backfill or re-analysis)."""
    results = []
    for pr_info in pr_list:
        try:
            result = analyze_pr.delay(
                task_data={
                    "owner": pr_info["owner"],
                    "repo": pr_info["repo"],
                    "pr_number": pr_info["pr_number"],
                    "head_sha": pr_info.get("head_sha", ""),
                },
                access_token=access_token,
                organization_id=organization_id,
            )
            results.append({
                "pr": f"{pr_info['owner']}/{pr_info['repo']}#{pr_info['pr_number']}",
                "task_id": result.id,
                "status": "queued",
            })
        except Exception as e:
            results.append({
                "pr": f"{pr_info['owner']}/{pr_info['repo']}#{pr_info['pr_number']}",
                "status": "failed",
                "error": str(e),
            })
    
    return {
        "total": len(pr_list),
        "queued": sum(1 for r in results if r["status"] == "queued"),
        "results": results,
    }
