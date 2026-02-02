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


# Migration Planning Endpoints
class GenerateMigrationPlanRequest(BaseModel):
    """Request to generate a migration plan."""
    
    simulation_result_id: UUID
    organization_id: UUID | None = None
    target_score: float = 0.95
    timeline_days: int = 90


class UpdateTaskStatusRequest(BaseModel):
    """Request to update task status."""
    
    status: str


@router.post("/migration-plans")
async def generate_migration_plan(request: GenerateMigrationPlanRequest):
    """Generate a migration plan from simulation results.
    
    Creates a comprehensive plan with tasks, milestones, and suggested PRs
    based on compliance gaps identified in the simulation.
    """
    from app.services.digital_twin import get_migration_planner, get_compliance_simulator
    
    simulator = get_compliance_simulator()
    result = await simulator.get_result(request.simulation_result_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Simulation result not found")
    
    planner = get_migration_planner()
    plan = await planner.generate_plan(
        simulation_result=result,
        organization_id=request.organization_id,
        target_score=request.target_score,
        timeline_days=request.timeline_days,
    )
    
    return {
        "id": str(plan.id),
        "name": plan.name,
        "created_at": plan.created_at.isoformat(),
        "metrics": {
            "total_tasks": plan.total_tasks,
            "total_estimated_hours": plan.total_estimated_hours,
            "current_score": plan.current_score,
            "target_score": plan.target_score,
            "progress_percentage": plan.progress_percentage,
        },
        "risk": {
            "level": plan.risk_level,
            "factors": plan.risk_factors,
        },
        "regulations_addressed": plan.regulations_addressed,
        "milestones": [
            {
                "id": str(m.id),
                "name": m.name,
                "phase": m.phase.value,
                "target_date": m.target_date.isoformat() if m.target_date else None,
                "task_count": len(m.tasks),
            }
            for m in plan.milestones
        ],
        "suggested_prs": plan.suggested_prs[:5],
    }


@router.get("/migration-plans/{plan_id}")
async def get_migration_plan(plan_id: UUID):
    """Get a migration plan by ID."""
    from app.services.digital_twin import get_migration_planner
    
    planner = get_migration_planner()
    plan = await planner.get_plan(plan_id)
    
    if not plan:
        raise HTTPException(status_code=404, detail="Migration plan not found")
    
    return {
        "id": str(plan.id),
        "name": plan.name,
        "description": plan.description,
        "created_at": plan.created_at.isoformat(),
        "updated_at": plan.updated_at.isoformat(),
        "metrics": {
            "total_tasks": plan.total_tasks,
            "completed_tasks": plan.completed_tasks,
            "blocked_tasks": plan.blocked_tasks,
            "total_estimated_hours": plan.total_estimated_hours,
            "current_score": plan.current_score,
            "target_score": plan.target_score,
            "progress_percentage": plan.progress_percentage,
        },
        "risk": {
            "level": plan.risk_level,
            "factors": plan.risk_factors,
        },
        "regulations_addressed": plan.regulations_addressed,
    }


@router.get("/migration-plans/{plan_id}/tasks")
async def get_migration_plan_tasks(plan_id: UUID, phase: str | None = None):
    """Get tasks for a migration plan."""
    from app.services.digital_twin import get_migration_planner
    
    planner = get_migration_planner()
    plan = await planner.get_plan(plan_id)
    
    if not plan:
        raise HTTPException(status_code=404, detail="Migration plan not found")
    
    tasks = plan.tasks
    if phase:
        tasks = [t for t in tasks if t.phase.value == phase]
    
    return {
        "plan_id": str(plan_id),
        "total": len(tasks),
        "tasks": [
            {
                "id": str(t.id),
                "title": t.title,
                "description": t.description,
                "phase": t.phase.value,
                "priority": t.priority.value,
                "status": t.status.value,
                "estimated_hours": t.estimated_hours,
                "assigned_to": t.assigned_to,
                "related_issues": t.related_issues,
                "related_files": t.related_files,
                "related_regulations": t.related_regulations,
                "acceptance_criteria": t.acceptance_criteria,
            }
            for t in tasks
        ],
    }


@router.patch("/migration-plans/{plan_id}/tasks/{task_id}")
async def update_migration_task(
    plan_id: UUID,
    task_id: UUID,
    request: UpdateTaskStatusRequest,
):
    """Update the status of a migration task."""
    from app.services.digital_twin import get_migration_planner, TaskStatus
    
    planner = get_migration_planner()
    
    try:
        status = TaskStatus(request.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {[s.value for s in TaskStatus]}",
        )
    
    task = await planner.update_task_status(plan_id, task_id, status)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "id": str(task.id),
        "title": task.title,
        "status": task.status.value,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


@router.get("/migration-plans/{plan_id}/export")
async def export_migration_plan(plan_id: UUID, format: str = "json"):
    """Export migration plan in various formats.
    
    Supported formats: json, markdown, jira
    """
    from app.services.digital_twin import get_migration_planner
    
    planner = get_migration_planner()
    
    try:
        export = await planner.export_plan(plan_id, format=format)
        return export
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Codebase Graph Endpoints
class BuildCodebaseGraphRequest(BaseModel):
    """Request to build a codebase graph."""
    
    repository_id: UUID
    organization_id: UUID
    files: dict[str, str]
    commit_sha: str | None = None


@router.post("/codebase-graphs")
async def build_codebase_graph(request: BuildCodebaseGraphRequest):
    """Build a codebase graph for compliance analysis.
    
    Analyzes source files to create a graph of code dependencies,
    data flows, and identifies compliance-sensitive areas.
    """
    from app.services.digital_twin import get_codebase_graph_builder
    
    builder = get_codebase_graph_builder()
    graph = await builder.build_graph(
        repository_id=request.repository_id,
        organization_id=request.organization_id,
        files=request.files,
        commit_sha=request.commit_sha,
    )
    
    return {
        "id": str(graph.id),
        "name": graph.name,
        "created_at": graph.created_at.isoformat(),
        "statistics": {
            "node_count": graph.node_count,
            "edge_count": graph.edge_count,
            "data_flow_count": len(graph.data_flows),
            "files_analyzed": graph.files_analyzed,
            "languages": graph.languages,
            "sensitive_nodes": len(graph.sensitive_data_nodes),
        },
    }


@router.get("/codebase-graphs/{graph_id}")
async def get_codebase_graph(graph_id: UUID):
    """Get codebase graph metadata."""
    from app.services.digital_twin import get_codebase_graph_builder
    
    builder = get_codebase_graph_builder()
    graph = await builder.get_graph(graph_id)
    
    if not graph:
        raise HTTPException(status_code=404, detail="Codebase graph not found")
    
    return {
        "id": str(graph.id),
        "name": graph.name,
        "repository_id": str(graph.repository_id) if graph.repository_id else None,
        "created_at": graph.created_at.isoformat(),
        "updated_at": graph.updated_at.isoformat(),
        "commit_sha": graph.commit_sha,
        "statistics": {
            "node_count": graph.node_count,
            "edge_count": graph.edge_count,
            "data_flow_count": len(graph.data_flows),
            "files_analyzed": graph.files_analyzed,
            "languages": graph.languages,
        },
    }


@router.get("/codebase-graphs/{graph_id}/visualization")
async def export_codebase_graph_visualization(graph_id: UUID):
    """Export codebase graph for visualization.
    
    Returns graph data in a format suitable for rendering with
    visualization libraries like D3.js, Cytoscape, or vis.js.
    """
    from app.services.digital_twin import get_codebase_graph_builder
    
    builder = get_codebase_graph_builder()
    
    try:
        return await builder.export_for_visualization(graph_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/codebase-graphs/{graph_id}/data-flows")
async def get_data_flows(graph_id: UUID, sensitivity: str | None = None):
    """Get data flows from a codebase graph.
    
    Optionally filter by data sensitivity level.
    """
    from app.services.digital_twin import get_codebase_graph_builder, DataSensitivity
    
    builder = get_codebase_graph_builder()
    graph = await builder.get_graph(graph_id)
    
    if not graph:
        raise HTTPException(status_code=404, detail="Codebase graph not found")
    
    flows = graph.data_flows
    
    if sensitivity:
        try:
            sens = DataSensitivity(sensitivity)
            flows = [f for f in flows if sens in f.data_sensitivity]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sensitivity. Must be one of: {[s.value for s in DataSensitivity]}",
            )
    
    return {
        "graph_id": str(graph_id),
        "total": len(flows),
        "data_flows": [
            {
                "id": str(f.id),
                "name": f.name,
                "description": f.description,
                "node_count": len(f.nodes),
                "data_types": f.data_types,
                "data_sensitivity": [s.value for s in f.data_sensitivity],
                "regulations_affected": f.regulations_affected,
                "compliance_score": f.compliance_score,
                "compliance_status": f.compliance_status,
            }
            for f in flows
        ],
    }


@router.get("/codebase-graphs/{graph_id}/sensitive-nodes")
async def get_sensitive_nodes(graph_id: UUID):
    """Get nodes handling sensitive data."""
    from app.services.digital_twin import get_codebase_graph_builder
    
    builder = get_codebase_graph_builder()
    graph = await builder.get_graph(graph_id)
    
    if not graph:
        raise HTTPException(status_code=404, detail="Codebase graph not found")
    
    sensitive = graph.sensitive_data_nodes
    
    return {
        "graph_id": str(graph_id),
        "total": len(sensitive),
        "nodes": [
            {
                "id": str(n.id),
                "type": n.node_type.value,
                "name": n.name,
                "qualified_name": n.qualified_name,
                "file_path": n.file_path,
                "data_types": n.data_types_handled,
                "data_sensitivity": [s.value for s in n.data_sensitivity],
                "compliance_issues": n.compliance_issues,
            }
            for n in sensitive
        ],
    }
