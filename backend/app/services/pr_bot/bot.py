"""PR Bot - Main orchestrator for automated compliance PR review."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog

from app.agents.copilot import CopilotClient
from app.services.github.client import GitHubClient
from app.services.pr_bot.checks import CheckConclusion, CheckOutput, ChecksService
from app.services.pr_bot.comments import CommentService, CommentSeverity
from app.services.pr_bot.labels import LabelService
from app.services.pr_bot.queue import PRAnalysisTask, PRTaskStatus
from app.services.pr_review.analyzer import PRAnalyzer
from app.services.pr_review.autofix import AutoFixGenerator
from app.services.pr_review.reviewer import PRReviewer

logger = structlog.get_logger()


@dataclass
class PRBotConfig:
    """Configuration for PR Bot behavior."""
    # Analysis settings
    enabled_regulations: list[str] = field(default_factory=lambda: [
        "GDPR", "CCPA", "HIPAA", "PCI-DSS", "EU AI Act", "SOX"
    ])
    deep_analysis: bool = True
    
    # GitHub integration settings
    post_review_comments: bool = True
    post_inline_comments: bool = True
    create_check_run: bool = True
    auto_label: bool = True
    
    # Filtering settings
    min_comment_severity: CommentSeverity = CommentSeverity.LOW
    max_comments_per_pr: int = 50
    
    # Merge gate settings
    block_on_critical: bool = True
    block_on_high: bool = True
    block_on_medium: bool = False
    require_all_comments_resolved: bool = False
    
    # Auto-fix settings
    generate_auto_fixes: bool = True
    auto_suggest_fixes: bool = True
    
    # Notification settings
    notify_on_failure: bool = True
    mention_codeowners: bool = False


@dataclass
class PRBotResult:
    """Result of a PR Bot analysis run."""
    task_id: str
    owner: str
    repo: str
    pr_number: int
    head_sha: str
    
    # Analysis results
    files_analyzed: int = 0
    total_violations: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    
    # What was done
    check_run_id: int | None = None
    review_id: int | None = None
    labels_applied: list[str] = field(default_factory=list)
    comments_posted: int = 0
    auto_fixes_available: int = 0
    
    # Outcome
    passed: bool = True
    should_block_merge: bool = False
    recommendation: str = "approve"  # approve, request_changes, comment
    
    # Timing
    analysis_time_ms: float = 0.0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    
    # Errors
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "owner": self.owner,
            "repo": self.repo,
            "pr_number": self.pr_number,
            "head_sha": self.head_sha,
            "files_analyzed": self.files_analyzed,
            "total_violations": self.total_violations,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "check_run_id": self.check_run_id,
            "review_id": self.review_id,
            "labels_applied": self.labels_applied,
            "comments_posted": self.comments_posted,
            "auto_fixes_available": self.auto_fixes_available,
            "passed": self.passed,
            "should_block_merge": self.should_block_merge,
            "recommendation": self.recommendation,
            "analysis_time_ms": self.analysis_time_ms,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }


class PRBot:
    """Automated PR compliance review bot."""

    def __init__(
        self,
        config: PRBotConfig | None = None,
        copilot_client: CopilotClient | None = None,
        github_client: GitHubClient | None = None,
    ):
        self.config = config or PRBotConfig()
        self.copilot = copilot_client
        self.github = github_client
        
        # Initialize services
        self.checks_service = ChecksService(github_client)
        self.comment_service = CommentService(github_client)
        self.label_service = LabelService(github_client)
        self.analyzer = PRAnalyzer(enabled_regulations=self.config.enabled_regulations)
        self.reviewer = PRReviewer(
            copilot_client=copilot_client,
            analyzer=self.analyzer,
            enabled_regulations=self.config.enabled_regulations,
        )

    async def process_task(
        self,
        task: PRAnalysisTask,
        access_token: str,
    ) -> PRBotResult:
        """Process a PR analysis task through the full pipeline."""
        import time
        start_time = time.perf_counter()
        
        result = PRBotResult(
            task_id=str(task.id),
            owner=task.owner,
            repo=task.repo,
            pr_number=task.pr_number,
            head_sha=task.head_sha,
        )
        
        try:
            logger.info(
                "PR Bot processing task",
                task_id=str(task.id),
                repo=f"{task.owner}/{task.repo}",
                pr_number=task.pr_number,
            )
            
            # Step 1: Create check run (marks PR as "pending")
            check_run = None
            if self.config.create_check_run and task.create_check_run:
                check_run = await self.checks_service.create_check_run(
                    owner=task.owner,
                    repo=task.repo,
                    head_sha=task.head_sha,
                    access_token=access_token,
                    external_id=str(task.id),
                )
                result.check_run_id = check_run.id
                
                # Mark as in progress
                await self.checks_service.start_check_run(
                    owner=task.owner,
                    repo=task.repo,
                    check_run_id=check_run.id,
                    access_token=access_token,
                )
            
            # Step 2: Add in-progress label
            if self.config.auto_label and task.auto_label:
                await self.label_service.add_in_progress_label(
                    owner=task.owner,
                    repo=task.repo,
                    pr_number=task.pr_number,
                    access_token=access_token,
                )
            
            # Step 3: Run compliance analysis
            review_result = await self.reviewer.review_pr(
                owner=task.owner,
                repo=task.repo,
                pr_number=task.pr_number,
                access_token=access_token,
                deep_analysis=self.config.deep_analysis and task.deep_analysis,
            )
            
            analysis = review_result.analysis
            violations = [
                {
                    "file_path": v.file_path,
                    "line_start": v.line_start,
                    "line_end": v.line_end,
                    "code": v.code,
                    "message": v.message,
                    "severity": v.severity.value,
                    "regulation": v.regulation,
                    "article_reference": v.article_reference,
                    "category": v.category,
                    "suggestion": v.suggestion,
                    "confidence": v.confidence,
                    "evidence": v.evidence,
                }
                for v in analysis.violations
            ] if analysis else []
            
            # Populate result
            result.files_analyzed = analysis.files_analyzed if analysis else 0
            result.total_violations = len(violations)
            result.critical_count = sum(1 for v in violations if v["severity"] == "critical")
            result.high_count = sum(1 for v in violations if v["severity"] == "high")
            result.medium_count = sum(1 for v in violations if v["severity"] == "medium")
            result.low_count = sum(1 for v in violations if v["severity"] == "low")
            
            # Determine if merge should be blocked
            should_block = False
            if self.config.block_on_critical and result.critical_count > 0:
                should_block = True
            if self.config.block_on_high and result.high_count > 0:
                should_block = True
            if self.config.block_on_medium and result.medium_count > 2:
                should_block = True
            
            result.should_block_merge = should_block
            result.passed = not should_block
            result.recommendation = review_result.recommendation
            
            # Step 4: Generate auto-fixes if configured
            auto_fixes = []
            if self.config.generate_auto_fixes and violations:
                if self.copilot:
                    generator = AutoFixGenerator(copilot_client=self.copilot)
                    auto_fixes = review_result.auto_fixes
                    result.auto_fixes_available = len(auto_fixes)
            
            # Step 5: Post review comments
            if self.config.post_review_comments and task.post_comments:
                # Generate inline comments
                comments = [
                    self.comment_service.create_comment_from_violation(v)
                    for v in violations
                ]
                
                # Filter by severity
                comments = self.comment_service.filter_comments_by_severity(
                    comments, self.config.min_comment_severity
                )
                
                # Deduplicate
                comments = self.comment_service.deduplicate_comments(comments)
                
                # Limit count
                comments = comments[:self.config.max_comments_per_pr]
                
                # Generate summary
                summary = self.comment_service.generate_summary_comment(
                    violations=violations,
                    files_analyzed=result.files_analyzed,
                    analysis_time_ms=review_result.review_time_ms,
                    regulations_checked=self.config.enabled_regulations,
                )
                
                # Post review
                if self.config.post_inline_comments:
                    review_id = await self.comment_service.post_review(
                        owner=task.owner,
                        repo=task.repo,
                        pr_number=task.pr_number,
                        comments=comments,
                        summary=summary,
                        recommendation=result.recommendation,
                        access_token=access_token,
                    )
                    result.review_id = review_id
                    result.comments_posted = len(comments)
                else:
                    # Just post summary comment
                    await self.comment_service.update_or_create_summary_comment(
                        owner=task.owner,
                        repo=task.repo,
                        issue_number=task.pr_number,
                        summary=summary,
                        access_token=access_token,
                    )
            
            # Step 6: Apply labels
            if self.config.auto_label and task.auto_label:
                labels = self.label_service.determine_labels(
                    violations=violations,
                    has_auto_fixes=result.auto_fixes_available > 0,
                )
                await self.label_service.apply_labels(
                    owner=task.owner,
                    repo=task.repo,
                    pr_number=task.pr_number,
                    labels=labels,
                    access_token=access_token,
                )
                result.labels_applied = labels
            
            # Step 7: Complete check run
            if check_run and result.check_run_id:
                conclusion, output = self.checks_service.build_output_from_analysis(
                    violations=violations,
                    files_analyzed=result.files_analyzed,
                    analysis_time_ms=review_result.review_time_ms,
                    regulations_checked=self.config.enabled_regulations,
                )
                
                # Override conclusion based on config
                if should_block:
                    conclusion = CheckConclusion.FAILURE
                elif violations:
                    conclusion = CheckConclusion.NEUTRAL
                else:
                    conclusion = CheckConclusion.SUCCESS
                
                await self.checks_service.complete_check_run(
                    owner=task.owner,
                    repo=task.repo,
                    check_run_id=result.check_run_id,
                    conclusion=conclusion,
                    output=output,
                    access_token=access_token,
                )
            
            # Calculate timing
            result.analysis_time_ms = (time.perf_counter() - start_time) * 1000
            result.completed_at = datetime.now(timezone.utc)
            
            logger.info(
                "PR Bot completed",
                task_id=str(task.id),
                violations=result.total_violations,
                passed=result.passed,
                time_ms=result.analysis_time_ms,
            )
            
        except Exception as e:
            result.error = str(e)
            result.completed_at = datetime.now(timezone.utc)
            result.analysis_time_ms = (time.perf_counter() - start_time) * 1000
            
            logger.exception(
                "PR Bot failed",
                task_id=str(task.id),
                error=str(e),
            )
            
            # Try to update check run as failed
            if result.check_run_id:
                try:
                    await self.checks_service.complete_check_run(
                        owner=task.owner,
                        repo=task.repo,
                        check_run_id=result.check_run_id,
                        conclusion=CheckConclusion.FAILURE,
                        output=CheckOutput(
                            title="❌ Compliance check failed",
                            summary=f"Analysis failed: {str(e)[:200]}",
                        ),
                        access_token=access_token,
                    )
                except Exception:
                    pass
            
            raise
        
        return result

    async def handle_pr_event(
        self,
        event_data: dict[str, Any],
        access_token: str,
        organization_id: UUID | None = None,
    ) -> PRAnalysisTask:
        """Handle a GitHub PR webhook event and create analysis task."""
        action = event_data.get("action")
        pr = event_data.get("pull_request", {})
        repo = event_data.get("repository", {})
        
        # Only process certain actions
        if action not in ("opened", "synchronize", "reopened"):
            raise ValueError(f"PR event action '{action}' not handled")
        
        owner, repo_name = repo.get("full_name", "/").split("/")
        
        task = PRAnalysisTask(
            owner=owner,
            repo=repo_name,
            pr_number=pr.get("number"),
            head_sha=pr.get("head", {}).get("sha", ""),
            base_sha=pr.get("base", {}).get("sha", ""),
            organization_id=organization_id,
            enabled_regulations=self.config.enabled_regulations,
            deep_analysis=self.config.deep_analysis,
            post_comments=self.config.post_review_comments,
            create_check_run=self.config.create_check_run,
            auto_label=self.config.auto_label,
        )
        
        logger.info(
            "Created PR analysis task from webhook",
            task_id=str(task.id),
            action=action,
            repo=f"{owner}/{repo_name}",
            pr_number=task.pr_number,
        )
        
        return task

    async def create_fix_pr(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        fixes: list[dict[str, Any]],
        access_token: str,
    ) -> dict[str, Any]:
        """Create a PR with compliance fixes from the bot analysis."""
        if not fixes:
            return {"error": "No fixes to apply"}
        
        client = self.github or GitHubClient(access_token=access_token)
        
        async with client:
            # Get PR info to find base branch
            pr = await client.get_pull_request(owner, repo, pr_number)
            
            # Get base SHA
            base_sha = await client.get_default_branch_sha(owner, repo)
            
            # Create branch
            branch_name = f"compliance-fix/{pr_number}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            await client.create_branch(owner, repo, branch_name, base_sha)
            
            # Apply fixes
            for fix in fixes:
                await client.create_or_update_file(
                    owner=owner,
                    repo=repo,
                    path=fix["file_path"],
                    content=fix["fixed_code"],
                    message=f"fix: {fix.get('description', 'Compliance fix')}",
                    branch=branch_name,
                    sha=fix.get("original_sha"),
                )
            
            # Create PR
            fix_descriptions = "\n".join(
                f"- {f.get('description', 'Fix')}" for f in fixes
            )
            
            created_pr = await client.create_pull_request(
                owner=owner,
                repo=repo,
                title=f"🔧 Compliance fixes for PR #{pr_number}",
                body=f"""## Automated Compliance Fixes

This PR contains automated fixes for compliance issues detected in #{pr_number}.

### Changes
{fix_descriptions}

### Review Checklist
- [ ] Verify fixes are correct
- [ ] Run tests
- [ ] Merge into #{pr_number} branch

---
<sub>Generated by [ComplianceAgent](https://complianceagent.ai)</sub>
""",
                head=branch_name,
                base=pr.head_branch,
                draft=True,
            )
            
            # Add labels
            await client.add_labels_to_pr(
                owner, repo, created_pr.number,
                ["compliance:auto-fix", "bot"]
            )
            
            logger.info(
                "Created fix PR",
                source_pr=pr_number,
                fix_pr=created_pr.number,
                fixes_count=len(fixes),
            )
            
            return {
                "pr_number": created_pr.number,
                "pr_url": created_pr.html_url,
                "branch": branch_name,
                "fixes_applied": len(fixes),
            }
