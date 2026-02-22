"""Compliance Digital Twin - Simulation and What-If Analysis."""

from app.services.digital_twin.codebase_graph import (
    CodebaseGraph,
    CodebaseGraphBuilder,
    CodeNode,
    CodeNodeType,
    DataFlow,
    DataFlowEdge,
    DataFlowType,
    DataSensitivity,
    get_codebase_graph_builder,
)
from app.services.digital_twin.enhanced import (
    BreachImpact,
    BreachScenario,
    DriftEvent,
    DriftType,
    EnhancedDigitalTwin,
    TimelinePoint,
    get_enhanced_digital_twin,
)
from app.services.digital_twin.migration_planner import (
    MigrationMilestone,
    MigrationPhase,
    MigrationPlan,
    MigrationPlanner,
    MigrationTask,
    TaskPriority,
    TaskStatus,
    get_migration_planner,
)
from app.services.digital_twin.models import (
    ComplianceSnapshot,
    ScenarioType,
    SimulationResult,
    SimulationScenario,
)
from app.services.digital_twin.simulator import ComplianceSimulator
from app.services.digital_twin.snapshot import SnapshotManager, get_snapshot_manager


# Global simulator instance
_simulator: ComplianceSimulator | None = None


def get_compliance_simulator() -> ComplianceSimulator:
    """Get or create the global compliance simulator."""
    global _simulator
    if _simulator is None:
        _simulator = ComplianceSimulator()
    return _simulator


__all__ = [
    "BreachImpact",
    "BreachScenario",
    "CodeNode",
    "CodeNodeType",
    "CodebaseGraph",
    "CodebaseGraphBuilder",
    "ComplianceIssue",
    "ComplianceSimulator",
    "ComplianceSnapshot",
    "ComplianceStatus",
    "DataFlow",
    "DataFlowEdge",
    "DataFlowType",
    "DataSensitivity",
    "DriftEvent",
    "DriftType",
    "EnhancedDigitalTwin",
    "MigrationMilestone",
    "MigrationPhase",
    "MigrationPlan",
    "MigrationPlanner",
    "MigrationTask",
    "RegulationCompliance",
    "ScenarioType",
    "SimulationResult",
    "SimulationScenario",
    "SnapshotManager",
    "TaskPriority",
    "TaskStatus",
    "TimelinePoint",
    "get_codebase_graph_builder",
    "get_compliance_simulator",
    "get_enhanced_digital_twin",
    "get_migration_planner",
    "get_snapshot_manager",
]
