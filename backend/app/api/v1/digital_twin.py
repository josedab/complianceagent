"""API endpoints for Compliance Digital Twin."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.digital_twin import (
    ComplianceSimulator,
    ScenarioType,
    SnapshotManager,
    get_compliance_simulator,
    get_snapshot_manager,
)


router = APIRouter(prefix="/digital-twin", tags=["digital-twin"])


# Request/Response Models
class CreateSnapshotRequest(BaseModel):
    """Request to create a compliance snapshot."""
    
    organization_id: UUID
    repository_id: UUID | None = None
    name: str | None = None
    commit_sha: str | None = None
    branch: str | None = None
    compliance_data: dict[str, Any] | None = None


class SnapshotResponse(BaseModel):
    """Compliance snapshot response."""
    
    id: UUID
    organization_id: UUID
    repository_id: UUID | None
    name: str
    created_at: str
    overall_score: float
    overall_status: str
    files_analyzed: int
    regulations: list[dict[str, Any]]
    issues_count: int


class CreateScenarioRequest(BaseModel):
    """Request to create a simulation scenario."""
    
    organization_id: UUID
    name: str
    scenario_type: str = Field(..., description="Type: code_change, architecture_change, vendor_change, regulation_adoption, data_flow_change, infrastructure_change")
    parameters: dict[str, Any]
    description: str = ""
    created_by: str | None = None


class ScenarioResponse(BaseModel):
    """Simulation scenario response."""
    
    id: UUID
    organization_id: UUID
    name: str
    description: str
    scenario_type: str
    created_at: str


class RunSimulationRequest(BaseModel):
    """Request to run a simulation."""
    
    scenario_id: UUID
    baseline_snapshot_id: UUID | None = None


class SimulationResultResponse(BaseModel):
    """Simulation result response."""
    
    id: UUID
    scenario_id: UUID
    baseline_snapshot_id: UUID
    baseline_score: float
    simulated_score: float
    score_delta: float
    passed: bool
    new_issues_count: int
    resolved_issues_count: int
    new_critical_issues: int
    recommendations: list[str]
    warnings: list[str]
    duration_ms: float


class CompareSnapshotsRequest(BaseModel):
    """Request to compare two snapshots."""
    
    snapshot1_id: UUID
    snapshot2_id: UUID


# Snapshot Endpoints
@router.post("/snapshots", response_model=SnapshotResponse)
async def create_snapshot(request: CreateSnapshotRequest):
    """Create a new compliance snapshot.
    
    Creates a point-in-time capture of the compliance state for an organization
    or repository. This serves as the baseline for what-if simulations.
    """
    manager = get_snapshot_manager()
    
    snapshot = await manager.create_snapshot(
        organization_id=request.organization_id,
        repository_id=request.repository_id,
        name=request.name,
        commit_sha=request.commit_sha,
        branch=request.branch,
        compliance_data=request.compliance_data,
    )
    
    return SnapshotResponse(
        id=snapshot.id,
        organization_id=snapshot.organization_id,
        repository_id=snapshot.repository_id,
        name=snapshot.name,
        created_at=snapshot.created_at.isoformat(),
        overall_score=snapshot.overall_score,
        overall_status=snapshot.overall_status.value,
        files_analyzed=snapshot.files_analyzed,
        regulations=[
            {
                "regulation": r.regulation,
                "status": r.status.value,
                "score": r.score,
                "issues_count": r.issues_count,
                "requirements_met": r.requirements_met,
                "requirements_total": r.requirements_total,
            }
            for r in snapshot.regulations
        ],
        issues_count=len(snapshot.issues),
    )


@router.get("/snapshots/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(snapshot_id: UUID):
    """Get a compliance snapshot by ID."""
    manager = get_snapshot_manager()
    snapshot = await manager.get_snapshot(snapshot_id)
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    return SnapshotResponse(
        id=snapshot.id,
        organization_id=snapshot.organization_id,
        repository_id=snapshot.repository_id,
        name=snapshot.name,
        created_at=snapshot.created_at.isoformat(),
        overall_score=snapshot.overall_score,
        overall_status=snapshot.overall_status.value,
        files_analyzed=snapshot.files_analyzed,
        regulations=[
            {
                "regulation": r.regulation,
                "status": r.status.value,
                "score": r.score,
                "issues_count": r.issues_count,
            }
            for r in snapshot.regulations
        ],
        issues_count=len(snapshot.issues),
    )


@router.get("/snapshots/{snapshot_id}/issues")
async def get_snapshot_issues(snapshot_id: UUID, limit: int = 100):
    """Get issues from a compliance snapshot."""
    manager = get_snapshot_manager()
    snapshot = await manager.get_snapshot(snapshot_id)
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    return {
        "snapshot_id": str(snapshot_id),
        "total_issues": len(snapshot.issues),
        "issues": [
            {
                "code": i.code,
                "message": i.message,
                "severity": i.severity,
                "regulation": i.regulation,
                "file_path": i.file_path,
                "line_number": i.line_number,
                "category": i.category,
            }
            for i in snapshot.issues[:limit]
        ],
    }


@router.get("/organizations/{organization_id}/snapshots")
async def list_snapshots(organization_id: UUID, limit: int = 50):
    """List snapshots for an organization."""
    manager = get_snapshot_manager()
    snapshots = await manager.list_snapshots(organization_id, limit=limit)
    
    return {
        "organization_id": str(organization_id),
        "count": len(snapshots),
        "snapshots": [
            {
                "id": str(s.id),
                "name": s.name,
                "created_at": s.created_at.isoformat(),
                "overall_score": s.overall_score,
                "overall_status": s.overall_status.value,
            }
            for s in snapshots
        ],
    }


@router.get("/organizations/{organization_id}/snapshots/latest")
async def get_latest_snapshot(organization_id: UUID, repository_id: UUID | None = None):
    """Get the latest snapshot for an organization."""
    manager = get_snapshot_manager()
    snapshot = await manager.get_latest_snapshot(organization_id, repository_id)
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="No snapshots found")
    
    return SnapshotResponse(
        id=snapshot.id,
        organization_id=snapshot.organization_id,
        repository_id=snapshot.repository_id,
        name=snapshot.name,
        created_at=snapshot.created_at.isoformat(),
        overall_score=snapshot.overall_score,
        overall_status=snapshot.overall_status.value,
        files_analyzed=snapshot.files_analyzed,
        regulations=[
            {
                "regulation": r.regulation,
                "status": r.status.value,
                "score": r.score,
            }
            for r in snapshot.regulations
        ],
        issues_count=len(snapshot.issues),
    )


@router.post("/snapshots/compare")
async def compare_snapshots(request: CompareSnapshotsRequest):
    """Compare two compliance snapshots.
    
    Useful for comparing compliance state before and after changes,
    or tracking compliance drift over time.
    """
    manager = get_snapshot_manager()
    
    try:
        comparison = await manager.compare_snapshots(
            request.snapshot1_id,
            request.snapshot2_id,
        )
        return comparison
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/snapshots/{snapshot_id}")
async def delete_snapshot(snapshot_id: UUID):
    """Delete a compliance snapshot."""
    manager = get_snapshot_manager()
    deleted = manager.delete_snapshot(snapshot_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    return {"deleted": True, "snapshot_id": str(snapshot_id)}


# Scenario Endpoints
@router.post("/scenarios", response_model=ScenarioResponse)
async def create_scenario(request: CreateScenarioRequest):
    """Create a simulation scenario.
    
    Scenarios define hypothetical changes to test against the compliance baseline.
    Supported types:
    - code_change: Test impact of code modifications
    - architecture_change: Test adding/removing components
    - vendor_change: Test adding/removing third-party services
    - regulation_adoption: Test adopting new compliance frameworks
    - data_flow_change: Test changes to data processing
    - infrastructure_change: Test infrastructure modifications
    """
    simulator = get_compliance_simulator()
    
    try:
        scenario_type = ScenarioType(request.scenario_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario_type. Must be one of: {[t.value for t in ScenarioType]}",
        )
    
    scenario = await simulator.create_scenario(
        organization_id=request.organization_id,
        name=request.name,
        scenario_type=scenario_type,
        parameters=request.parameters,
        description=request.description,
        created_by=request.created_by,
    )
    
    return ScenarioResponse(
        id=scenario.id,
        organization_id=scenario.organization_id,
        name=scenario.name,
        description=scenario.description,
        scenario_type=scenario.scenario_type.value,
        created_at=scenario.created_at.isoformat(),
    )


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: UUID):
    """Get a simulation scenario by ID."""
    simulator = get_compliance_simulator()
    scenario = await simulator.get_scenario(scenario_id)
    
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    return {
        "id": str(scenario.id),
        "organization_id": str(scenario.organization_id),
        "name": scenario.name,
        "description": scenario.description,
        "scenario_type": scenario.scenario_type.value,
        "created_at": scenario.created_at.isoformat(),
        "created_by": scenario.created_by,
        "parameters": scenario.parameters,
    }


# Simulation Endpoints
@router.post("/simulate", response_model=SimulationResultResponse)
async def run_simulation(request: RunSimulationRequest):
    """Run a what-if compliance simulation.
    
    Simulates the compliance impact of a scenario against a baseline snapshot.
    Returns predicted compliance score changes, new issues, and recommendations.
    """
    simulator = get_compliance_simulator()
    
    try:
        result = await simulator.run_simulation(
            scenario_id=request.scenario_id,
            baseline_snapshot_id=request.baseline_snapshot_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return SimulationResultResponse(
        id=result.id,
        scenario_id=result.scenario_id,
        baseline_snapshot_id=result.baseline_snapshot_id,
        baseline_score=result.baseline_score,
        simulated_score=result.simulated_score,
        score_delta=result.score_delta,
        passed=result.passed,
        new_issues_count=len(result.new_issues),
        resolved_issues_count=len(result.resolved_issues),
        new_critical_issues=result.new_critical_issues,
        recommendations=result.recommendations,
        warnings=result.warnings,
        duration_ms=result.duration_ms,
    )


@router.get("/results/{result_id}")
async def get_simulation_result(result_id: UUID):
    """Get a simulation result by ID."""
    simulator = get_compliance_simulator()
    result = await simulator.get_result(result_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return {
        "id": str(result.id),
        "scenario_id": str(result.scenario_id),
        "baseline_snapshot_id": str(result.baseline_snapshot_id),
        "baseline_score": result.baseline_score,
        "simulated_score": result.simulated_score,
        "score_delta": result.score_delta,
        "risk_delta": result.risk_delta,
        "passed": result.passed,
        "compliance_before": result.compliance_before,
        "compliance_after": result.compliance_after,
        "new_issues": [
            {
                "code": i.code,
                "message": i.message,
                "severity": i.severity,
                "regulation": i.regulation,
            }
            for i in result.new_issues
        ],
        "resolved_issues": [
            {
                "code": i.code,
                "message": i.message,
                "severity": i.severity,
            }
            for i in result.resolved_issues
        ],
        "new_critical_issues": result.new_critical_issues,
        "recommendations": result.recommendations,
        "warnings": result.warnings,
        "completed_at": result.completed_at.isoformat() if result.completed_at else None,
        "duration_ms": result.duration_ms,
    }


@router.get("/results/{result_id}/issues")
async def get_simulation_issues(result_id: UUID):
    """Get detailed issue information from a simulation result."""
    simulator = get_compliance_simulator()
    result = await simulator.get_result(result_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return {
        "result_id": str(result_id),
        "new_issues": [
            {
                "code": i.code,
                "message": i.message,
                "severity": i.severity,
                "regulation": i.regulation,
                "file_path": i.file_path,
                "line_number": i.line_number,
                "category": i.category,
            }
            for i in result.new_issues
        ],
        "resolved_issues": [
            {
                "code": i.code,
                "message": i.message,
                "severity": i.severity,
                "regulation": i.regulation,
            }
            for i in result.resolved_issues
        ],
    }
