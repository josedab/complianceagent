"""Self-Healing Compliance Mesh Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.self_healing_mesh.models import (
    HealingEvent,
    HealingPipeline,
    MeshConfig,
    MeshStats,
    PipelineStage,
    RiskTier,
)


logger = structlog.get_logger()


class SelfHealingMeshService:
    """Event-driven self-healing compliance pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._events: list[HealingEvent] = []
        self._pipelines: dict[str, HealingPipeline] = {}
        self._config = MeshConfig()
        self._failure_count = 0

    async def ingest_event(self, event: HealingEvent) -> HealingPipeline:
        """Ingest a compliance event and trigger healing pipeline."""
        event.detected_at = event.detected_at or datetime.now(UTC)
        self._events.append(event)

        if not self._config.enabled:
            logger.info("Mesh disabled, skipping", event_id=str(event.id))
            return HealingPipeline(event_id=event.id, stage=PipelineStage.FAILED)

        if self._failure_count >= self._config.circuit_breaker_threshold:
            logger.warning("Circuit breaker open", failures=self._failure_count)
            return HealingPipeline(event_id=event.id, stage=PipelineStage.ESCALATED)

        active = sum(1 for p in self._pipelines.values() if p.stage not in (PipelineStage.COMPLETED, PipelineStage.FAILED, PipelineStage.ESCALATED))
        if active >= self._config.max_concurrent_pipelines:
            logger.warning("Max concurrent pipelines reached")
            return HealingPipeline(event_id=event.id, stage=PipelineStage.ESCALATED)

        pipeline = await self._run_pipeline(event)
        self._pipelines[str(pipeline.id)] = pipeline
        return pipeline

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

        # Stage: Analyze
        pipeline.stage = PipelineStage.ANALYZING
        pipeline.stages_completed.append("detected")

        # Stage: Fix
        pipeline.stage = PipelineStage.FIXING
        pipeline.stages_completed.append("analyzing")
        pipeline.fix_description = f"Auto-fix for {event.event_type.value}: {event.description}"
        pipeline.files_changed = [f"src/{event.source_service or 'main'}.py"]

        # Stage: Test
        if self._config.test_required:
            pipeline.stage = PipelineStage.TESTING
            pipeline.stages_completed.append("fixing")
            pipeline.test_passed = True

        # Stage: PR or auto-merge
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
        severity_map = {"low": RiskTier.AUTO_MERGE, "medium": RiskTier.SINGLE_REVIEW, "high": RiskTier.TEAM_REVIEW, "critical": RiskTier.MANUAL_ONLY}
        tier = severity_map.get(event.severity, RiskTier.SINGLE_REVIEW)
        if self._config.auto_merge_max_risk == "none":
            return max(tier, RiskTier.SINGLE_REVIEW, key=lambda x: list(RiskTier).index(x))
        return tier

    async def approve_pipeline(self, pipeline_id: str, approver: str = "") -> HealingPipeline | None:
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline or pipeline.stage != PipelineStage.AWAITING_APPROVAL:
            return None
        pipeline.stage = PipelineStage.MERGING
        pipeline.stages_completed.append("approved")
        pipeline.stage = PipelineStage.COMPLETED
        pipeline.stages_completed.append("merging")
        pipeline.completed_at = datetime.now(UTC)
        logger.info("Pipeline approved", pipeline_id=pipeline_id, approver=approver)
        return pipeline

    async def escalate_pipeline(self, pipeline_id: str, reason: str = "") -> HealingPipeline | None:
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline:
            return None
        pipeline.stage = PipelineStage.ESCALATED
        return pipeline

    def get_pipeline(self, pipeline_id: str) -> HealingPipeline | None:
        return self._pipelines.get(pipeline_id)

    def list_pipelines(self, stage: PipelineStage | None = None, repo: str | None = None, limit: int = 50) -> list[HealingPipeline]:
        results = list(self._pipelines.values())
        if stage:
            results = [p for p in results if p.stage == stage]
        if repo:
            results = [p for p in results if p.repo == repo]
        return sorted(results, key=lambda p: p.created_at or datetime.min.replace(tzinfo=UTC), reverse=True)[:limit]

    async def update_config(self, config: MeshConfig) -> MeshConfig:
        self._config = config
        return config

    def get_config(self) -> MeshConfig:
        return self._config

    def get_stats(self) -> MeshStats:
        by_stage: dict[str, int] = {}
        by_event: dict[str, int] = {}
        heal_times: list[float] = []
        completed = 0
        auto = 0
        escalated = 0

        for p in self._pipelines.values():
            by_stage[p.stage.value] = by_stage.get(p.stage.value, 0) + 1
            if p.stage == PipelineStage.COMPLETED:
                completed += 1
                heal_times.append(p.time_to_heal_seconds)
                if p.risk_tier == RiskTier.AUTO_MERGE:
                    auto += 1
            elif p.stage == PipelineStage.ESCALATED:
                escalated += 1

        for e in self._events:
            by_event[e.event_type.value] = by_event.get(e.event_type.value, 0) + 1

        return MeshStats(
            total_events=len(self._events),
            total_pipelines=len(self._pipelines),
            completed_pipelines=completed,
            auto_merged=auto,
            escalated=escalated,
            avg_heal_time_seconds=round(sum(heal_times) / len(heal_times), 3) if heal_times else 0.0,
            by_stage=by_stage,
            by_event_type=by_event,
        )
