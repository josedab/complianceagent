"""Automated Certification Pipeline Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

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


class CertPipelineService:
    """End-to-end certification pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._runs: dict[str, CertificationRun] = {}
        self._gaps: list[ControlGap] = []
        self._reports: list[CertReport] = []

    async def start_certification(self, framework: str, target_date: str = "", auditor: str = "") -> CertificationRun:
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

        # Auto gap analysis
        gaps = []
        met = 0
        for ctrl in controls:
            if ctrl["gap_likely"]:
                gap = ControlGap(
                    run_id=run.id,
                    control_id=ctrl["id"],
                    control_name=ctrl["name"],
                    gap_description=f"Control {ctrl['id']} ({ctrl['name']}) requires implementation or additional evidence",
                    priority="high" if ctrl["id"].startswith("CC6") or ctrl["id"].startswith("A.9") else "medium",
                    evidence_needed=[f"Evidence for {ctrl['id']}", f"Configuration screenshot for {ctrl['name']}"],
                )
                gaps.append(gap)
            else:
                met += 1

        self._gaps.extend(gaps)
        run.controls_met = met
        run.gaps_found = len(gaps)
        run.readiness_pct = round(met / len(controls) * 100, 1) if controls else 0
        run.stages_completed.append("gap_analysis")
        run.stage = CertStage.EVIDENCE_COLLECTION

        self._runs[str(run.id)] = run
        logger.info("Certification started", framework=framework, gaps=len(gaps), readiness=run.readiness_pct)
        return run

    async def advance_stage(self, run_id: str) -> CertificationRun | None:
        run = self._runs.get(run_id)
        if not run:
            return None

        stage_order = list(CertStage)
        current_idx = stage_order.index(run.stage)
        if current_idx < len(stage_order) - 1:
            run.stages_completed.append(run.stage.value)
            run.stage = stage_order[current_idx + 1]
            if run.stage == CertStage.COMPLETED:
                run.completed_at = datetime.now(UTC)
        return run

    async def resolve_gap(self, gap_id: UUID, resolution: str = "") -> ControlGap | None:
        for gap in self._gaps:
            if gap.id == gap_id:
                gap.status = GapStatus.RESOLVED
                gap.remediation_plan = resolution
                # Update run stats
                for run in self._runs.values():
                    if run.id == gap.run_id:
                        run.gaps_resolved += 1
                        run.controls_met += 1
                        run.readiness_pct = round(run.controls_met / run.total_controls * 100, 1) if run.total_controls else 0
                return gap
        return None

    def get_gaps(self, run_id: str | None = None, status: GapStatus | None = None) -> list[ControlGap]:
        results = list(self._gaps)
        if run_id:
            run = self._runs.get(run_id)
            if run:
                results = [g for g in results if g.run_id == run.id]
        if status:
            results = [g for g in results if g.status == status]
        return results

    async def generate_report(self, run_id: str) -> CertReport | None:
        run = self._runs.get(run_id)
        if not run:
            return None
        open_gaps = sum(1 for g in self._gaps if g.run_id == run.id and g.status == GapStatus.OPEN)
        recommendations = []
        if open_gaps > 0:
            recommendations.append(f"Resolve {open_gaps} open control gaps before audit")
        if run.readiness_pct < 80:
            recommendations.append("Readiness below 80% — additional evidence collection recommended")
        recommendations.append("Schedule pre-audit readiness review with auditor")

        report = CertReport(
            run_id=run.id,
            framework=run.framework.value,
            readiness_pct=run.readiness_pct,
            controls_summary={"total": run.total_controls, "met": run.controls_met, "gaps": run.gaps_found, "resolved": run.gaps_resolved},
            open_gaps=open_gaps,
            recommendations=recommendations,
            generated_at=datetime.now(UTC),
        )
        self._reports.append(report)
        return report

    def get_run(self, run_id: str) -> CertificationRun | None:
        return self._runs.get(run_id)

    def list_runs(self, framework: CertFramework | None = None) -> list[CertificationRun]:
        results = list(self._runs.values())
        if framework:
            results = [r for r in results if r.framework == framework]
        return results

    def get_stats(self) -> CertPipelineStats:
        by_fw: dict[str, int] = {}
        by_stage: dict[str, int] = {}
        readiness = []
        total_gaps = 0
        resolved = 0
        for r in self._runs.values():
            by_fw[r.framework.value] = by_fw.get(r.framework.value, 0) + 1
            by_stage[r.stage.value] = by_stage.get(r.stage.value, 0) + 1
            readiness.append(r.readiness_pct)
            total_gaps += r.gaps_found
            resolved += r.gaps_resolved
        return CertPipelineStats(
            total_runs=len(self._runs),
            by_framework=by_fw,
            by_stage=by_stage,
            avg_readiness_pct=round(sum(readiness) / len(readiness), 1) if readiness else 0.0,
            total_gaps_found=total_gaps,
            total_gaps_resolved=resolved,
        )
