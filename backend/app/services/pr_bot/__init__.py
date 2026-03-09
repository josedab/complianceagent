"""PR Bot Service - Automated compliance PR review and generation."""

from dataclasses import dataclass, field
from typing import Any

from app.services.pr_bot.checks import CheckConclusion, ChecksService
from app.services.pr_bot.comments import CommentGenerator
from app.services.pr_bot.labels import ComplianceLabel, LabelService
from app.services.pr_bot.queue import PRAnalysisQueue, PRAnalysisTask, TaskStatus


@dataclass
class PRBotConfig:
    """Configuration for PR Bot."""

    enabled: bool = True
    auto_comment: bool = True
    auto_label: bool = True
    create_check_run: bool = True
    block_on_critical: bool = True
    min_severity: str = "medium"
    frameworks: list[str] = field(
        default_factory=lambda: ["GDPR", "CCPA", "HIPAA", "PCI-DSS", "SOX"]
    )


@dataclass
class PRBotResult:
    """Result of PR compliance analysis."""

    pr_number: int = 0
    owner: str = ""
    repo: str = ""
    violations_found: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    violations: list[dict[str, Any]] = field(default_factory=list)

    @property
    def total_violations(self) -> int:
        return self.violations_found

    @property
    def has_blocking_issues(self) -> bool:
        return self.critical_count > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pr_number": self.pr_number,
            "owner": self.owner,
            "repo": self.repo,
            "violations_found": self.violations_found,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
        }


class PRBot:
    """PR compliance bot."""

    def __init__(self, config: PRBotConfig | None = None) -> None:
        self.config = config or PRBotConfig()
        self._github_client: Any = None
        self._analyzer: Any = None

    def _get_github_client(self, access_token: str = "") -> Any:
        return self._github_client

    def _get_analyzer(self) -> Any:
        return self._analyzer

    async def analyze_pr(
        self,
        owner: str = "",
        repo: str = "",
        pr_number: int = 0,
        access_token: str = "",
    ) -> "PRBotResult":
        client = self._get_github_client(access_token)
        analyzer = self._get_analyzer()
        await client.get_pull_request(owner, repo, pr_number)
        files = await client.get_pull_request_files(owner, repo, pr_number)

        all_violations: list[dict[str, Any]] = []
        for f in files:
            violations = await analyzer.analyze_diff(f)
            all_violations.extend(violations)

        critical = sum(1 for v in all_violations if v.get("severity") == "critical")
        high = sum(1 for v in all_violations if v.get("severity") == "high")
        medium = sum(1 for v in all_violations if v.get("severity") == "medium")
        low = sum(1 for v in all_violations if v.get("severity") == "low")

        return PRBotResult(
            pr_number=pr_number,
            owner=owner,
            repo=repo,
            violations_found=len(all_violations),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            violations=all_violations,
        )

    async def process_task(self, task: PRAnalysisTask) -> "PRBotResult":
        return await self.analyze_pr(
            owner=task.owner,
            repo=task.repo,
            pr_number=task.pr_number,
            access_token=task.access_token,
        )

    async def _create_check_run(
        self,
        owner: str = "",
        repo: str = "",
        head_sha: str = "",
        result: "PRBotResult | None" = None,
        access_token: str = "",
    ) -> Any:
        client = self._get_github_client(access_token)
        check = await client.create_check_run(
            owner=owner,
            repo=repo,
            name="ComplianceAgent",
            head_sha=head_sha,
        )
        return check.get("id") if isinstance(check, dict) else check


__all__ = [
    "CheckConclusion",
    "ChecksService",
    "CommentGenerator",
    "ComplianceLabel",
    "LabelService",
    "PRAnalysisQueue",
    "PRAnalysisTask",
    "PRBot",
    "PRBotConfig",
    "PRBotResult",
    "TaskStatus",
]
