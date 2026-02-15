"""API endpoints for Regulatory Change Impact Simulator."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep

from app.services.impact_simulator import (
    ImpactSimulatorService,
    RegulatoryChange,
    ScenarioType,
)

logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class RegulatoryChangeSchema(BaseModel):
    """Regulatory change definition."""

    regulation: str = Field(..., description="Regulation identifier")
    article_ref: str = Field(default="")
    change_description: str = Field(..., description="Description of the change")
    scenario_type: str = Field(default="regulation_change")
    new_requirements: list[str] = Field(default_factory=list)
    modified_requirements: list[str] = Field(default_factory=list)
    removed_requirements: list[str] = Field(default_factory=list)
    effective_date: str = Field(default="")


class RunSimulationRequest(BaseModel):
    """Request to run a simulation."""

    scenario_name: str = Field(..., description="Name for this simulation")
    change: RegulatoryChangeSchema
    repo: str = Field(default="", description="Repository to analyze")


class AffectedComponentSchema(BaseModel):
    """Affected component response."""

    file_path: str
    component_type: str
    component_name: str
    impact_level: str
    changes_required: list[str]
    estimated_hours: float


class BlastRadiusSchema(BaseModel):
    """Blast radius response."""

    total_files: int
    total_services: int
    total_endpoints: int
    total_data_stores: int
    affected_components: list[AffectedComponentSchema]
    estimated_total_hours: float
    estimated_person_weeks: float


class SimulationResultSchema(BaseModel):
    """Simulation result response."""

    id: str
    scenario_name: str
    status: str
    overall_impact: str
    risk_score: float
    blast_radius: BlastRadiusSchema
    recommendations: list[str]
    completed_at: str | None


class PrebuiltScenarioSchema(BaseModel):
    """Pre-built scenario summary."""

    id: str
    name: str
    description: str
    category: str
    difficulty: str
    regulation: str


class CompareRequest(BaseModel):
    """Request to compare scenarios."""

    scenario_ids: list[str] = Field(..., min_length=1)
    repo: str = Field(default="")


# --- Endpoints ---


def _to_result_schema(r: Any) -> SimulationResultSchema:
    """Convert simulation result to response schema."""
    return SimulationResultSchema(
        id=str(r.id),
        scenario_name=r.scenario_name,
        status=r.status.value,
        overall_impact=r.overall_impact.value,
        risk_score=r.risk_score,
        blast_radius=BlastRadiusSchema(
            total_files=r.blast_radius.total_files,
            total_services=r.blast_radius.total_services,
            total_endpoints=r.blast_radius.total_endpoints,
            total_data_stores=r.blast_radius.total_data_stores,
            affected_components=[
                AffectedComponentSchema(
                    file_path=c.file_path, component_type=c.component_type,
                    component_name=c.component_name, impact_level=c.impact_level.value,
                    changes_required=c.changes_required, estimated_hours=c.estimated_hours,
                )
                for c in r.blast_radius.affected_components
            ],
            estimated_total_hours=r.blast_radius.estimated_total_hours,
            estimated_person_weeks=r.blast_radius.estimated_person_weeks,
        ),
        recommendations=r.recommendations,
        completed_at=r.completed_at.isoformat() if r.completed_at else None,
    )


@router.post(
    "/simulate",
    response_model=SimulationResultSchema,
    summary="Run impact simulation",
    description="Simulate the impact of a hypothetical regulatory change",
)
async def run_simulation(
    request: RunSimulationRequest,
    db: DB,
    copilot: CopilotDep,
) -> SimulationResultSchema:
    """Run a regulatory impact simulation."""
    service = ImpactSimulatorService(db=db, copilot_client=copilot)

    change = RegulatoryChange(
        regulation=request.change.regulation,
        article_ref=request.change.article_ref,
        change_description=request.change.change_description,
        scenario_type=ScenarioType(request.change.scenario_type),
        new_requirements=request.change.new_requirements,
        modified_requirements=request.change.modified_requirements,
        removed_requirements=request.change.removed_requirements,
        effective_date=request.change.effective_date,
    )

    result = await service.run_simulation(
        scenario_name=request.scenario_name, change=change, repo=request.repo,
    )
    return _to_result_schema(result)


@router.post(
    "/simulate/prebuilt/{scenario_id}",
    response_model=SimulationResultSchema,
    summary="Run pre-built scenario",
)
async def run_prebuilt(
    scenario_id: str,
    db: DB,
    copilot: CopilotDep,
    repo: str = "",
) -> SimulationResultSchema:
    """Run a pre-built simulation scenario."""
    service = ImpactSimulatorService(db=db, copilot_client=copilot)
    result = await service.run_prebuilt_scenario(scenario_id, repo=repo)
    if result.status.value == "failed":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")
    return _to_result_schema(result)


@router.get(
    "/scenarios",
    response_model=list[PrebuiltScenarioSchema],
    summary="List pre-built scenarios",
)
async def list_scenarios(
    db: DB,
    copilot: CopilotDep,
    category: str | None = None,
) -> list[PrebuiltScenarioSchema]:
    """List available pre-built scenarios."""
    service = ImpactSimulatorService(db=db, copilot_client=copilot)
    scenarios = await service.list_prebuilt_scenarios(category=category)
    return [
        PrebuiltScenarioSchema(
            id=s.id, name=s.name, description=s.description,
            category=s.category, difficulty=s.difficulty,
            regulation=s.change.regulation,
        )
        for s in scenarios
    ]


@router.get(
    "/results",
    response_model=list[SimulationResultSchema],
    summary="List simulation results",
)
async def list_results(
    db: DB,
    copilot: CopilotDep,
    limit: int = 20,
) -> list[SimulationResultSchema]:
    """List previous simulation results."""
    service = ImpactSimulatorService(db=db, copilot_client=copilot)
    results = await service.list_results(limit=limit)
    return [_to_result_schema(r) for r in results]


@router.get(
    "/results/{result_id}",
    response_model=SimulationResultSchema,
    summary="Get simulation result",
)
async def get_result(
    result_id: UUID,
    db: DB,
    copilot: CopilotDep,
) -> SimulationResultSchema:
    """Get a specific simulation result."""
    service = ImpactSimulatorService(db=db, copilot_client=copilot)
    result = await service.get_result(result_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")
    return _to_result_schema(result)


@router.post(
    "/compare",
    response_model=list[SimulationResultSchema],
    summary="Compare scenarios",
    description="Run and compare multiple scenarios side by side",
)
async def compare_scenarios(
    request: CompareRequest,
    db: DB,
    copilot: CopilotDep,
) -> list[SimulationResultSchema]:
    """Compare multiple scenarios."""
    service = ImpactSimulatorService(db=db, copilot_client=copilot)
    results = await service.compare_scenarios(request.scenario_ids, repo=request.repo)
    return [_to_result_schema(r) for r in results]


# --- Blast Radius & Detailed Comparison Schemas ---


class BlastRadiusComponentSchema(BaseModel):
    """A component affected by a regulatory change."""

    component_path: str
    component_type: str
    impact_level: str
    regulations_affected: list[str]
    estimated_effort_hours: float
    change_type: str
    description: str


class BlastRadiusAnalysisSchema(BaseModel):
    """Full blast radius analysis for a regulatory scenario."""

    scenario_id: str
    total_components: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    components: list[BlastRadiusComponentSchema]
    total_effort_hours: float
    risk_score: float


class DetailedCompareRequest(BaseModel):
    """Request to compare scenarios with detailed analysis."""

    scenario_ids: list[str] = Field(..., min_length=2, description="Scenario IDs to compare")


class ScenarioComparisonSchema(BaseModel):
    """Comparison of multiple regulatory scenarios."""

    scenarios: list[dict[str, Any]]
    winner: str
    recommendation: str
    comparison_matrix: dict[str, dict[str, float]]


# --- Blast Radius & Detailed Comparison Endpoints ---


@router.get(
    "/blast-radius/{scenario_id}",
    response_model=BlastRadiusAnalysisSchema,
    summary="Analyze blast radius",
    description="Analyze the blast radius of a regulatory change scenario",
)
async def analyze_blast_radius(
    scenario_id: str,
    db: DB,
    copilot: CopilotDep,
) -> BlastRadiusAnalysisSchema:
    """Analyze the blast radius of a regulatory change scenario."""
    service = ImpactSimulatorService(db=db, copilot_client=copilot)
    analysis = service.analyze_blast_radius(scenario_id)
    return BlastRadiusAnalysisSchema(**analysis.to_dict())


@router.post(
    "/compare-detailed",
    response_model=ScenarioComparisonSchema,
    summary="Compare scenarios with detailed analysis",
    description="Compare multiple regulatory impact scenarios side by side with blast radius analysis",
)
async def compare_scenarios_detailed(
    request: DetailedCompareRequest,
    db: DB,
    copilot: CopilotDep,
) -> ScenarioComparisonSchema:
    """Compare multiple regulatory impact scenarios side by side."""
    service = ImpactSimulatorService(db=db, copilot_client=copilot)
    comparison = service.compare_scenarios_detailed(request.scenario_ids)
    return ScenarioComparisonSchema(**comparison.to_dict())
