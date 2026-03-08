"""PR bot service facade — unified entry point for pull-request compliance analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

from app.services.pr_bot.bot import PRBot, PRBotConfig, PRBotResult
from app.services.pr_bot.checks import CheckConclusion, CheckOutput, ChecksService, CheckStatus
from app.services.pr_bot.comments import CommentService, CommentSeverity
from app.services.pr_bot.labels import ComplianceLabel, LabelService
from app.services.pr_bot.policy_gates import (
    PolicyEvaluationSummary,
    PolicyGateService,
    get_policy_gate_service,
)
from app.services.pr_bot.queue import PRAnalysisQueue, PRAnalysisTask


logger = structlog.get_logger(__name__)

__all__ = [
    "CheckConclusion",
    "CheckStatus",
    "CommentSeverity",
    "ComplianceLabel",
    "PRAnalysisTask",
    "PRBot",
    "PRBotConfig",
    "PRBotResult",
    "PRBotService",
    "get_pr_bot_service",
]


@dataclass
class PRBotService:
    """Facade over PR-bot sub-modules: bot, checks, comments, labels, queue, and policy gates."""

    bot: PRBot = field(default_factory=PRBot)
    checks_service: ChecksService = field(default_factory=ChecksService)
    comment_service: CommentService = field(default_factory=CommentService)
    label_service: LabelService = field(default_factory=LabelService)
    queue: PRAnalysisQueue = field(default_factory=PRAnalysisQueue)
    gate_service: PolicyGateService = field(default_factory=get_policy_gate_service)

    # ------------------------------------------------------------------
    # Core analysis
    # ------------------------------------------------------------------

    async def analyze_pr(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        head_sha: str,
        access_token: str = "",
        changed_files: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Run full compliance analysis on a pull request."""
        result = await self.bot.analyze_pr(
            owner,
            repo,
            pr_number,
            head_sha,
            token=access_token,
            changed_files=changed_files,
        )
        logger.info(
            "pr_analyzed",
            repo=f"{owner}/{repo}",
            pr=pr_number,
        )
        return result

    async def process_task(
        self,
        task: PRAnalysisTask,
        access_token: str,
    ) -> PRBotResult:
        """Process a queued PR analysis task end-to-end."""
        return await self.bot.process_task(task, access_token)

    # ------------------------------------------------------------------
    # Check runs
    # ------------------------------------------------------------------

    async def create_check_run(
        self,
        owner: str,
        repo: str,
        head_sha: str,
        access_token: str | None = None,
    ) -> Any:
        """Create a GitHub check run for the given commit."""
        check = await self.checks_service.create_check_run(
            owner,
            repo,
            head_sha,
            access_token=access_token,
        )
        logger.info("check_run_created", repo=f"{owner}/{repo}", sha=head_sha[:8])
        return check

    async def complete_check_run(
        self,
        owner: str,
        repo: str,
        check_run_id: int,
        conclusion: CheckConclusion,
        output: CheckOutput,
        access_token: str | None = None,
    ) -> Any:
        """Mark a check run as completed with the given conclusion."""
        return await self.checks_service.complete_check_run(
            owner,
            repo,
            check_run_id,
            conclusion,
            output,
            access_token=access_token,
        )

    # ------------------------------------------------------------------
    # Policy gates
    # ------------------------------------------------------------------

    async def enforce_gates(
        self,
        pr_number: int,
        repository: str,
        changed_files: list[dict[str, Any]],
    ) -> PolicyEvaluationSummary:
        """Evaluate all policy gates for a pull request."""
        summary = await self.gate_service.evaluate_pr(
            pr_number,
            repository,
            changed_files,
        )
        logger.info(
            "gates_evaluated",
            repo=repository,
            pr=pr_number,
            can_merge=summary.can_merge,
        )
        return summary

    # ------------------------------------------------------------------
    # Queue helpers
    # ------------------------------------------------------------------

    async def enqueue(self, task: PRAnalysisTask) -> str:
        """Add a PR analysis task to the processing queue."""
        return await self.queue.enqueue(task)

    async def get_queue_size(self) -> int:
        return await self.queue.get_queue_size()


_service: PRBotService | None = None


def get_pr_bot_service() -> PRBotService:
    """Return the global PRBotService singleton."""
    global _service
    if _service is None:
        _service = PRBotService()
        logger.info("pr_bot_service_initialized")
    return _service
