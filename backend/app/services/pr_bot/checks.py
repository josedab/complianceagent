"""GitHub Checks API Service - Create and update check runs for merge gates."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import structlog

from app.services.github.client import GitHubClient

logger = structlog.get_logger()


class CheckStatus(str, Enum):
    """Status of a GitHub check run."""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class CheckConclusion(str, Enum):
    """Conclusion of a completed check run."""
    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"
    SKIPPED = "skipped"


@dataclass
class CheckAnnotation:
    """An annotation (inline comment) in a check run."""
    path: str
    start_line: int
    end_line: int
    annotation_level: str  # notice, warning, failure
    message: str
    title: str | None = None
    raw_details: str | None = None
    start_column: int | None = None
    end_column: int | None = None


@dataclass
class CheckOutput:
    """Output summary for a check run."""
    title: str
    summary: str
    text: str | None = None
    annotations: list[CheckAnnotation] = field(default_factory=list)
    images: list[dict[str, str]] = field(default_factory=list)


@dataclass
class CheckRun:
    """A GitHub check run."""
    id: int | None = None
    name: str = "ComplianceAgent"
    head_sha: str = ""
    status: CheckStatus = CheckStatus.QUEUED
    conclusion: CheckConclusion | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    external_id: str | None = None
    details_url: str | None = None
    output: CheckOutput | None = None


class ChecksService:
    """Service for managing GitHub Check runs for compliance gates."""

    CHECK_NAME = "ComplianceAgent"
    
    def __init__(self, github_client: GitHubClient | None = None):
        self.github = github_client

    async def create_check_run(
        self,
        owner: str,
        repo: str,
        head_sha: str,
        access_token: str | None = None,
        external_id: str | None = None,
    ) -> CheckRun:
        """Create a new check run in 'queued' status."""
        client = self.github or GitHubClient(access_token=access_token)
        
        async with client:
            payload = {
                "name": self.CHECK_NAME,
                "head_sha": head_sha,
                "status": CheckStatus.QUEUED.value,
                "external_id": external_id,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
            
            response = await client._client.post(
                f"/repos/{owner}/{repo}/check-runs",
                json=payload,
            )
            
            if response.status_code not in (200, 201):
                logger.error(
                    "Failed to create check run",
                    status_code=response.status_code,
                    body=response.text[:500],
                )
                raise Exception(f"Failed to create check run: {response.status_code}")
            
            data = response.json()
            logger.info(
                "Check run created",
                check_id=data["id"],
                repo=f"{owner}/{repo}",
                head_sha=head_sha[:8],
            )
            
            return CheckRun(
                id=data["id"],
                name=data["name"],
                head_sha=head_sha,
                status=CheckStatus.QUEUED,
                started_at=datetime.now(timezone.utc),
                external_id=external_id,
            )

    async def update_check_run(
        self,
        owner: str,
        repo: str,
        check_run_id: int,
        status: CheckStatus | None = None,
        conclusion: CheckConclusion | None = None,
        output: CheckOutput | None = None,
        access_token: str | None = None,
        details_url: str | None = None,
    ) -> CheckRun:
        """Update an existing check run."""
        client = self.github or GitHubClient(access_token=access_token)
        
        async with client:
            payload: dict[str, Any] = {}
            
            if status:
                payload["status"] = status.value
            
            if conclusion:
                payload["conclusion"] = conclusion.value
                payload["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            if details_url:
                payload["details_url"] = details_url
            
            if output:
                payload["output"] = {
                    "title": output.title,
                    "summary": output.summary,
                }
                if output.text:
                    payload["output"]["text"] = output.text
                if output.annotations:
                    # GitHub limits to 50 annotations per request
                    payload["output"]["annotations"] = [
                        {
                            "path": a.path,
                            "start_line": a.start_line,
                            "end_line": a.end_line,
                            "annotation_level": a.annotation_level,
                            "message": a.message,
                            "title": a.title,
                            **({"raw_details": a.raw_details} if a.raw_details else {}),
                        }
                        for a in output.annotations[:50]
                    ]
            
            response = await client._client.patch(
                f"/repos/{owner}/{repo}/check-runs/{check_run_id}",
                json=payload,
            )
            
            if response.status_code != 200:
                logger.error(
                    "Failed to update check run",
                    check_id=check_run_id,
                    status_code=response.status_code,
                )
                raise Exception(f"Failed to update check run: {response.status_code}")
            
            data = response.json()
            logger.info(
                "Check run updated",
                check_id=check_run_id,
                status=status.value if status else None,
                conclusion=conclusion.value if conclusion else None,
            )
            
            return CheckRun(
                id=data["id"],
                name=data["name"],
                head_sha=data["head_sha"],
                status=CheckStatus(data["status"]),
                conclusion=CheckConclusion(data["conclusion"]) if data.get("conclusion") else None,
            )

    async def start_check_run(
        self,
        owner: str,
        repo: str,
        check_run_id: int,
        access_token: str | None = None,
    ) -> CheckRun:
        """Mark a check run as in progress."""
        return await self.update_check_run(
            owner=owner,
            repo=repo,
            check_run_id=check_run_id,
            status=CheckStatus.IN_PROGRESS,
            access_token=access_token,
        )

    async def complete_check_run(
        self,
        owner: str,
        repo: str,
        check_run_id: int,
        conclusion: CheckConclusion,
        output: CheckOutput,
        access_token: str | None = None,
        details_url: str | None = None,
    ) -> CheckRun:
        """Complete a check run with results."""
        return await self.update_check_run(
            owner=owner,
            repo=repo,
            check_run_id=check_run_id,
            status=CheckStatus.COMPLETED,
            conclusion=conclusion,
            output=output,
            access_token=access_token,
            details_url=details_url,
        )

    def build_output_from_analysis(
        self,
        violations: list[dict],
        files_analyzed: int,
        analysis_time_ms: float,
        regulations_checked: list[str],
    ) -> tuple[CheckConclusion, CheckOutput]:
        """Build check output from analysis results."""
        critical_count = sum(1 for v in violations if v.get("severity") == "critical")
        high_count = sum(1 for v in violations if v.get("severity") == "high")
        medium_count = sum(1 for v in violations if v.get("severity") == "medium")
        low_count = sum(1 for v in violations if v.get("severity") == "low")
        
        # Determine conclusion based on violation severity
        if critical_count > 0:
            conclusion = CheckConclusion.FAILURE
        elif high_count > 0:
            conclusion = CheckConclusion.FAILURE
        elif medium_count > 2:
            conclusion = CheckConclusion.ACTION_REQUIRED
        elif violations:
            conclusion = CheckConclusion.NEUTRAL
        else:
            conclusion = CheckConclusion.SUCCESS
        
        # Build title
        if not violations:
            title = "✅ Compliance check passed"
        else:
            title = f"⚠️ {len(violations)} compliance issues found"
        
        # Build summary
        summary = f"## Compliance Review Summary\n\n"
        summary += f"Analyzed **{files_analyzed}** files in {analysis_time_ms:.0f}ms\n\n"
        summary += f"**Regulations checked:** {', '.join(regulations_checked)}\n\n"
        
        if violations:
            summary += "### Issues Found\n"
            summary += f"- 🔴 Critical: **{critical_count}**\n"
            summary += f"- 🟠 High: **{high_count}**\n"
            summary += f"- 🟡 Medium: **{medium_count}**\n"
            summary += f"- 🔵 Low: **{low_count}**\n"
        else:
            summary += "✅ No compliance issues detected!"
        
        # Build annotations
        annotations = []
        for v in violations:
            level_map = {
                "critical": "failure",
                "high": "failure", 
                "medium": "warning",
                "low": "notice",
                "info": "notice",
            }
            annotations.append(CheckAnnotation(
                path=v.get("file_path", ""),
                start_line=v.get("line_start", 1),
                end_line=v.get("line_end", v.get("line_start", 1)),
                annotation_level=level_map.get(v.get("severity", "medium"), "warning"),
                message=v.get("message", "Compliance issue detected"),
                title=f"[{v.get('code', 'COMPLIANCE')}] {v.get('regulation', 'Security')}",
            ))
        
        output = CheckOutput(
            title=title,
            summary=summary,
            annotations=annotations,
        )
        
        return conclusion, output

    async def request_check_rerun(
        self,
        owner: str,
        repo: str,
        check_run_id: int,
        access_token: str | None = None,
    ) -> bool:
        """Request a re-run of a check (used after fixes are applied)."""
        client = self.github or GitHubClient(access_token=access_token)
        
        async with client:
            response = await client._client.post(
                f"/repos/{owner}/{repo}/check-runs/{check_run_id}/rerequest",
            )
            return response.status_code == 201
