"""Compliance Digital Twin Simulation Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.twin_simulation.models import (
    ChangeType,
    ProposedChange,
    SimulationHistory,
    SimulationResult,
    SimulationStatus,
    TwinSnapshot,
)


logger = structlog.get_logger()

_CHANGE_IMPACT: dict[ChangeType, dict] = {
    ChangeType.CODE_CHANGE: {"base_delta": -2.0, "risk": "May introduce new compliance violations"},
    ChangeType.DEPENDENCY_ADD: {"base_delta": -3.0, "risk": "New dependency may have license/vulnerability issues"},
    ChangeType.DEPENDENCY_REMOVE: {"base_delta": 1.0, "risk": "Removing may break compliance features"},
    ChangeType.VENDOR_CHANGE: {"base_delta": -5.0, "risk": "Vendor change requires compliance re-assessment"},
    ChangeType.ARCHITECTURE_CHANGE: {"base_delta": -4.0, "risk": "Architecture changes may affect data flow compliance"},
    ChangeType.CONFIG_CHANGE: {"base_delta": -1.0, "risk": "Config changes may weaken security controls"},
}


class TwinSimulationService:
    """What-if compliance simulation with digital twin."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._snapshots: dict[str, TwinSnapshot] = {}
        self._simulations: list[SimulationResult] = []

    async def capture_snapshot(self, repo: str, name: str = "") -> TwinSnapshot:
        snapshot = TwinSnapshot(
            name=name or f"snapshot-{datetime.now(UTC).strftime('%Y%m%d-%H%M')}",
            repo=repo,
            score=85.0,
            frameworks={"GDPR": 88.0, "HIPAA": 82.0, "PCI-DSS": 90.0, "SOC2": 78.0},
            violation_count=12,
            captured_at=datetime.now(UTC),
        )
        self._snapshots[repo] = snapshot
        logger.info("Snapshot captured", repo=repo)
        return snapshot

    async def simulate(
        self,
        repo: str,
        changes: list[dict],
    ) -> SimulationResult:
        start = datetime.now(UTC)
        snapshot = self._snapshots.get(repo)
        base_score = snapshot.score if snapshot else 85.0

        proposed = [ProposedChange(
            change_type=ChangeType(c.get("change_type", "code_change")),
            description=c.get("description", ""),
            target=c.get("target", ""),
            details=c.get("details", {}),
        ) for c in changes]

        total_delta = 0.0
        framework_impacts = []
        warnings = []
        recommendations = []

        for change in proposed:
            impact = _CHANGE_IMPACT.get(change.change_type, {"base_delta": -1.0, "risk": "Unknown impact"})
            delta = impact["base_delta"]
            total_delta += delta
            warnings.append(impact["risk"])

            if change.change_type == ChangeType.VENDOR_CHANGE:
                framework_impacts.append({"framework": "SOC2", "delta": -3.0, "reason": "Vendor re-assessment required"})
                framework_impacts.append({"framework": "GDPR", "delta": -2.0, "reason": "Data processing agreement review needed"})
                recommendations.append("Conduct vendor compliance assessment before change")
            elif change.change_type == ChangeType.DEPENDENCY_ADD:
                framework_impacts.append({"framework": "NIS2", "delta": -2.0, "reason": "Supply chain risk"})
                recommendations.append("Run SBOM analysis on new dependency")
            elif change.change_type == ChangeType.CODE_CHANGE:
                framework_impacts.append({"framework": "GDPR", "delta": delta, "reason": "Code change may affect data processing"})
                recommendations.append("Run compliance scan on changed files")

        new_score = max(0, min(100, base_score + total_delta))
        risk = "low" if total_delta > -2 else "medium" if total_delta > -5 else "high"
        duration = (datetime.now(UTC) - start).total_seconds() * 1000

        result = SimulationResult(
            changes=proposed,
            status=SimulationStatus.COMPLETED,
            score_before=base_score,
            score_after=round(new_score, 1),
            score_delta=round(total_delta, 1),
            framework_impacts=framework_impacts,
            risk_assessment=risk,
            recommendations=recommendations,
            warnings=warnings,
            simulation_time_ms=round(duration, 2),
            created_at=datetime.now(UTC),
        )
        self._simulations.append(result)
        logger.info("Simulation completed", repo=repo, delta=total_delta, risk=risk)
        return result

    def get_snapshot(self, repo: str) -> TwinSnapshot | None:
        return self._snapshots.get(repo)

    def list_simulations(self, limit: int = 20) -> list[SimulationResult]:
        return sorted(self._simulations, key=lambda s: s.created_at or datetime.min.replace(tzinfo=UTC), reverse=True)[:limit]

    def get_history(self) -> SimulationHistory:
        by_type: dict[str, int] = {}
        deltas = []
        prevented = 0
        for sim in self._simulations:
            deltas.append(sim.score_delta)
            if sim.score_delta < -5:
                prevented += 1
            for c in sim.changes:
                by_type[c.change_type.value] = by_type.get(c.change_type.value, 0) + 1
        return SimulationHistory(
            total_simulations=len(self._simulations),
            avg_score_delta=round(sum(deltas) / len(deltas), 1) if deltas else 0.0,
            prevented_regressions=prevented,
            by_change_type=by_type,
        )
