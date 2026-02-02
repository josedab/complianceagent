"""Comment Service - Generate and post inline PR review comments."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog

from app.services.github.client import GitHubClient

logger = structlog.get_logger()


class CommentSeverity(str, Enum):
    """Severity level for comments."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class InlineComment:
    """An inline PR review comment."""
    id: UUID
    file_path: str
    line: int
    body: str
    severity: CommentSeverity
    regulation: str | None = None
    article_reference: str | None = None
    suggestion: str | None = None
    confidence: float = 0.0
    
    def to_github_comment(self) -> dict[str, Any]:
        """Convert to GitHub review comment format."""
        return {
            "path": self.file_path,
            "line": self.line,
            "body": self.body,
        }


class CommentService:
    """Service for generating and posting PR review comments."""

    SEVERITY_EMOJI = {
        CommentSeverity.CRITICAL: "🔴",
        CommentSeverity.HIGH: "🟠",
        CommentSeverity.MEDIUM: "🟡",
        CommentSeverity.LOW: "🔵",
        CommentSeverity.INFO: "⚪",
    }

    def __init__(self, github_client: GitHubClient | None = None):
        self.github = github_client

    def create_comment_from_violation(
        self,
        violation: dict[str, Any],
    ) -> InlineComment:
        """Create an inline comment from a compliance violation."""
        severity = CommentSeverity(violation.get("severity", "medium"))
        emoji = self.SEVERITY_EMOJI.get(severity, "⚪")
        
        # Build comment body
        body = f"{emoji} **{severity.value.upper()}** - `{violation.get('code', 'COMPLIANCE')}`\n\n"
        body += f"{violation.get('message', 'Compliance issue detected')}\n\n"
        
        if violation.get("regulation"):
            body += f"📋 **Regulation:** {violation.get('regulation')}"
            if violation.get("article_reference"):
                body += f" ({violation.get('article_reference')})"
            body += "\n\n"
        
        if violation.get("suggestion"):
            body += f"💡 **Suggestion:** {violation.get('suggestion')}\n\n"
        
        # Add code suggestion if available
        if violation.get("fix_suggestion"):
            body += "```suggestion\n"
            body += violation.get("fix_suggestion", "")
            body += "\n```\n\n"
        
        if violation.get("evidence"):
            body += f"<details><summary>Evidence</summary>\n\n```\n{violation.get('evidence')[:500]}\n```\n</details>\n\n"
        
        body += f"<sub>Confidence: {violation.get('confidence', 0.85):.0%} | "
        body += f"Category: {violation.get('category', 'general')} | "
        body += f"[Learn more](https://complianceagent.ai/docs/{violation.get('code', 'general').lower()})</sub>"
        
        return InlineComment(
            id=uuid4(),
            file_path=violation.get("file_path", ""),
            line=violation.get("line_start", 1),
            body=body,
            severity=severity,
            regulation=violation.get("regulation"),
            article_reference=violation.get("article_reference"),
            suggestion=violation.get("suggestion"),
            confidence=violation.get("confidence", 0.85),
        )

    def filter_comments_by_severity(
        self,
        comments: list[InlineComment],
        min_severity: CommentSeverity = CommentSeverity.LOW,
    ) -> list[InlineComment]:
        """Filter comments to only include those at or above min severity."""
        severity_order = [
            CommentSeverity.INFO,
            CommentSeverity.LOW,
            CommentSeverity.MEDIUM,
            CommentSeverity.HIGH,
            CommentSeverity.CRITICAL,
        ]
        min_index = severity_order.index(min_severity)
        return [c for c in comments if severity_order.index(c.severity) >= min_index]

    def deduplicate_comments(
        self,
        comments: list[InlineComment],
    ) -> list[InlineComment]:
        """Remove duplicate comments on the same line/file."""
        seen: set[tuple[str, int]] = set()
        unique: list[InlineComment] = []
        
        # Sort by severity (highest first) so we keep the most severe
        severity_order = {
            CommentSeverity.CRITICAL: 4,
            CommentSeverity.HIGH: 3,
            CommentSeverity.MEDIUM: 2,
            CommentSeverity.LOW: 1,
            CommentSeverity.INFO: 0,
        }
        sorted_comments = sorted(
            comments,
            key=lambda c: severity_order.get(c.severity, 0),
            reverse=True,
        )
        
        for comment in sorted_comments:
            key = (comment.file_path, comment.line)
            if key not in seen:
                seen.add(key)
                unique.append(comment)
        
        return unique

    def generate_summary_comment(
        self,
        violations: list[dict[str, Any]],
        files_analyzed: int,
        analysis_time_ms: float,
        regulations_checked: list[str],
        pr_url: str | None = None,
    ) -> str:
        """Generate a summary comment for the PR."""
        critical_count = sum(1 for v in violations if v.get("severity") == "critical")
        high_count = sum(1 for v in violations if v.get("severity") == "high")
        medium_count = sum(1 for v in violations if v.get("severity") == "medium")
        low_count = sum(1 for v in violations if v.get("severity") == "low")
        
        if not violations:
            summary = "## ✅ Compliance Review Passed\n\n"
            summary += f"Analyzed **{files_analyzed}** files • No issues detected\n\n"
        else:
            summary = "## ⚠️ Compliance Review Summary\n\n"
            summary += f"Analyzed **{files_analyzed}** files\n\n"
            summary += "### Issues Found\n"
            summary += f"| Severity | Count |\n"
            summary += f"|----------|-------|\n"
            summary += f"| 🔴 Critical | {critical_count} |\n"
            summary += f"| 🟠 High | {high_count} |\n"
            summary += f"| 🟡 Medium | {medium_count} |\n"
            summary += f"| 🔵 Low | {low_count} |\n\n"
        
        # Group by regulation
        if violations:
            by_regulation: dict[str, int] = {}
            for v in violations:
                reg = v.get("regulation") or "Security"
                by_regulation[reg] = by_regulation.get(reg, 0) + 1
            
            summary += "### By Regulation\n"
            for reg, count in sorted(by_regulation.items(), key=lambda x: -x[1]):
                summary += f"- **{reg}**: {count} issues\n"
            summary += "\n"
        
        summary += f"**Regulations checked:** {', '.join(regulations_checked)}\n\n"
        
        # Add action items
        if critical_count > 0 or high_count > 0:
            summary += "### 🚨 Action Required\n"
            summary += "This PR has **critical or high severity** compliance issues that must be resolved before merging.\n\n"
        
        summary += f"<sub>Analysis completed in {analysis_time_ms:.0f}ms by [ComplianceAgent](https://complianceagent.ai)</sub>"
        
        return summary

    async def post_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        comments: list[InlineComment],
        summary: str,
        recommendation: str,  # approve, request_changes, comment
        access_token: str | None = None,
    ) -> int | None:
        """Post a PR review with inline comments."""
        client = self.github or GitHubClient(access_token=access_token)
        
        async with client:
            # Map recommendation to GitHub event
            event_map = {
                "approve": "APPROVE",
                "request_changes": "REQUEST_CHANGES",
                "comment": "COMMENT",
            }
            event = event_map.get(recommendation, "COMMENT")
            
            # Prepare GitHub API payload
            gh_comments = [c.to_github_comment() for c in comments[:50]]  # GitHub limits to 50
            
            payload = {
                "body": summary,
                "event": event,
                "comments": gh_comments,
            }
            
            response = await client._client.post(
                f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
                json=payload,
            )
            
            if response.status_code in (200, 201):
                data = response.json()
                logger.info(
                    "PR review posted",
                    review_id=data.get("id"),
                    comments_count=len(gh_comments),
                    event=event,
                )
                return data.get("id")
            
            logger.error(
                "Failed to post PR review",
                status_code=response.status_code,
                body=response.text[:500],
            )
            return None

    async def post_single_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        comment: InlineComment,
        commit_id: str,
        access_token: str | None = None,
    ) -> int | None:
        """Post a single review comment."""
        client = self.github or GitHubClient(access_token=access_token)
        
        async with client:
            payload = {
                "body": comment.body,
                "commit_id": commit_id,
                "path": comment.file_path,
                "line": comment.line,
            }
            
            response = await client._client.post(
                f"/repos/{owner}/{repo}/pulls/{pr_number}/comments",
                json=payload,
            )
            
            if response.status_code in (200, 201):
                return response.json().get("id")
            
            logger.error(
                "Failed to post comment",
                status_code=response.status_code,
            )
            return None

    async def update_or_create_summary_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        summary: str,
        access_token: str | None = None,
    ) -> int | None:
        """Update existing bot comment or create new one."""
        client = self.github or GitHubClient(access_token=access_token)
        bot_marker = "<!-- ComplianceAgent Summary -->"
        
        async with client:
            # Find existing comment
            response = await client._client.get(
                f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            )
            
            existing_comment_id = None
            if response.status_code == 200:
                for comment in response.json():
                    if bot_marker in comment.get("body", ""):
                        existing_comment_id = comment["id"]
                        break
            
            comment_body = f"{bot_marker}\n{summary}"
            
            if existing_comment_id:
                # Update existing
                response = await client._client.patch(
                    f"/repos/{owner}/{repo}/issues/comments/{existing_comment_id}",
                    json={"body": comment_body},
                )
            else:
                # Create new
                response = await client._client.post(
                    f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
                    json={"body": comment_body},
                )
            
            if response.status_code in (200, 201):
                return response.json().get("id")
            return None
