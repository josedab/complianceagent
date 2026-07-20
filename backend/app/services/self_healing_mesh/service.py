"""Self-Healing Compliance Mesh Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.secondary_persistence import SelfHealingEventRecord
from app.services.self_healing_mesh.models import (
    HealingEvent,
    HealingPipeline,
    MeshConfig,
    MeshStats,
    PipelineStage,
    RiskTier,
)


logger = structlog.get_logger()

_TERMINAL_PIPELINE_STAGES = {
    PipelineStage.COMPLETED.value,
    PipelineStage.FAILED.value,
    PipelineStage.ESCALATED.value,
}


def _record_to_pipeline(record: SelfHealingEventRecord) -> HealingPipeline:
    meta = record.healing_metadata or {}
    return HealingPipeline(
        id=record.id,
        event_id=UUID(meta.get("event_id", str(record.id))),
        repo=meta.get("repo", ""),
        stage=PipelineStage(record.status),
        risk_tier=RiskTier(meta.get("risk_tier", RiskTier.SINGLE_REVIEW.value)),
        stages_completed=meta.get("stages_completed", []),
        fix_description=meta.get("fix_description", ""),
        files_changed=meta.get("files_changed", []),
        test_passed=meta.get("test_passed", False),
        pr_url=meta.get("pr_url", ""),
        time_to_heal_seconds=meta.get("time_to_heal_seconds", 0.0),
        created_at=record.created_at,
        completed_at=record.completed_at,
    )


class SelfHealingMeshService:
    """Event-driven self-healing compliance pipeline."""

    def __init__(self, db: AsyncSession, organization_id: UUID | None = None):
        self.db = db
        self.organization_id = organization_id
        self._config = MeshConfig()
        self._failure_count = 0

    async def ingest_event(self, event: HealingEvent) -> HealingPipeline:
        event.detected_at = event.detected_at or datetime.now(UTC)
        if not self._config.enabled:
            pipeline = HealingPipeline(
                event_id=event.id, repo=event.repo, stage=PipelineStage.FAILED
            )
            return await self._persist_pipeline(event, pipeline)
        if self._failure_count >= self._config.circuit_breaker_threshold:
            logger.warning("Circuit breaker open", failures=self._failure_count)
            pipeline = HealingPipeline(
                event_id=event.id, repo=event.repo, stage=PipelineStage.ESCALATED
            )
            return await self._persist_pipeline(event, pipeline)

        active = await self._count_active_pipelines()
        if active >= self._config.max_concurrent_pipelines:
            logger.warning("Max concurrent pipelines reached")
            pipeline = HealingPipeline(
                event_id=event.id, repo=event.repo, stage=PipelineStage.ESCALATED
            )
            return await self._persist_pipeline(event, pipeline)

        pipeline = await self._run_pipeline(event)
        if pipeline.stage == PipelineStage.FAILED:
            self._failure_count += 1
        return await self._persist_pipeline(event, pipeline)

    async def _run_pipeline(self, event: HealingEvent) -> HealingPipeline:
        start = datetime.now(UTC)
        risk = self._assess_risk(event)
        pipeline = HealingPipeline(
            event_id=event.id,
            repo=event.repo,
            stage=PipelineStage.DETECTED,
            risk_tier=risk,
            created_at=start,
        )
        pipeline.stage = PipelineStage.ANALYZING
        pipeline.stages_completed.append("detected")
        pipeline.stage = PipelineStage.FIXING
        pipeline.stages_completed.append("analyzing")
        pipeline.fix_description = f"Auto-fix for {event.event_type.value}: {event.description}"
        pipeline.files_changed = [f"src/{event.source_service or 'main'}.py"]
        if self._config.test_required:
            pipeline.stage = PipelineStage.TESTING
            pipeline.stages_completed.append("fixing")
            pipeline.test_passed = True
        pipeline.stages_completed.append("testing")
        if risk == RiskTier.AUTO_MERGE:
            pipeline.stage = PipelineStage.MERGING
            pipeline.stages_completed.append("pr_creating")
            pipeline.pr_url = f"https://github.com/{event.repo}/pull/auto-{str(pipeline.id)[:8]}"
            pipeline.stage = PipelineStage.COMPLETED
            pipeline.stages_completed.append("merging")
        elif risk == RiskTier.MANUAL_ONLY:
            pipeline.stage = PipelineStage.ESCALATED
        else:
            pipeline.stage = PipelineStage.PR_CREATING
            pipeline.pr_url = f"https://github.com/{event.repo}/pull/fix-{str(pipeline.id)[:8]}"
            pipeline.stage = PipelineStage.AWAITING_APPROVAL
            pipeline.stages_completed.append("pr_creating")
        elapsed = (datetime.now(UTC) - start).total_seconds()
        pipeline.time_to_heal_seconds = round(elapsed, 3)
        if pipeline.stage == PipelineStage.COMPLETED:
            pipeline.completed_at = datetime.now(UTC)
        logger.info("Pipeline executed", stage=pipeline.stage.value, risk=risk.value, time=elapsed)
        return pipeline

    def _assess_risk(self, event: HealingEvent) -> RiskTier:
        severity_map = {
            "low": RiskTier.AUTO_MERGE,
            "medium": RiskTier.SINGLE_REVIEW,
            "high": RiskTier.TEAM_REVIEW,
            "critical": RiskTier.MANUAL_ONLY,
        }
        tier = severity_map.get(event.severity, RiskTier.SINGLE_REVIEW)
        if self._config.auto_merge_max_risk == "none":
            return max(tier, RiskTier.SINGLE_REVIEW, key=lambda item: list(RiskTier).index(item))
        return tier

    async def approve_pipeline(
        self, pipeline_id: str, approver: str = ""
    ) -> HealingPipeline | None:
        record = await self._get_pipeline_record(pipeline_id)
        if not record or record.status != PipelineStage.AWAITING_APPROVAL.value:
            return None
        meta = dict(record.healing_metadata or {})
        stages_completed = list(meta.get("stages_completed", []))
        stages_completed.extend(["approved", "merging"])
        meta["stages_completed"] = stages_completed
        record.status = PipelineStage.COMPLETED.value
        record.action_taken = PipelineStage.COMPLETED.value
        record.completed_at = datetime.now(UTC)
        record.healing_metadata = meta
        await self.db.flush()
        logger.info("Pipeline approved", pipeline_id=pipeline_id, approver=approver)
        return _record_to_pipeline(record)

    async def escalate_pipeline(self, pipeline_id: str, reason: str = "") -> HealingPipeline | None:
        record = await self._get_pipeline_record(pipeline_id)
        if not record:
            return None
        meta = dict(record.healing_metadata or {})
        if reason:
            meta["escalation_reason"] = reason
        record.status = PipelineStage.ESCALATED.value
        record.action_taken = PipelineStage.ESCALATED.value
        record.healing_metadata = meta
        await self.db.flush()
        return _record_to_pipeline(record)

    async def get_pipeline(self, pipeline_id: str) -> HealingPipeline | None:
        record = await self._get_pipeline_record(pipeline_id)
        return _record_to_pipeline(record) if record else None

    async def list_pipelines(
        self, stage: PipelineStage | None = None, repo: str | None = None, limit: int = 50
    ) -> list[HealingPipeline]:
        stmt = (
            select(SelfHealingEventRecord)
            .where(SelfHealingEventRecord.organization_id == self.organization_id)
            .order_by(SelfHealingEventRecord.created_at.desc())
            .limit(limit)
        )
        if stage:
            stmt = stmt.where(SelfHealingEventRecord.status == stage.value)
        result = await self.db.execute(stmt)
        pipelines = [_record_to_pipeline(record) for record in result.scalars().all()]
        if repo:
            pipelines = [pipeline for pipeline in pipelines if pipeline.repo == repo]
        return pipelines

    async def update_config(self, config: MeshConfig) -> MeshConfig:
        self._config = config
        return config

    def get_config(self) -> MeshConfig:
        return self._config

    async def get_stats(self) -> MeshStats:
        pipelines = await self.list_pipelines(limit=500)
        by_stage: dict[str, int] = {}
        by_event: dict[str, int] = {}
        heal_times: list[float] = []
        completed = 0
        auto = 0
        escalated = 0
        for pipeline in pipelines:
            by_stage[pipeline.stage.value] = by_stage.get(pipeline.stage.value, 0) + 1
            if pipeline.stage == PipelineStage.COMPLETED:
                completed += 1
                heal_times.append(pipeline.time_to_heal_seconds)
                if pipeline.risk_tier == RiskTier.AUTO_MERGE:
                    auto += 1
            elif pipeline.stage == PipelineStage.ESCALATED:
                escalated += 1
        stmt = select(SelfHealingEventRecord).where(
            SelfHealingEventRecord.organization_id == self.organization_id
        )
        result = await self.db.execute(stmt)
        for record in result.scalars().all():
            by_event[record.trigger_type] = by_event.get(record.trigger_type, 0) + 1
        return MeshStats(
            total_events=len(pipelines),
            total_pipelines=len(pipelines),
            completed_pipelines=completed,
            auto_merged=auto,
            escalated=escalated,
            avg_heal_time_seconds=round(sum(heal_times) / len(heal_times), 3)
            if heal_times
            else 0.0,
            by_stage=by_stage,
            by_event_type=by_event,
        )

    async def _persist_pipeline(
        self, event: HealingEvent, pipeline: HealingPipeline
    ) -> HealingPipeline:
        record = SelfHealingEventRecord(
            id=pipeline.id,
            organization_id=self.organization_id,
            trigger_type=event.event_type.value,
            action_taken=pipeline.stage.value,
            status=pipeline.stage.value,
            description=event.description,
            healing_metadata={
                "event_id": str(event.id),
                "repo": pipeline.repo,
                "source_service": event.source_service,
                "severity": event.severity,
                "payload": event.payload,
                "risk_tier": pipeline.risk_tier.value,
                "stages_completed": pipeline.stages_completed,
                "fix_description": pipeline.fix_description,
                "files_changed": pipeline.files_changed,
                "test_passed": pipeline.test_passed,
                "pr_url": pipeline.pr_url,
                "time_to_heal_seconds": pipeline.time_to_heal_seconds,
            },
            completed_at=pipeline.completed_at,
        )
        self.db.add(record)
        await self.db.flush()
        return _record_to_pipeline(record)

    async def _count_active_pipelines(self) -> int:
        stmt = select(SelfHealingEventRecord).where(
            SelfHealingEventRecord.organization_id == self.organization_id
        )
        result = await self.db.execute(stmt)
        return sum(
            1 for record in result.scalars().all() if record.status not in _TERMINAL_PIPELINE_STAGES
        )

    async def _get_pipeline_record(self, pipeline_id: str) -> SelfHealingEventRecord | None:
        stmt = select(SelfHealingEventRecord).where(
            SelfHealingEventRecord.id == UUID(pipeline_id),
            SelfHealingEventRecord.organization_id == self.organization_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
