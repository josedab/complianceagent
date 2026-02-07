"""Compliance Co-Pilot for PRs Service."""

import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.pr_copilot.models import (
    ComplianceFinding,
    LearningStats,
    PRReviewResult,
    ReviewSeverity,
    ReviewStatus,
    SuggestionAction,
    SuggestionFeedback,
)

logger = structlog.get_logger()


class PRCopilotService:
    """AI-powered compliance co-pilot for pull request reviews."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._reviews: dict[UUID, PRReviewResult] = {}
        self._feedback: list[SuggestionFeedback] = []

    async def analyze_pr(
        self,
        repo: str,
        pr_number: int,
        diff: str,
        files_changed: list[str] | None = None,
        base_branch: str = "main",
    ) -> PRReviewResult:
        """Perform comprehensive compliance analysis on a PR."""
        start = time.monotonic()

        result = PRReviewResult(
            pr_number=pr_number,
            repo=repo,
            status=ReviewStatus.ANALYZING,
        )

        logger.info("Analyzing PR for compliance", repo=repo, pr=pr_number)

        findings = await self._scan_diff(diff, files_changed or [])
        result.findings = findings
        result.status = ReviewStatus.COMPLETED
        result.analyzed_at = datetime.now(UTC)
        result.analysis_time_ms = (time.monotonic() - start) * 1000

        # Determine risk level and labels
        result.risk_level = self._compute_risk_level(findings)
        result.labels = self._compute_labels(findings)
        result.summary = self._generate_summary(findings, repo, pr_number)

        self._reviews[result.id] = result

        logger.info(
            "PR analysis complete",
            repo=repo,
            pr=pr_number,
            findings=len(findings),
            risk=result.risk_level,
        )
        return result

    async def get_review(self, review_id: UUID) -> PRReviewResult | None:
        """Get a PR review result."""
        return self._reviews.get(review_id)

    async def list_reviews(
        self,
        repo: str | None = None,
        status: ReviewStatus | None = None,
    ) -> list[PRReviewResult]:
        """List PR reviews."""
        results = list(self._reviews.values())
        if repo:
            results = [r for r in results if r.repo == repo]
        if status:
            results = [r for r in results if r.status == status]
        return sorted(results, key=lambda r: r.analyzed_at or datetime.min, reverse=True)

    async def submit_feedback(self, feedback: SuggestionFeedback) -> SuggestionFeedback:
        """Submit feedback on a compliance suggestion."""
        feedback.recorded_at = datetime.now(UTC)
        self._feedback.append(feedback)
        logger.info(
            "Suggestion feedback recorded",
            finding=str(feedback.finding_id),
            action=feedback.action.value,
        )
        return feedback

    async def get_learning_stats(self) -> LearningStats:
        """Get aggregated learning statistics."""
        stats = LearningStats(total_suggestions=len(self._feedback))

        for fb in self._feedback:
            if fb.action == SuggestionAction.ACCEPTED:
                stats.accepted += 1
            elif fb.action == SuggestionAction.DISMISSED:
                stats.dismissed += 1
            elif fb.action == SuggestionAction.DEFERRED:
                stats.deferred += 1

        if stats.total_suggestions > 0:
            stats.acceptance_rate = stats.accepted / stats.total_suggestions

        return stats

    async def get_inline_comments(self, review_id: UUID) -> list[dict]:
        """Generate inline review comments for GitHub/GitLab."""
        review = self._reviews.get(review_id)
        if not review:
            return []

        comments = []
        for finding in review.findings:
            comment = {
                "path": finding.file_path,
                "line": finding.line_start,
                "side": "RIGHT",
                "body": self._format_inline_comment(finding),
            }
            comments.append(comment)

        return comments

    async def _scan_diff(self, diff: str, files_changed: list[str]) -> list[ComplianceFinding]:
        """Scan a diff for compliance issues."""
        findings: list[ComplianceFinding] = []

        if self.copilot:
            try:
                ai_result = await self.copilot.analyze_legal_text(diff)
                for req in ai_result.get("requirements", []):
                    findings.append(
                        ComplianceFinding(
                            file_path=req.get("file", files_changed[0] if files_changed else ""),
                            line_start=req.get("line", 1),
                            severity=ReviewSeverity.MEDIUM,
                            regulation=req.get("regulation", ""),
                            title=req.get("action", "Compliance check"),
                            description=req.get("description", ""),
                            confidence=req.get("confidence", 0.5),
                        )
                    )
            except Exception:
                logger.exception("AI analysis failed during PR scan")
        else:
            # Pattern-based fallback detection
            findings.extend(self._pattern_scan(diff, files_changed))

        return findings

    def _pattern_scan(self, diff: str, files_changed: list[str]) -> list[ComplianceFinding]:
        """Pattern-based compliance scanning fallback."""
        findings = []
        patterns = {
            "personal_data": {
                "keywords": ["email", "phone", "address", "ssn", "date_of_birth"],
                "regulation": "GDPR",
                "article": "Art. 5(1)(c)",
                "title": "Personal data handling detected",
            },
            "logging_pii": {
                "keywords": ["log(", "logger.", "print("],
                "regulation": "GDPR",
                "article": "Art. 5(1)(f)",
                "title": "Potential PII in logs",
            },
            "encryption": {
                "keywords": ["password", "secret", "token", "api_key"],
                "regulation": "PCI-DSS",
                "article": "Req. 3.4",
                "title": "Sensitive data may need encryption",
            },
        }

        diff_lower = diff.lower()
        file_path = files_changed[0] if files_changed else "unknown"

        for _pattern_name, config in patterns.items():
            for keyword in config["keywords"]:
                if keyword in diff_lower:
                    findings.append(
                        ComplianceFinding(
                            file_path=file_path,
                            line_start=1,
                            severity=ReviewSeverity.MEDIUM,
                            regulation=config["regulation"],
                            article_ref=config["article"],
                            title=config["title"],
                            description=f"Detected '{keyword}' pattern in diff",
                            confidence=0.7,
                        )
                    )
                    break  # One finding per pattern category

        return findings

    def _compute_risk_level(self, findings: list[ComplianceFinding]) -> str:
        """Compute overall risk level from findings."""
        if any(f.severity == ReviewSeverity.CRITICAL for f in findings):
            return "critical"
        if any(f.severity == ReviewSeverity.HIGH for f in findings):
            return "high"
        if any(f.severity == ReviewSeverity.MEDIUM for f in findings):
            return "medium"
        if findings:
            return "low"
        return "none"

    def _compute_labels(self, findings: list[ComplianceFinding]) -> list[str]:
        """Compute PR labels based on findings."""
        if not findings:
            return ["compliance-ok"]
        risk = self._compute_risk_level(findings)
        if risk in ("critical", "high"):
            return ["compliance-critical"]
        return ["compliance-warning"]

    def _generate_summary(self, findings: list[ComplianceFinding], repo: str, pr: int) -> str:
        """Generate a human-readable summary."""
        if not findings:
            return f"✅ No compliance issues found in {repo}#{pr}."

        critical = sum(1 for f in findings if f.severity == ReviewSeverity.CRITICAL)
        high = sum(1 for f in findings if f.severity == ReviewSeverity.HIGH)
        medium = sum(1 for f in findings if f.severity == ReviewSeverity.MEDIUM)

        parts = [f"Found {len(findings)} compliance issue(s) in {repo}#{pr}:"]
        if critical:
            parts.append(f"🔴 {critical} critical")
        if high:
            parts.append(f"🟠 {high} high")
        if medium:
            parts.append(f"🟡 {medium} medium")
        return " ".join(parts)

    def _format_inline_comment(self, finding: ComplianceFinding) -> str:
        """Format a finding as an inline review comment."""
        body = f"⚠️ **Compliance: {finding.title}**\n\n"
        body += f"**Regulation:** {finding.regulation}"
        if finding.article_ref:
            body += f" ({finding.article_ref})"
        body += f"\n**Severity:** {finding.severity.value}\n"
        if finding.description:
            body += f"\n{finding.description}\n"
        if finding.suggested_code:
            body += f"\n**Suggested fix:**\n```\n{finding.suggested_code}\n```\n"
        return body
