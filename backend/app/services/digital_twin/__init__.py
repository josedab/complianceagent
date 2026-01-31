"""Compliance Digital Twin - Simulation and What-If Analysis."""

from app.services.digital_twin.snapshot import SnapshotManager, get_snapshot_manager
from app.services.digital_twin.simulator import ComplianceSimulator
from app.services.digital_twin.models import (
    ComplianceSnapshot,
    SimulationScenario,
    SimulationResult,
    ScenarioType,
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
    "SnapshotManager",
    "ComplianceSimulator",
    "ComplianceSnapshot",
    "SimulationScenario",
    "SimulationResult",
    "ScenarioType",
    "get_compliance_simulator",
    "get_snapshot_manager",
]
