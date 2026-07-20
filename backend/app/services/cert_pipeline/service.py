"""Automated Certification Pipeline Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.critical_persistence import CertControlGapRecord, CertificationRunRecord
from app.services.cert_pipeline.models import (
    CertFramework,
    CertificationRun,
    CertPipelineStats,
    CertReport,
    CertStage,
    ControlGap,
    GapStatus,
)


logger = structlog.get_logger()

_FRAMEWORK_CONTROLS: dict[CertFramework, list[dict]] = {
    CertFramework.SOC2_TYPE2: [
        {"id": "CC1.1", "name": "Integrity and Ethical Values", "gap_likely": False},
        {"id": "CC5.1", "name": "Logical Access Controls", "gap_likely": True},
        {"id": "CC6.1", "name": "Access Security", "gap_likely": True},
        {"id": "CC6.2", "name": "Account Management", "gap_likely": False},
        {"id": "CC7.1", "name": "System Monitoring", "gap_likely": True},
        {"id": "CC7.2", "name": "Incident Detection", "gap_likely": False},
        {"id": "CC7.3", "name": "Incident Response", "gap_likely": True},
        {"id": "CC8.1", "name": "Change Management", "gap_likely": False},
        {"id": "CC9.1", "name": "Risk Mitigation", "gap_likely": True},
    ],
    CertFramework.ISO27001: [
        {"id": "A.5.1", "name": "Information Security Policies", "gap_likely": False},
        {"id": "A.8.1", "name": "Asset Management", "gap_likely": True},
        {"id": "A.9.1", "name": "Access Control Policy", "gap_likely": True},
        {"id": "A.10.1", "name": "Cryptographic Controls", "gap_likely": True},
        {"id": "A.12.4", "name": "Logging and Monitoring", "gap_likely": False},
        {"id": "A.14.1", "name": "Secure Development", "gap_likely": True},
        {"id": "A.16.1", "name": "Incident Management", "gap_likely": False},
        {"id": "A.18.1", "name": "Legal Compliance", "gap_likely": True},
    ],
}

_VALID_RUN_TRANSITIONS: dict[str, set[str]] = {
    "gap_analysis": {"evidence_collection"},
    "evidence_collection": {"report_generation"},
    "report_generation": {"auditor_review"},
    "auditor_review": {"remediation"},
    "remediation": {"certification"},
    "certification": {"completed"},
}


def _run_record_to_domain(rec: CertificationRunRecord) -> CertificationRun:
    meta = rec.run_metadata or {}
    return CertificationRun(
        id=rec.id,
        framework=CertFramework(rec.regulation),
        stage=CertStage(rec.status),
        stages_completed=meta.get("stages_completed", []),
        total_controls=rec.controls_total,
        controls_met=rec.controls_passed,
        gaps_found=rec.controls_failed,
        gaps_resolved=meta.get("gaps_resolved", 0),
        evidence_collected=meta.get("evidence_collected", 0),
        readiness_pct=rec.score or 0.0,
        auditor_assigned=meta.get("auditor_assigned", ""),
        target_date=meta.get("target_date", ""),
        started_at=rec.created_at,
        completed_at=rec.completed_at,
    )


def _gap_record_to_domain(rec: CertControlGapRecord) -> ControlGap:
    meta = rec.gap_metadata or {}
    return ControlGap(
        id=rec.id,
        run_id=rec.run_id,
        control_id=rec.control_id,
        control_name=meta.get("control_name", ""),
        gap_description=rec.description,
        status=GapStatus(meta.get("status", "open")),
        remediation_plan=rec.remediation_hint or "",
        evidence_needed=meta.get("evidence_needed", []),
        priority=rec.severity,
    )


class CertPipelineService:
    """End-to-end certification pipeline."""

    def __init__(self, db: AsyncSession, organization_id: UUID | None = None):
        self.db = db
        self.organization_id = organization_id

    async def start_certification(
        self, framework: str, target_date: str = "", auditor: str = ""
    ) -> CertificationRun:
        fw = CertFramework(framework)
        controls = _FRAMEWORK_CONTROLS.get(fw, [])
        now = datetime.now(UTC)

        run = CertificationRun(
            framework=fw,
            stage=CertStage.GAP_ANALYSIS,
            total_controls=len(controls),
            auditor_assigned=auditor,
            target_date=target_date,
            started_at=now,
        )

        gaps = []
        met = 0
        for ctrl in controls:
            if ctrl["gap_likely"]:
                gap = ControlGap(
                    run_id=run.id,
                    control_id=ctrl["id"],
                    control_name=ctrl["name"],
                    gap_description=f"Control {ctrl['id']} ({ctrl['name']}) requires implementation or additional evidence",
                    priority="high"
                    if ctrl["id"].startswith("CC6") or ctrl["id"].startswith("A.9")
                    else "medium",
                    evidence_needed=[
                        f"Evidence for {ctrl['id']}",
                        f"Configuration screenshot for {ctrl['name']}",
                    ],
                )
                gaps.append(gap)
            else:
                met += 1

        run.controls_met = met
        run.gaps_found = len(gaps)
        run.readiness_pct = round(met / len(controls) * 100, 1) if controls else 0
        run.stages_completed.append("gap_analysis")
        run.stage = CertStage.EVIDENCE_COLLECTION

        # Persist run
        run_rec = CertificationRunRecord(
            id=run.id,
            organization_id=self.organization_id,
            regulation=fw.value,
            run_type="automated",
            status=run.stage.value,
            score=run.readiness_pct,
            controls_total=run.total_controls,
            controls_passed=met,
            controls_failed=len(gaps),
            run_metadata={
                "stages_completed": run.stages_completed,
                "auditor_assigned": auditor,
                "target_date": target_date,
                "gaps_resolved": 0,
            },
        )
        self.db.add(run_rec)

        # Persist gaps
        for gap in gaps:
            gap_rec = CertControlGapRecord(
                id=gap.id,
                organization_id=self.organization_id,
                run_id=run.id,
                control_id=gap.control_id,
                severity=gap.priority,
                description=gap.gap_description,
                remediation_hint=gap.remediation_plan or None,
                gap_metadata={
                    "control_name": gap.control_name,
                    "status": gap.status.value,
                    "evidence_needed": gap.evidence_needed,
                },
            )
            self.db.add(gap_rec)

        await self.db.flush()
        logger.info(
            "Certification started",
            framework=framework,
            gaps=len(gaps),
            readiness=run.readiness_pct,
        )
        return run

    async def advance_stage(self, run_id: str) -> CertificationRun | None:
        rec = await self._get_run_record(run_id)
        if not rec:
            return None

        stage_order = list(CertStage)
        current_stage = CertStage(rec.status)
        current_idx = stage_order.index(current_stage)
        if current_idx < len(stage_order) - 1:
            meta = dict(rec.run_metadata or {})
            completed = list(meta.get("stages_completed", []))
            completed.append(current_stage.value)
            new_stage = stage_order[current_idx + 1]
            rec.status = new_stage.value
            meta["stages_completed"] = completed
            rec.run_metadata = meta
            if new_stage == CertStage.COMPLETED:
                rec.completed_at = datetime.now(UTC)
            await self.db.flush()

        return _run_record_to_domain(rec)

    async def resolve_gap(self, gap_id: UUID, resolution: str = "") -> ControlGap | None:
        stmt = select(CertControlGapRecord).where(
            CertControlGapRecord.id == gap_id,
            CertControlGapRecord.organization_id == self.organization_id,
        )
        result = await self.db.execute(stmt)
        gap_rec = result.scalar_one_or_none()
        if not gap_rec:
            return None

        meta = dict(gap_rec.gap_metadata or {})
        meta["status"] = GapStatus.RESOLVED.value
        gap_rec.gap_metadata = meta
        gap_rec.remediation_hint = resolution or gap_rec.remediation_hint

        # Update run stats
        run_rec = await self._get_run_record(str(gap_rec.run_id))
        if run_rec:
            run_meta = dict(run_rec.run_metadata or {})
            run_meta["gaps_resolved"] = run_meta.get("gaps_resolved", 0) + 1
            run_rec.controls_passed = (run_rec.controls_passed or 0) + 1
            run_rec.score = (
                round(run_rec.controls_passed / run_rec.controls_total * 100, 1)
                if run_rec.controls_total
                else 0
            )
            run_rec.run_metadata = run_meta

        await self.db.flush()
        return _gap_record_to_domain(gap_rec)

    async def get_gaps(
        self, run_id: str | None = None, status: GapStatus | None = None
    ) -> list[ControlGap]:
        stmt = select(CertControlGapRecord).where(
            CertControlGapRecord.organization_id == self.organization_id,
        )
        if run_id:
            stmt = stmt.where(CertControlGapRecord.run_id == UUID(run_id))
        result = await self.db.execute(stmt)
        gaps = [_gap_record_to_domain(r) for r in result.scalars().all()]
        if status:
            gaps = [g for g in gaps if g.status == status]
        return gaps

    async def generate_report(self, run_id: str) -> CertReport | None:
        rec = await self._get_run_record(run_id)
        if not rec:
            return None
        run = _run_record_to_domain(rec)
        gaps = await self.get_gaps(run_id=run_id)
        open_gaps = sum(1 for g in gaps if g.status == GapStatus.OPEN)
        recommendations = []
        if open_gaps > 0:
            recommendations.append(f"Resolve {open_gaps} open control gaps before audit")
        if run.readiness_pct < 80:
            recommendations.append(
                "Readiness below 80% — additional evidence collection recommended"
            )
        recommendations.append("Schedule pre-audit readiness review with auditor")

        return CertReport(
            run_id=run.id,
            framework=run.framework.value,
            readiness_pct=run.readiness_pct,
            controls_summary={
                "total": run.total_controls,
                "met": run.controls_met,
                "gaps": run.gaps_found,
                "resolved": run.gaps_resolved,
            },
            open_gaps=open_gaps,
            recommendations=recommendations,
            generated_at=datetime.now(UTC),
        )

    async def get_run(self, run_id: str) -> CertificationRun | None:
        rec = await self._get_run_record(run_id)
        return _run_record_to_domain(rec) if rec else None

    async def list_runs(self, framework: CertFramework | None = None) -> list[CertificationRun]:
        stmt = select(CertificationRunRecord).where(
            CertificationRunRecord.organization_id == self.organization_id,
        )
        if framework:
            stmt = stmt.where(CertificationRunRecord.regulation == framework.value)
        result = await self.db.execute(stmt)
        return [_run_record_to_domain(r) for r in result.scalars().all()]

    async def get_stats(self) -> CertPipelineStats:
        runs = await self.list_runs()
        by_fw: dict[str, int] = {}
        by_stage: dict[str, int] = {}
        readiness = []
        total_gaps = 0
        resolved = 0
        for r in runs:
            by_fw[r.framework.value] = by_fw.get(r.framework.value, 0) + 1
            by_stage[r.stage.value] = by_stage.get(r.stage.value, 0) + 1
            readiness.append(r.readiness_pct)
            total_gaps += r.gaps_found
            resolved += r.gaps_resolved
        return CertPipelineStats(
            total_runs=len(runs),
            by_framework=by_fw,
            by_stage=by_stage,
            avg_readiness_pct=round(sum(readiness) / len(readiness), 1) if readiness else 0.0,
            total_gaps_found=total_gaps,
            total_gaps_resolved=resolved,
        )

    async def _get_run_record(self, run_id: str) -> CertificationRunRecord | None:
        stmt = select(CertificationRunRecord).where(
            CertificationRunRecord.id == UUID(run_id),
            CertificationRunRecord.organization_id == self.organization_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
