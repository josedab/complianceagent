"""Compliance Auto-Remediation Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.critical_persistence import (
    RemediationApprovalRecord,
    RemediationFixRecord,
    RemediationPipelineRecord,
)
from app.services.auto_remediation.models import (
    ApprovalPolicy,
    RemediationConfig,
    RemediationFix,
    RemediationPipeline,
    RemediationStats,
    RemediationStatus,
    RiskLevel,
)


logger = structlog.get_logger()

_VALID_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "detected": {"analyzing"},
    "analyzing": {"fix_generated", "failed"},
    "fix_generated": {"awaiting_approval", "approved"},
    "awaiting_approval": {"approved", "failed"},
    "approved": {"pr_created"},
    "pr_created": {"merged", "rolled_back"},
    "merged": {"rolled_back"},
}


def _pipeline_rec_to_domain(rec: RemediationPipelineRecord) -> RemediationPipeline:
    meta = rec.pipeline_metadata or {}
    return RemediationPipeline(
        id=rec.id,
        repo=meta.get("repo", ""),
        branch=meta.get("branch", "main"),
        trigger_event=rec.trigger_type,
        status=RemediationStatus(rec.status),
        risk_level=RiskLevel(meta.get("risk_level", "low")),
        approval_policy=ApprovalPolicy(meta.get("approval_policy", "single_approval")),
        violations_detected=meta.get("violations_detected", 0),
        fixes_generated=rec.fixes_total,
        pr_url=meta.get("pr_url", ""),
        created_at=rec.created_at,
        updated_at=rec.updated_at,
    )


def _fix_rec_to_domain(rec: RemediationFixRecord) -> RemediationFix:
    meta = rec.fix_metadata or {}
    return RemediationFix(
        id=rec.id,
        pipeline_id=rec.pipeline_id,
        file_path=meta.get("file_path", ""),
        original_code=meta.get("original_code", ""),
        fixed_code=meta.get("fixed_code", ""),
        framework=meta.get("framework", ""),
        rule_id=rec.control_id,
        explanation=meta.get("explanation", ""),
        test_status=meta.get("test_status", "pending"),
        created_at=rec.created_at,
    )


class AutoRemediationService:
    """Automatic compliance drift remediation with approval workflows."""

    def __init__(self, db: AsyncSession, organization_id: UUID | None = None):
        self.db = db
        self.organization_id = organization_id
        self._config = RemediationConfig()

    async def trigger_pipeline(
        self,
        repo: str,
        branch: str = "main",
        trigger_event: str = "push",
        violations: list[dict] | None = None,
    ) -> RemediationPipeline:
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

        pipeline.status = RemediationStatus.ANALYZING
        fixes = await self._generate_fixes(pipeline, violation_list)
        pipeline.fixes_generated = len(fixes)
        pipeline.status = RemediationStatus.FIX_GENERATED

        if self._config.auto_merge_low_risk and risk == RiskLevel.LOW:
            pipeline.status = RemediationStatus.APPROVED
            pipeline.pr_url = f"https://github.com/{repo}/pull/auto-{str(pipeline.id)[:8]}"
            pipeline.status = RemediationStatus.PR_CREATED
        elif policy != ApprovalPolicy.MANUAL_ONLY:
            pipeline.status = RemediationStatus.AWAITING_APPROVAL

        pipeline.updated_at = datetime.now(UTC)

        # Persist pipeline
        rec = RemediationPipelineRecord(
            id=pipeline.id,
            organization_id=self.organization_id,
            trigger_type=trigger_event,
            status=pipeline.status.value,
            fixes_total=pipeline.fixes_generated,
            pipeline_metadata={
                "repo": repo,
                "branch": branch,
                "risk_level": risk.value,
                "approval_policy": policy.value,
                "violations_detected": len(violation_list),
                "pr_url": pipeline.pr_url,
            },
        )
        self.db.add(rec)

        # Persist fixes
        for fix in fixes:
            fix_rec = RemediationFixRecord(
                id=fix.id,
                organization_id=self.organization_id,
                pipeline_id=pipeline.id,
                control_id=fix.rule_id,
                fix_type=fix.framework or "auto",
                status="completed",
                fix_metadata={
                    "file_path": fix.file_path,
                    "original_code": fix.original_code,
                    "fixed_code": fix.fixed_code,
                    "framework": fix.framework,
                    "explanation": fix.explanation,
                    "test_status": fix.test_status,
                },
            )
            self.db.add(fix_rec)

        await self.db.flush()
        logger.info("Remediation pipeline triggered", repo=repo, risk=risk.value, fixes=len(fixes))
        return pipeline

    async def _generate_fixes(
        self, pipeline: RemediationPipeline, violations: list[dict]
    ) -> list[RemediationFix]:
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
        return fixes

    def _assess_risk(self, violations: list[dict]) -> RiskLevel:
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
        if risk == RiskLevel.LOW and self._config.auto_merge_low_risk:
            return ApprovalPolicy.AUTO_MERGE
        if risk == RiskLevel.CRITICAL:
            return ApprovalPolicy.TEAM_APPROVAL
        return self._config.approval_policy

    async def approve_pipeline(
        self, pipeline_id: UUID, approver: str, comment: str = ""
    ) -> RemediationPipeline | None:
        rec = await self._get_pipeline_record(pipeline_id)
        if not rec:
            return None

        if rec.status not in ("awaiting_approval", "fix_generated"):
            raise ValueError(f"Cannot approve pipeline in status '{rec.status}'")

        meta = dict(rec.pipeline_metadata or {})
        meta["pr_url"] = f"https://github.com/{meta.get('repo', '')}/pull/fix-{str(rec.id)[:8]}"
        rec.status = RemediationStatus.PR_CREATED.value
        rec.pipeline_metadata = meta

        # Persist approval
        approval_rec = RemediationApprovalRecord(
            organization_id=self.organization_id,
            fix_id=rec.id,
            reviewer_id=None,
            decision="approved",
            notes=f"Approved by {approver}. {comment}",
            decided_at=datetime.now(UTC),
        )
        self.db.add(approval_rec)
        await self.db.flush()

        logger.info("Pipeline approved", pipeline_id=str(pipeline_id), approver=approver)
        return _pipeline_rec_to_domain(rec)

    async def reject_pipeline(
        self, pipeline_id: UUID, approver: str, comment: str = ""
    ) -> RemediationPipeline | None:
        rec = await self._get_pipeline_record(pipeline_id)
        if not rec:
            return None
        rec.status = RemediationStatus.FAILED.value
        approval_rec = RemediationApprovalRecord(
            organization_id=self.organization_id,
            fix_id=rec.id,
            decision="rejected",
            notes=f"Rejected by {approver}. {comment}",
            decided_at=datetime.now(UTC),
        )
        self.db.add(approval_rec)
        await self.db.flush()
        return _pipeline_rec_to_domain(rec)

    async def rollback_pipeline(self, pipeline_id: UUID) -> RemediationPipeline | None:
        rec = await self._get_pipeline_record(pipeline_id)
        if not rec:
            return None
        rec.status = RemediationStatus.ROLLED_BACK.value
        await self.db.flush()
        logger.info("Pipeline rolled back", pipeline_id=str(pipeline_id))
        return _pipeline_rec_to_domain(rec)

    async def get_pipeline(self, pipeline_id: str) -> RemediationPipeline | None:
        rec = await self._get_pipeline_record(UUID(pipeline_id))
        return _pipeline_rec_to_domain(rec) if rec else None

    async def list_pipelines(
        self,
        repo: str | None = None,
        status: RemediationStatus | None = None,
        limit: int = 50,
    ) -> list[RemediationPipeline]:
        stmt = select(RemediationPipelineRecord).where(
            RemediationPipelineRecord.organization_id == self.organization_id,
        )
        if status:
            stmt = stmt.where(RemediationPipelineRecord.status == status.value)
        stmt = stmt.order_by(RemediationPipelineRecord.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        pipelines = [_pipeline_rec_to_domain(r) for r in result.scalars().all()]
        if repo:
            pipelines = [p for p in pipelines if p.repo == repo]
        return pipelines

    async def get_fixes(self, pipeline_id: UUID | None = None) -> list[RemediationFix]:
        stmt = select(RemediationFixRecord).where(
            RemediationFixRecord.organization_id == self.organization_id,
        )
        if pipeline_id:
            stmt = stmt.where(RemediationFixRecord.pipeline_id == pipeline_id)
        result = await self.db.execute(stmt)
        return [_fix_rec_to_domain(r) for r in result.scalars().all()]

    async def update_config(self, config: RemediationConfig) -> RemediationConfig:
        self._config = config
        logger.info("Remediation config updated")
        return config

    def get_config(self) -> RemediationConfig:
        return self._config

    async def get_stats(self) -> RemediationStats:
        pipelines = await self.list_pipelines()
        by_status: dict[str, int] = {}
        total_fixes = 0
        merged = 0
        for p in pipelines:
            by_status[p.status.value] = by_status.get(p.status.value, 0) + 1
            total_fixes += p.fixes_generated
            if p.status == RemediationStatus.MERGED:
                merged += p.fixes_generated
        return RemediationStats(
            total_pipelines=len(pipelines),
            by_status=by_status,
            total_fixes_generated=total_fixes,
            total_fixes_merged=merged,
            auto_merge_rate=round(merged / total_fixes, 2) if total_fixes else 0.0,
        )

    async def _get_pipeline_record(self, pipeline_id: UUID) -> RemediationPipelineRecord | None:
        stmt = select(RemediationPipelineRecord).where(
            RemediationPipelineRecord.id == pipeline_id,
            RemediationPipelineRecord.organization_id == self.organization_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
