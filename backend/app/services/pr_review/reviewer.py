"""PR Reviewer - Phase 2: AI-powered compliance review with inline suggestions."""

import time
from typing import Any
from uuid import uuid4

import structlog

from app.agents.copilot import CopilotClient, CopilotMessage
from app.services.pr_review.analyzer import PRAnalyzer
from app.services.pr_review.models import (
    ComplianceViolation,
    FileDiff,
    PRAnalysisResult,
    PRReviewResult,
    ReviewComment,
    ReviewStatus,
    ViolationSeverity,
)


logger = structlog.get_logger()


class PRReviewer:
    """AI-powered PR compliance reviewer that generates inline suggestions."""

    def __init__(
        self,
        copilot_client: CopilotClient | None = None,
        analyzer: PRAnalyzer | None = None,
        enabled_regulations: list[str] | None = None,
    ):
        self.copilot_client = copilot_client
        self.analyzer = analyzer or PRAnalyzer(enabled_regulations=enabled_regulations)
        self.enabled_regulations = enabled_regulations or [
            "GDPR", "CCPA", "HIPAA", "PCI-DSS", "EU AI Act", "SOX"
        ]

    async def review_pr(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        access_token: str | None = None,
        deep_analysis: bool = True,
    ) -> PRReviewResult:
        """Perform a complete compliance review of a PR.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            access_token: GitHub access token
            deep_analysis: Whether to use AI for deep analysis (slower but more accurate)
            
        Returns:
            PRReviewResult with all findings, comments, and recommendations
        """
        start_time = time.perf_counter()
        
        # Phase 1: Pattern-based analysis
        analysis = await self.analyzer.analyze_pr(owner, repo, pr_number, access_token)
        
        # Phase 2: AI-enhanced analysis if enabled
        if deep_analysis and self.copilot_client and analysis.violations:
            analysis = await self._enhance_with_ai(analysis)
        
        # Generate review comments
        comments = self._generate_review_comments(analysis)
        
        # Generate summary and recommendation
        summary = self._generate_summary(analysis)
        recommendation = self._determine_recommendation(analysis)
        
        review_time = (time.perf_counter() - start_time) * 1000
        
        return PRReviewResult(
            id=uuid4(),
            analysis=analysis,
            comments=comments,
            auto_fixes=[],  # Populated by AutoFixGenerator
            status=ReviewStatus.COMPLETED,
            summary=summary,
            recommendation=recommendation,
            review_time_ms=review_time,
        )

    async def review_files(
        self,
        files: list[dict[str, Any]],
        deep_analysis: bool = True,
    ) -> PRReviewResult:
        """Review a list of files directly (for webhook-based review).
        
        Args:
            files: List of file dicts with 'path', 'content', 'patch'
            deep_analysis: Whether to use AI for deep analysis
            
        Returns:
            PRReviewResult with findings
        """
        start_time = time.perf_counter()
        
        all_violations: list[ComplianceViolation] = []
        file_diffs: list[FileDiff] = []
        
        for file_data in files:
            path = file_data.get("path", "unknown")
            patch = file_data.get("patch", "")
            
            file_diff = FileDiff(
                path=path,
                old_path=None,
                status="modified",
                additions=patch.count("\n+"),
                deletions=patch.count("\n-"),
                patch=patch,
            )
            file_diffs.append(file_diff)
            
            violations = await self.analyzer.analyze_diff_content(patch, path)
            all_violations.extend(violations)
        
        analysis = PRAnalysisResult(
            files_analyzed=len(files),
            violations=all_violations,
            files=file_diffs,
            regulations_checked=self.enabled_regulations,
        )
        
        if deep_analysis and self.copilot_client and all_violations:
            analysis = await self._enhance_with_ai(analysis)
        
        comments = self._generate_review_comments(analysis)
        summary = self._generate_summary(analysis)
        recommendation = self._determine_recommendation(analysis)
        
        review_time = (time.perf_counter() - start_time) * 1000
        
        return PRReviewResult(
            analysis=analysis,
            comments=comments,
            status=ReviewStatus.COMPLETED,
            summary=summary,
            recommendation=recommendation,
            review_time_ms=review_time,
        )

    async def _enhance_with_ai(self, analysis: PRAnalysisResult) -> PRAnalysisResult:
        """Enhance violation analysis using AI for better context and suggestions."""
        if not self.copilot_client:
            return analysis
        
        enhanced_violations = []
        
        # Group violations by file for context
        violations_by_file: dict[str, list[ComplianceViolation]] = {}
        for v in analysis.violations:
            violations_by_file.setdefault(v.file_path, []).append(v)
        
        async with self.copilot_client:
            for file_path, file_violations in violations_by_file.items():
                # Get file content from diff
                file_diff = next((f for f in analysis.files if f.path == file_path), None)
                if not file_diff:
                    enhanced_violations.extend(file_violations)
                    continue
                
                # Prepare context for AI
                violations_text = "\n".join(
                    f"- Line {v.line_start}: [{v.code}] {v.message}"
                    for v in file_violations
                )
                
                try:
                    enhanced = await self._ai_analyze_violations(
                        file_path=file_path,
                        file_content=file_diff.patch,
                        violations=violations_text,
                        regulations=self.enabled_regulations,
                    )
                    
                    # Update violations with AI insights
                    for v in file_violations:
                        ai_info = enhanced.get(str(v.line_start), {})
                        if ai_info:
                            v.suggestion = ai_info.get("suggestion", v.suggestion)
                            v.confidence = min(v.confidence + 0.1, 1.0)  # Boost confidence
                            v.metadata["ai_analysis"] = ai_info.get("analysis", "")
                        enhanced_violations.append(v)
                        
                except Exception as e:
                    logger.warning(f"AI enhancement failed: {e}")
                    enhanced_violations.extend(file_violations)
        
        analysis.violations = enhanced_violations
        return analysis

    async def _ai_analyze_violations(
        self,
        file_path: str,
        file_content: str,
        violations: str,
        regulations: list[str],
    ) -> dict[str, Any]:
        """Use AI to analyze violations and provide suggestions."""
        system_prompt = """You are an expert compliance code reviewer. 
Analyze the code violations and provide:
1. Whether each violation is a true positive or false positive
2. Specific fix suggestions with code examples
3. Regulatory context and citations

Return JSON with line numbers as keys:
{
  "42": {
    "is_valid": true,
    "confidence": 0.95,
    "analysis": "This code stores email without consent check...",
    "suggestion": "Add consent verification before storing: if user.has_consent('email_storage'): ...",
    "regulation_details": "GDPR Article 7 requires explicit consent..."
  }
}"""

        user_prompt = f"""Analyze these compliance violations in {file_path}:

**Code (diff format):**
```
{file_content[:3000]}
```

**Detected Violations:**
{violations}

**Regulations to check:** {', '.join(regulations)}

Return JSON only."""

        response = await self.copilot_client.chat(
            messages=[CopilotMessage(role="user", content=user_prompt)],
            system_message=system_prompt,
            temperature=0.3,
            max_tokens=2048,
        )
        
        try:
            return self.copilot_client._parse_json_response(response.content, "violation analysis")
        except Exception:
            return {}

    def _generate_review_comments(self, analysis: PRAnalysisResult) -> list[ReviewComment]:
        """Generate GitHub review comments from violations."""
        comments: list[ReviewComment] = []
        
        for violation in analysis.violations:
            # Format the comment body with compliance details
            body = self._format_comment_body(violation)
            
            comment = ReviewComment(
                violation=violation,
                file_path=violation.file_path,
                line=violation.line_start,
                body=body,
            )
            comments.append(comment)
        
        return comments

    def _format_comment_body(self, violation: ComplianceViolation) -> str:
        """Format a violation into a GitHub comment."""
        severity_emoji = {
            ViolationSeverity.CRITICAL: "🔴",
            ViolationSeverity.HIGH: "🟠",
            ViolationSeverity.MEDIUM: "🟡",
            ViolationSeverity.LOW: "🔵",
            ViolationSeverity.INFO: "⚪",
        }
        
        emoji = severity_emoji.get(violation.severity, "⚪")
        
        body = f"{emoji} **{violation.severity.value.upper()} - {violation.code}**\n\n"
        body += f"{violation.message}\n\n"
        
        if violation.regulation:
            body += f"📋 **Regulation:** {violation.regulation}"
            if violation.article_reference:
                body += f" ({violation.article_reference})"
            body += "\n\n"
        
        if violation.suggestion:
            body += f"💡 **Suggestion:** {violation.suggestion}\n\n"
        
        if violation.evidence:
            body += f"```\n{violation.evidence[:200]}\n```\n\n"
        
        body += f"<sub>Confidence: {violation.confidence:.0%} | Category: {violation.category or 'general'}</sub>"
        
        return body

    def _generate_summary(self, analysis: PRAnalysisResult) -> str:
        """Generate a summary of the compliance review."""
        if not analysis.violations:
            return "✅ No compliance issues detected in this PR."
        
        summary = "## Compliance Review Summary\n\n"
        summary += f"Analyzed **{analysis.files_analyzed}** files with **{analysis.total_additions}** additions.\n\n"
        
        # Violation counts
        summary += "### Issues Found\n"
        summary += f"- 🔴 Critical: **{analysis.critical_count}**\n"
        summary += f"- 🟠 High: **{analysis.high_count}**\n"
        summary += f"- 🟡 Medium: **{analysis.medium_count}**\n"
        summary += f"- 🔵 Low: **{analysis.low_count}**\n\n"
        
        # Group by regulation
        by_regulation: dict[str, int] = {}
        for v in analysis.violations:
            reg = v.regulation or "Security"
            by_regulation[reg] = by_regulation.get(reg, 0) + 1
        
        summary += "### By Regulation\n"
        for reg, count in sorted(by_regulation.items(), key=lambda x: -x[1]):
            summary += f"- {reg}: {count}\n"
        
        summary += f"\n<sub>Analysis completed in {analysis.analysis_time_ms:.0f}ms</sub>"
        
        return summary

    def _determine_recommendation(self, analysis: PRAnalysisResult) -> str:
        """Determine the review recommendation (approve, request_changes, comment)."""
        if analysis.critical_count > 0:
            return "request_changes"
        if analysis.high_count > 0:
            return "request_changes"
        if analysis.medium_count > 2:
            return "comment"
        if analysis.violations:
            return "comment"
        return "approve"

    async def post_review_to_github(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        review: PRReviewResult,
        access_token: str,
    ) -> int | None:
        """Post the review to GitHub as PR review comments.
        
        Returns the GitHub review ID if successful.
        """
        from app.services.github.client import GitHubClient
        
        async with GitHubClient(access_token=access_token) as client:
            # Prepare review comments for GitHub API
            gh_comments = []
            for comment in review.comments:
                gh_comments.append({
                    "path": comment.file_path,
                    "line": comment.line,
                    "body": comment.body,
                })
            
            # Map recommendation to GitHub event
            event_map = {
                "approve": "APPROVE",
                "request_changes": "REQUEST_CHANGES",
                "comment": "COMMENT",
            }
            event = event_map.get(review.recommendation, "COMMENT")
            
            # Create the review
            response = await client._client.post(
                f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
                json={
                    "body": review.summary,
                    "event": event,
                    "comments": gh_comments[:50],  # GitHub limits to 50 comments
                },
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("id")
            
            logger.error(f"Failed to post review: {response.status_code} - {response.text}")
            return None
