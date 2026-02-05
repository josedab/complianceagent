"""Compliance Digital Twin - Simulation and What-If Analysis."""

from app.services.digital_twin.snapshot import SnapshotManager, get_snapshot_manager
from app.services.digital_twin.simulator import ComplianceSimulator
from app.services.digital_twin.models import (
    ComplianceSnapshot,
    SimulationScenario,
    SimulationResult,
    ScenarioType,
)
from app.services.digital_twin.migration_planner import (
    MigrationPlanner,
    MigrationPlan,
    MigrationTask,
    MigrationMilestone,
    MigrationPhase,
    TaskPriority,
    TaskStatus,
    get_migration_planner,
)
from app.services.digital_twin.codebase_graph import (
    CodebaseGraph,
    CodebaseGraphBuilder,
    CodeNode,
    DataFlowEdge,
    DataFlow,
    CodeNodeType,
    DataFlowType,
    DataSensitivity,
    get_codebase_graph_builder,
)
from app.services.digital_twin.enhanced import (
    EnhancedDigitalTwin,
    DriftType,
    BreachScenario,
    DriftEvent,
    BreachImpact,
    TimelinePoint,
    get_enhanced_digital_twin,
)


# Global simulator instance
_simulator: ComplianceSimulator | None = None


def get_compliance_simulator() -> ComplianceSimulator:
    """Get or create the global compliance simulator."""
    global _simulator
    if _simulator is None:
        _simulator = ComplianceSimulator()
    return _simulator


__all__ = [
    # Snapshot management
    "SnapshotManager",
    "get_snapshot_manager",
    # Simulation
    "ComplianceSimulator",
    "ComplianceSnapshot",
    "SimulationScenario",
    "SimulationResult",
    "ScenarioType",
    "get_compliance_simulator",
    # Migration planning
    "MigrationPlanner",
    "MigrationPlan",
    "MigrationTask",
    "MigrationMilestone",
    "MigrationPhase",
    "TaskPriority",
    "TaskStatus",
    "get_migration_planner",
    # Codebase graph
    "CodebaseGraph",
    "CodebaseGraphBuilder",
    "CodeNode",
    "DataFlowEdge",
    "DataFlow",
    "CodeNodeType",
    "DataFlowType",
    "DataSensitivity",
    "get_codebase_graph_builder",
    # Enhanced Digital Twin (Phase 3)
    "EnhancedDigitalTwin",
    "DriftType",
    "BreachScenario",
    "DriftEvent",
    "BreachImpact",
    "TimelinePoint",
    "get_enhanced_digital_twin",
]
