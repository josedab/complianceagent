"""API endpoints for Regulation Change Simulator."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB


logger = structlog.get_logger()
router = APIRouter()


def _serialize(obj: Any) -> dict[str, Any]:
    """Convert a dataclass to a JSON-serializable dict."""
    from dataclasses import fields, is_dataclass

    if not is_dataclass(obj):
        return obj

    result = {}
    for f in fields(obj):
        v = getattr(obj, f.name)
        result[f.name] = _ser_val(v)
    return result


def _ser_val(v: Any) -> Any:
    from dataclasses import is_dataclass
    from datetime import datetime
    from enum import Enum
    from uuid import UUID

    if v is None:
        return None
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, UUID):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, list):
        return [_ser_val(item) for item in v]
    if isinstance(v, dict):
        return {k: _ser_val(val) for k, val in v.items()}
    if is_dataclass(v):
        return _serialize(v)
    return v


# --- Schemas ---


class CreateScenarioRequest(BaseModel):
    regulation: str = Field(..., description="Regulation being simulated (e.g. 'GDPR', 'SOC2')")
    change_description: str = Field(..., description="Description of the regulatory change")
    affected_articles: list[str] = Field(
        default_factory=list, description="Articles affected by the change"
    )


class ScenarioResponse(BaseModel):
    model_config = {"extra": "ignore"}
    id: UUID | None = None
    regulation: str = ""
    change_description: str = ""
    affected_articles: list[str] = Field(default_factory=list)
    status: str = ""
    created_at: str = ""


class ScenarioListResponse(BaseModel):
    model_config = {"extra": "ignore"}
    scenarios: list[ScenarioResponse] = Field(default_factory=list)
    total: int = 0


class SimulationResultResponse(BaseModel):
    model_config = {"extra": "ignore"}
    scenario_id: UUID | None = None
    impact_score: float = 0.0
    affected_controls: int = 0
    gaps_introduced: int = 0
    remediation_items: list[dict[str, Any]] = Field(default_factory=list)
    estimated_effort_hours: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)


class RoadmapResponse(BaseModel):
    model_config = {"extra": "ignore"}
    scenario_id: UUID | None = None
    phases: list[dict[str, Any]] = Field(default_factory=list)
    total_duration_weeks: int = 0
    priority_actions: list[str] = Field(default_factory=list)
    resource_requirements: dict[str, Any] = Field(default_factory=dict)


class CompareRequest(BaseModel):
    scenario_ids: list[UUID] = Field(..., description="Scenario IDs to compare", min_length=2)


class CompareResponse(BaseModel):
    model_config = {"extra": "ignore"}
    scenarios: list[ScenarioResponse] = Field(default_factory=list)
    comparison_matrix: dict[str, Any] = Field(default_factory=dict)
    combined_impact_score: float = 0.0
    overlapping_controls: list[str] = Field(default_factory=list)


# --- Endpoints ---


@router.post(
    "/scenarios",
    response_model=ScenarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a simulation scenario",
)
async def create_scenario(request: CreateScenarioRequest, db: DB) -> ScenarioResponse:
    """Create a new regulation change scenario."""
    from app.services.reg_simulator import RegulatorySimulatorService as RegSimulatorService

    service = RegSimulatorService(db=db)
    from app.services.reg_simulator.models import SimulationScenario as ScenarioModel
    scenario_obj = ScenarioModel(
        regulation=request.regulation,
        change_description=request.change_description,
        affected_articles=request.affected_articles,
    )
    scenario = await service.create_scenario(scenario=scenario_obj)
    return ScenarioResponse(**_serialize(scenario))


@router.get("/scenarios", response_model=ScenarioListResponse, summary="List simulation scenarios")
async def list_scenarios(db: DB) -> ScenarioListResponse:
    """List all regulation change scenarios."""
    from app.services.reg_simulator import RegulatorySimulatorService as RegSimulatorService

    service = RegSimulatorService(db=db)
    scenarios = await service.list_scenarios()
    return ScenarioListResponse(
        scenarios=[ScenarioResponse(**_serialize(s)) for s in scenarios],
        total=len(scenarios),
    )


@router.get(
    "/scenarios/{scenario_id}", response_model=ScenarioResponse, summary="Get scenario details"
)
async def get_scenario(scenario_id: UUID, db: DB) -> ScenarioResponse:
    """Get details of a specific scenario."""
    from app.services.reg_simulator import RegulatorySimulatorService as RegSimulatorService

    service = RegSimulatorService(db=db)
    scenario = await service.get_scenario(scenario_id=scenario_id)
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")
    return ScenarioResponse(**_serialize(scenario))


@router.post(
    "/scenarios/{scenario_id}/simulate",
    response_model=SimulationResultResponse,
    summary="Run simulation on a scenario",
)
async def run_simulation(scenario_id: UUID, db: DB) -> SimulationResultResponse:
    """Run the impact simulation for a scenario."""
    from app.services.reg_simulator import RegulatorySimulatorService as RegSimulatorService

    service = RegSimulatorService(db=db)
    result = await service.run_simulation(scenario_id=scenario_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")
    return SimulationResultResponse(**_serialize(result))


@router.get(
    "/scenarios/{scenario_id}/result",
    response_model=SimulationResultResponse,
    summary="Get simulation result",
)
async def get_simulation_result(scenario_id: UUID, db: DB) -> SimulationResultResponse:
    """Get the result of a previously run simulation."""
    from app.services.reg_simulator import RegulatorySimulatorService as RegSimulatorService

    service = RegSimulatorService(db=db)
    result = await service.get_simulation_result(scenario_id=scenario_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Simulation result not found"
        )
    return SimulationResultResponse(**_serialize(result))


@router.post(
    "/scenarios/{scenario_id}/roadmap",
    response_model=RoadmapResponse,
    summary="Generate preparation roadmap",
)
async def generate_roadmap(scenario_id: UUID, db: DB) -> RoadmapResponse:
    """Generate a preparation roadmap for a regulation change scenario."""
    from app.services.reg_simulator import RegulatorySimulatorService as RegSimulatorService

    service = RegSimulatorService(db=db)
    roadmap = await service.generate_roadmap(scenario_id=scenario_id)
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")
    return RoadmapResponse(**_serialize(roadmap))


@router.post("/compare", response_model=CompareResponse, summary="Compare multiple scenarios")
async def compare_scenarios(request: CompareRequest, db: DB) -> CompareResponse:
    """Compare the impact of multiple regulation change scenarios."""
    from app.services.reg_simulator import RegulatorySimulatorService as RegSimulatorService

    service = RegSimulatorService(db=db)
    comparison = await service.compare_scenarios(scenario_ids=request.scenario_ids)
    return CompareResponse(**_serialize(comparison))
