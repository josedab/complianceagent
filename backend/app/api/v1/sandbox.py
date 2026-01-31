"""Sandbox Simulation API endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.v1.deps import DB, CurrentOrganization, OrgMember


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
