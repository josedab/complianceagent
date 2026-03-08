"""Digital twin service facade — unified entry point for compliance simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog

from app.services.digital_twin.codebase_graph import (
    CodebaseGraphBuilder,
    get_codebase_graph_builder,
)
from app.services.digital_twin.enhanced import (
    BreachImpact,
    BreachScenario,
    DriftEvent,
    EnhancedDigitalTwin,
    get_enhanced_digital_twin,
)
from app.services.digital_twin.live_tracker import LivePostureTracker
from app.services.digital_twin.migration_planner import (
    MigrationPlan,
    MigrationPlanner,
    get_migration_planner,
)
from app.services.digital_twin.models import (
    ComplianceSnapshot,
    ScenarioType,
    SimulationResult,
    SimulationScenario,
)
from app.services.digital_twin.simulator import ComplianceSimulator, get_compliance_simulator
from app.services.digital_twin.snapshot import SnapshotManager, get_snapshot_manager


if TYPE_CHECKING:
    from uuid import UUID


logger = structlog.get_logger(__name__)

__all__ = [
    "BreachImpact",
    "ComplianceSnapshot",
    "DigitalTwinService",
    "DriftEvent",
    "MigrationPlan",
    "SimulationResult",
    "SimulationScenario",
    "get_digital_twin_service",
]


@dataclass
class DigitalTwinService:
    """Facade over digital-twin sub-modules: simulator, snapshot, enhanced, migration, and graph."""

    simulator: ComplianceSimulator = field(default_factory=get_compliance_simulator)
    snapshot_manager: SnapshotManager = field(default_factory=get_snapshot_manager)
    enhanced_twin: EnhancedDigitalTwin = field(default_factory=get_enhanced_digital_twin)
    migration_planner: MigrationPlanner = field(default_factory=get_migration_planner)
    graph_builder: CodebaseGraphBuilder = field(default_factory=get_codebase_graph_builder)

    # ------------------------------------------------------------------
    # Sub-module factories
    # ------------------------------------------------------------------

    def get_simulator(self) -> ComplianceSimulator:
        return self.simulator

    def get_migration_planner(self) -> MigrationPlanner:
        return self.migration_planner

    def get_live_tracker(self, db) -> LivePostureTracker:
        """Create a LivePostureTracker bound to the given DB session."""
        return LivePostureTracker(db=db)

    # ------------------------------------------------------------------
    # Scenario & simulation
    # ------------------------------------------------------------------

    async def create_scenario(
        self,
        organization_id: UUID,
        name: str,
        scenario_type: ScenarioType,
        parameters: dict[str, Any],
        description: str = "",
        created_by: str | None = None,
    ) -> SimulationScenario:
        """Create a new what-if scenario for simulation."""
        scenario = await self.simulator.create_scenario(
            organization_id,
            name,
            scenario_type,
            parameters,
            description=description,
            created_by=created_by,
        )
        logger.info("scenario_created", scenario_id=str(scenario.id), type=scenario_type)
        return scenario

    async def run_simulation(
        self,
        scenario_id: UUID,
        baseline_snapshot_id: UUID | None = None,
    ) -> SimulationResult:
        """Execute a simulation against an optional baseline snapshot."""
        result = await self.simulator.run_simulation(
            scenario_id,
            baseline_snapshot_id=baseline_snapshot_id,
        )
        logger.info(
            "simulation_completed",
            scenario_id=str(scenario_id),
            score_delta=result.score_delta,
        )
        return result

    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------

    async def get_snapshot(self, snapshot_id: UUID) -> ComplianceSnapshot | None:
        """Retrieve a compliance snapshot by ID."""
        return await self.snapshot_manager.get_snapshot(snapshot_id)

    async def get_latest_snapshot(
        self,
        organization_id: UUID,
        repository_id: UUID | None = None,
    ) -> ComplianceSnapshot | None:
        return await self.snapshot_manager.get_latest_snapshot(
            organization_id,
            repository_id=repository_id,
        )

    # ------------------------------------------------------------------
    # Breach & drift (enhanced twin)
    # ------------------------------------------------------------------

    async def simulate_breach(
        self,
        organization_id: UUID,
        scenario: BreachScenario,
        parameters: dict[str, Any] | None = None,
    ) -> BreachImpact:
        return await self.enhanced_twin.simulate_breach(
            organization_id,
            scenario,
            parameters=parameters,
        )

    async def detect_drift(
        self,
        organization_id: UUID,
        threshold: float = 0.05,
    ) -> list[DriftEvent]:
        return await self.enhanced_twin.detect_drift(organization_id, threshold=threshold)


_service: DigitalTwinService | None = None


def get_digital_twin_service() -> DigitalTwinService:
    """Return the global DigitalTwinService singleton."""
    global _service
    if _service is None:
        _service = DigitalTwinService()
        logger.info("digital_twin_service_initialized")
    return _service
