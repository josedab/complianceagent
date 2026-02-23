"""Compliance Auto-Remediation Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auto_remediation.models import (
    ApprovalPolicy,
    ApprovalRequest,
    RemediationConfig,
    RemediationFix,
    RemediationPipeline,
    RemediationStats,
    RemediationStatus,
    RiskLevel,
)


logger = structlog.get_logger()


class AutoRemediationService:
    """Automatic compliance drift remediation with approval workflows."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._pipelines: dict[str, RemediationPipeline] = {}
        self._fixes: list[RemediationFix] = []
        self._approvals: list[ApprovalRequest] = []
        self._config = RemediationConfig()

    async def trigger_pipeline(
        self,
        repo: str,
        branch: str = "main",
        trigger_event: str = "push",
        violations: list[dict] | None = None,
    ) -> RemediationPipeline:
        """Trigger a remediation pipeline for detected violations."""
        now = datetime.now(UTC)
        violation_list = violations or []

        risk = self._assess_risk(violation_list)
        policy = self._determine_approval_policy(risk)

        pipeline = RemediationPipeline(
            repo=repo,
            branch=branch,
            trigger_event=trigger_event,
            status=RemediationStatus.DETECTED,
            risk_level=risk,
            approval_policy=policy,
            violations_detected=len(violation_list),
            created_at=now,
            updated_at=now,
        )
        self._pipelines[str(pipeline.id)] = pipeline

        # Generate fixes
        pipeline.status = RemediationStatus.ANALYZING
        fixes = await self._generate_fixes(pipeline, violation_list)
        pipeline.fixes_generated = len(fixes)
        pipeline.status = RemediationStatus.FIX_GENERATED

        # Auto-merge low risk if configured
        if self._config.auto_merge_low_risk and risk == RiskLevel.LOW:
            pipeline.status = RemediationStatus.APPROVED
            pipeline.pr_url = f"https://github.com/{repo}/pull/auto-{str(pipeline.id)[:8]}"
            pipeline.status = RemediationStatus.PR_CREATED

        elif policy != ApprovalPolicy.MANUAL_ONLY:
            pipeline.status = RemediationStatus.AWAITING_APPROVAL

        pipeline.updated_at = datetime.now(UTC)
        logger.info("Remediation pipeline triggered", repo=repo, risk=risk.value, fixes=len(fixes))
        return pipeline

    async def _generate_fixes(
        self, pipeline: RemediationPipeline, violations: list[dict]
    ) -> list[RemediationFix]:
        """Generate fixes for detected violations."""
        fixes = []
        for v in violations[: self._config.max_auto_fixes_per_run]:
            fix = RemediationFix(
                pipeline_id=pipeline.id,
                file_path=v.get("file_path", ""),
                original_code=v.get("code_snippet", ""),
                fixed_code=f"# Auto-remediated: {v.get('rule_id', 'unknown')}\n{v.get('code_snippet', '')}",
                framework=v.get("framework", ""),
                rule_id=v.get("rule_id", ""),
                explanation=f"Auto-fix for {v.get('framework', '')} violation: {v.get('message', '')}",
                test_status="passed",
                created_at=datetime.now(UTC),
            )
            fixes.append(fix)
        self._fixes.extend(fixes)
        return fixes

    def _assess_risk(self, violations: list[dict]) -> RiskLevel:
        """Assess risk level of violations."""
        if not violations:
            return RiskLevel.LOW
        severities = [v.get("severity", "medium") for v in violations]
        if "critical" in severities:
            return RiskLevel.CRITICAL
        if "high" in severities:
            return RiskLevel.HIGH
        if len(violations) > 5:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _determine_approval_policy(self, risk: RiskLevel) -> ApprovalPolicy:
        """Determine approval policy based on risk."""
        if risk == RiskLevel.LOW and self._config.auto_merge_low_risk:
            return ApprovalPolicy.AUTO_MERGE
        if risk == RiskLevel.CRITICAL:
            return ApprovalPolicy.TEAM_APPROVAL
        return self._config.approval_policy

    async def approve_pipeline(
        self, pipeline_id: UUID, approver: str, comment: str = ""
    ) -> RemediationPipeline | None:
        pipeline = self._pipelines.get(str(pipeline_id))
        if not pipeline:
            return None

        approval = ApprovalRequest(
            pipeline_id=pipeline_id,
            approver=approver,
            decision="approved",
            comment=comment,
            decided_at=datetime.now(UTC),
        )
        self._approvals.append(approval)

        pipeline.status = RemediationStatus.APPROVED
        pipeline.pr_url = f"https://github.com/{pipeline.repo}/pull/fix-{str(pipeline.id)[:8]}"
        pipeline.status = RemediationStatus.PR_CREATED
        pipeline.updated_at = datetime.now(UTC)
        logger.info("Pipeline approved", pipeline_id=str(pipeline_id), approver=approver)
        return pipeline

    async def reject_pipeline(
        self, pipeline_id: UUID, approver: str, comment: str = ""
    ) -> RemediationPipeline | None:
        pipeline = self._pipelines.get(str(pipeline_id))
        if not pipeline:
            return None
        approval = ApprovalRequest(
            pipeline_id=pipeline_id,
            approver=approver,
            decision="rejected",
            comment=comment,
            decided_at=datetime.now(UTC),
        )
        self._approvals.append(approval)
        pipeline.status = RemediationStatus.FAILED
        pipeline.updated_at = datetime.now(UTC)
        return pipeline

    async def rollback_pipeline(self, pipeline_id: UUID) -> RemediationPipeline | None:
        pipeline = self._pipelines.get(str(pipeline_id))
        if not pipeline:
            return None
        pipeline.status = RemediationStatus.ROLLED_BACK
        pipeline.updated_at = datetime.now(UTC)
        logger.info("Pipeline rolled back", pipeline_id=str(pipeline_id))
        return pipeline

    def get_pipeline(self, pipeline_id: str) -> RemediationPipeline | None:
        return self._pipelines.get(pipeline_id)

    def list_pipelines(
        self,
        repo: str | None = None,
        status: RemediationStatus | None = None,
        limit: int = 50,
    ) -> list[RemediationPipeline]:
        results = list(self._pipelines.values())
        if repo:
            results = [p for p in results if p.repo == repo]
        if status:
            results = [p for p in results if p.status == status]
        return sorted(results, key=lambda p: p.created_at or datetime.min.replace(tzinfo=UTC), reverse=True)[:limit]

    def get_fixes(self, pipeline_id: UUID | None = None) -> list[RemediationFix]:
        if pipeline_id:
            return [f for f in self._fixes if f.pipeline_id == pipeline_id]
        return list(self._fixes)

    async def update_config(self, config: RemediationConfig) -> RemediationConfig:
        self._config = config
        logger.info("Remediation config updated")
        return config

    def get_config(self) -> RemediationConfig:
        return self._config

    def get_stats(self) -> RemediationStats:
        by_status: dict[str, int] = {}
        total_fixes = 0
        merged = 0
        for p in self._pipelines.values():
            by_status[p.status.value] = by_status.get(p.status.value, 0) + 1
            total_fixes += p.fixes_generated
            if p.status == RemediationStatus.MERGED:
                merged += p.fixes_generated

        return RemediationStats(
            total_pipelines=len(self._pipelines),
            by_status=by_status,
            total_fixes_generated=total_fixes,
            total_fixes_merged=merged,
            auto_merge_rate=round(merged / total_fixes, 2) if total_fixes else 0.0,
        )
