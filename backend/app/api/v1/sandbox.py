"""Sandbox Simulation API endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.api.v1.deps import DB, CurrentOrganization, OrgMember


logger = structlog.get_logger()

router = APIRouter()


class SimulationScenarioRequest(BaseModel):
    """Request to create a simulation scenario."""

    name: str
    simulation_type: str
    parameters: dict[str, Any]
    description: str = ""


class SimulationScenarioResponse(BaseModel):
    """Simulation scenario response."""

    id: str
    name: str
    simulation_type: str
    description: str
    created_at: datetime


class SimulationResultResponse(BaseModel):
    """Simulation result response."""

    id: str
    scenario_id: str
    passed: bool
    compliance_before: dict[str, float]
    compliance_after: dict[str, float]
    new_issues: list[dict[str, Any]]
    resolved_issues: list[dict[str, Any]]
    risk_delta: float
    recommendations: list[str]
    duration_ms: float


@router.post("/scenarios", response_model=SimulationScenarioResponse)
async def create_simulation_scenario(
    request: SimulationScenarioRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> SimulationScenarioResponse:
    """Create a new simulation scenario."""
    from app.services.sandbox import SimulationType, get_compliance_sandbox

    sandbox = get_compliance_sandbox()

    sim_type = SimulationType(request.simulation_type)
    scenario = await sandbox.create_scenario(
        name=request.name,
        simulation_type=sim_type,
        parameters=request.parameters,
        description=request.description,
        created_by=str(member.user_id),
    )

    return SimulationScenarioResponse(
        id=str(scenario.id),
        name=scenario.name,
        simulation_type=scenario.simulation_type.value,
        description=scenario.description,
        created_at=scenario.created_at,
    )


@router.post("/scenarios/{scenario_id}/run", response_model=SimulationResultResponse)
async def run_simulation(
    scenario_id: str,
    current_state: dict[str, Any],
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> SimulationResultResponse:
    """Run a simulation scenario."""
    from app.services.sandbox import get_compliance_sandbox

    sandbox = get_compliance_sandbox()

    scenario_uuid = UUID(scenario_id)
    result = await sandbox.run_simulation(scenario_uuid, current_state)

    # Determine if passed (no new critical issues)
    passed = not any(i.get("severity") == "error" for i in result.new_issues)

    return SimulationResultResponse(
        id=str(result.id),
        scenario_id=str(result.scenario_id),
        passed=passed,
        compliance_before=result.compliance_before,
        compliance_after=result.compliance_after,
        new_issues=result.new_issues,
        resolved_issues=result.resolved_issues,
        risk_delta=result.risk_delta,
        recommendations=result.recommendations,
        duration_ms=result.duration_ms,
    )


class ScenarioCompareRequest(BaseModel):
    """Request to compare multiple scenarios."""

    scenario_ids: list[str]
    current_state: dict[str, Any] = {}


class ScenarioComparisonResultSchema(BaseModel):
    """Per-scenario summary within a comparison."""

    scenario_name: str
    result_id: str
    risk_delta: float
    new_issues_count: int
    resolved_issues_count: int
    compliance_after: dict[str, float]
    duration_ms: float


class ScenarioCompareResponse(BaseModel):
    """Response for scenario comparison."""

    scenario_ids: list[str]
    results: dict[str, ScenarioComparisonResultSchema]
    best_scenario_id: str
    baseline_compliance: dict[str, float]
    compared_at: datetime


class ScenarioTemplateSchema(BaseModel):
    """Pre-built scenario template."""

    id: str
    name: str
    description: str
    simulation_type: str
    default_parameters: dict[str, Any]
    tags: list[str]


class ScenarioListResponse(BaseModel):
    """Paginated list of scenarios."""

    items: list[SimulationScenarioResponse]
    total: int
    page: int
    page_size: int


class ResultListResponse(BaseModel):
    """Paginated list of simulation results."""

    items: list[SimulationResultResponse]
    total: int
    page: int
    page_size: int


class DeleteScenarioResponse(BaseModel):
    """Response after deleting a scenario."""

    deleted: bool
    scenario_id: str


@router.get(
    "/scenarios",
    response_model=ScenarioListResponse,
    summary="List scenarios",
    description="List all simulation scenarios with optional pagination and creator filter.",
)
async def list_scenarios(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    created_by: str | None = Query(None, description="Filter by creator user ID"),
) -> ScenarioListResponse:
    """List all simulation scenarios."""
    from app.services.sandbox import get_compliance_sandbox

    sandbox = get_compliance_sandbox()
    scenarios = sandbox.list_scenarios(created_by=created_by)
    total = len(scenarios)

    start = (page - 1) * page_size
    end = start + page_size
    page_items = scenarios[start:end]

    return ScenarioListResponse(
        items=[
            SimulationScenarioResponse(
                id=str(s.id),
                name=s.name,
                simulation_type=s.simulation_type.value,
                description=s.description,
                created_at=s.created_at,
            )
            for s in page_items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/scenarios/{scenario_id}",
    response_model=SimulationScenarioResponse,
    summary="Get scenario",
    description="Get a specific simulation scenario by ID.",
)
async def get_scenario(
    scenario_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> SimulationScenarioResponse:
    """Get a specific simulation scenario."""
    from app.services.sandbox import get_compliance_sandbox

    sandbox = get_compliance_sandbox()
    scenario = sandbox.get_scenario(UUID(scenario_id))
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    return SimulationScenarioResponse(
        id=str(scenario.id),
        name=scenario.name,
        simulation_type=scenario.simulation_type.value,
        description=scenario.description,
        created_at=scenario.created_at,
    )


@router.delete(
    "/scenarios/{scenario_id}",
    response_model=DeleteScenarioResponse,
    summary="Delete scenario",
    description="Delete a simulation scenario and its associated results.",
)
async def delete_scenario(
    scenario_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> DeleteScenarioResponse:
    """Delete a simulation scenario."""
    from app.services.sandbox import get_compliance_sandbox

    sandbox = get_compliance_sandbox()
    deleted = await sandbox.delete_scenario(UUID(scenario_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Scenario not found")

    return DeleteScenarioResponse(deleted=True, scenario_id=scenario_id)


@router.post(
    "/scenarios/compare",
    response_model=ScenarioCompareResponse,
    summary="Compare scenarios",
    description="Run multiple scenarios in parallel and compare their results side-by-side.",
)
async def compare_scenarios(
    request: ScenarioCompareRequest,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ScenarioCompareResponse:
    """Compare multiple simulation scenarios."""
    from app.services.sandbox import get_compliance_sandbox

    sandbox = get_compliance_sandbox()

    scenario_uuids = [UUID(sid) for sid in request.scenario_ids]
    try:
        comparison = await sandbox.compare_scenarios(
            scenario_ids=scenario_uuids,
            current_state=request.current_state,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return ScenarioCompareResponse(
        scenario_ids=comparison.scenario_ids,
        results={
            k: ScenarioComparisonResultSchema(**v)
            for k, v in comparison.results.items()
        },
        best_scenario_id=comparison.best_scenario_id,
        baseline_compliance=comparison.baseline_compliance,
        compared_at=comparison.compared_at,
    )


@router.get(
    "/templates",
    response_model=list[ScenarioTemplateSchema],
    summary="Get scenario templates",
    description="Get pre-built scenario templates for common compliance use cases.",
)
async def get_scenario_templates(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> list[ScenarioTemplateSchema]:
    """Get pre-built scenario templates."""
    from app.services.sandbox import get_compliance_sandbox

    sandbox = get_compliance_sandbox()
    templates = sandbox.get_scenario_templates()

    return [
        ScenarioTemplateSchema(
            id=t.id,
            name=t.name,
            description=t.description,
            simulation_type=t.simulation_type.value,
            default_parameters=t.default_parameters,
            tags=t.tags,
        )
        for t in templates
    ]


@router.get(
    "/results",
    response_model=ResultListResponse,
    summary="List simulation results",
    description="List all simulation results with optional filtering by scenario and pagination.",
)
async def list_results(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    scenario_id: str | None = Query(None, description="Filter by scenario ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> ResultListResponse:
    """List simulation results."""
    from app.services.sandbox import get_compliance_sandbox

    sandbox = get_compliance_sandbox()
    scenario_uuid = UUID(scenario_id) if scenario_id else None
    results = sandbox.list_results(scenario_id=scenario_uuid)
    total = len(results)

    start = (page - 1) * page_size
    end = start + page_size
    page_items = results[start:end]

    return ResultListResponse(
        items=[
            SimulationResultResponse(
                id=str(r.id),
                scenario_id=str(r.scenario_id),
                passed=not any(i.get("severity") == "error" for i in r.new_issues),
                compliance_before=r.compliance_before,
                compliance_after=r.compliance_after,
                new_issues=r.new_issues,
                resolved_issues=r.resolved_issues,
                risk_delta=r.risk_delta,
                recommendations=r.recommendations,
                duration_ms=r.duration_ms,
            )
            for r in page_items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/results/{result_id}",
    response_model=SimulationResultResponse,
    summary="Get simulation result",
    description="Get a specific simulation result by ID.",
)
async def get_result(
    result_id: str,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> SimulationResultResponse:
    """Get a specific simulation result."""
    from app.services.sandbox import get_compliance_sandbox

    sandbox = get_compliance_sandbox()
    result = sandbox.get_result(UUID(result_id))
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    passed = not any(i.get("severity") == "error" for i in result.new_issues)

    return SimulationResultResponse(
        id=str(result.id),
        scenario_id=str(result.scenario_id),
        passed=passed,
        compliance_before=result.compliance_before,
        compliance_after=result.compliance_after,
        new_issues=result.new_issues,
        resolved_issues=result.resolved_issues,
        risk_delta=result.risk_delta,
        recommendations=result.recommendations,
        duration_ms=result.duration_ms,
    )
