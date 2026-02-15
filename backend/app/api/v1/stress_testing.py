"""API endpoints for Regulatory Compliance Stress Testing."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.stress_testing import (
    ScenarioType,
    SimulationRun,
    StressTestingService,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class CreateScenarioRequest(BaseModel):
    """Request to create a stress test scenario."""

    name: str = Field(..., description="Scenario name")
    scenario_type: str = Field(..., description="Type of scenario")
    description: str = Field(default="")
    parameters: dict[str, Any] = Field(default_factory=dict)


class ScenarioSchema(BaseModel):
    """Stress scenario response."""

    id: str
    name: str
    scenario_type: str
    description: str
    parameters: dict[str, Any]
    probability: float
    severity: str


class RunSimulationRequest(BaseModel):
    """Request to run a simulation."""

    scenario_id: str = Field(..., description="Scenario UUID")
    iterations: int = Field(default=1000, ge=1)
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)


class SimulationResultSchema(BaseModel):
    """Simulation result response."""

    id: str
    run_id: str
    metric: str
    p50: float
    p95: float
    p99: float
    mean: float
    std_dev: float
    distribution: list[dict[str, Any]]


class SimulationRunSchema(BaseModel):
    """Simulation run response."""

    id: str
    scenario_id: str
    iterations: int
    confidence_level: float
    status: str
    results: list[SimulationResultSchema]
    started_at: str | None
    completed_at: str | None


class RiskExposureRequest(BaseModel):
    """Request to calculate risk exposure."""

    regulation: str = Field(..., description="Regulation identifier")


class RiskExposureSchema(BaseModel):
    """Risk exposure response."""

    id: str
    regulation: str
    exposure_amount: float
    probability: float
    expected_loss: float
    risk_tier: str
    mitigations: list[str]


class StressTestReportSchema(BaseModel):
    """Stress test report response."""

    id: str
    total_scenarios: int
    total_simulations: int
    aggregate_exposure: float
    risk_exposures: list[RiskExposureSchema]
    worst_case_scenario: str
    recommendations: list[str]
    generated_at: str | None


# --- Endpoints ---


@router.post(
    "/scenarios",
    response_model=ScenarioSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create stress test scenario",
)
async def create_scenario(
    request: CreateScenarioRequest,
    db: DB,
    copilot: CopilotDep,
) -> ScenarioSchema:
    """Create a new stress test scenario."""
    service = StressTestingService(db=db, copilot_client=copilot)
    scenario = await service.create_scenario(
        name=request.name,
        scenario_type=ScenarioType(request.scenario_type),
        description=request.description,
        parameters=request.parameters,
    )
    return ScenarioSchema(
        id=str(scenario.id),
        name=scenario.name,
        scenario_type=scenario.scenario_type.value,
        description=scenario.description,
        parameters=scenario.parameters,
        probability=scenario.probability,
        severity=scenario.severity.value,
    )


@router.get(
    "/scenarios",
    response_model=list[ScenarioSchema],
    summary="List stress test scenarios",
)
async def list_scenarios(
    db: DB,
    copilot: CopilotDep,
) -> list[ScenarioSchema]:
    """List all stress test scenarios."""
    service = StressTestingService(db=db, copilot_client=copilot)
    scenarios = await service.list_scenarios()
    return [
        ScenarioSchema(
            id=str(s.id),
            name=s.name,
            scenario_type=s.scenario_type.value,
            description=s.description,
            parameters=s.parameters,
            probability=s.probability,
            severity=s.severity.value,
        )
        for s in scenarios
    ]


@router.post(
    "/simulate",
    response_model=SimulationRunSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Run Monte Carlo simulation",
)
async def run_simulation(
    request: RunSimulationRequest,
    db: DB,
    copilot: CopilotDep,
) -> SimulationRunSchema:
    """Run a Monte Carlo simulation for a scenario."""
    service = StressTestingService(db=db, copilot_client=copilot)
    run = await service.run_simulation(
        scenario_id=UUID(request.scenario_id),
        iterations=request.iterations,
        confidence=request.confidence,
    )
    return _run_to_schema(run)


@router.get(
    "/simulations/{run_id}",
    response_model=SimulationRunSchema,
    summary="Get simulation run",
)
async def get_simulation(
    run_id: UUID,
    db: DB,
    copilot: CopilotDep,
) -> SimulationRunSchema:
    """Get a simulation run by ID."""
    service = StressTestingService(db=db, copilot_client=copilot)
    run = await service.get_simulation(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation not found")
    return _run_to_schema(run)


@router.post(
    "/risk-exposure",
    response_model=RiskExposureSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Calculate risk exposure",
)
async def calculate_risk_exposure(
    request: RiskExposureRequest,
    db: DB,
    copilot: CopilotDep,
) -> RiskExposureSchema:
    """Calculate risk exposure for a regulation."""
    service = StressTestingService(db=db, copilot_client=copilot)
    exposure = await service.calculate_risk_exposure(request.regulation)
    return RiskExposureSchema(
        id=str(exposure.id),
        regulation=exposure.regulation,
        exposure_amount=exposure.exposure_amount,
        probability=exposure.probability,
        expected_loss=exposure.expected_loss,
        risk_tier=exposure.risk_tier.value,
        mitigations=exposure.mitigations,
    )


@router.get(
    "/report",
    response_model=StressTestReportSchema,
    summary="Generate stress test report",
)
async def get_report(
    db: DB,
    copilot: CopilotDep,
) -> StressTestReportSchema:
    """Generate an aggregate stress test report."""
    service = StressTestingService(db=db, copilot_client=copilot)
    report = await service.generate_report()
    return StressTestReportSchema(
        id=str(report.id),
        total_scenarios=report.total_scenarios,
        total_simulations=report.total_simulations,
        aggregate_exposure=report.aggregate_exposure,
        risk_exposures=[
            RiskExposureSchema(
                id=str(e.id),
                regulation=e.regulation,
                exposure_amount=e.exposure_amount,
                probability=e.probability,
                expected_loss=e.expected_loss,
                risk_tier=e.risk_tier.value,
                mitigations=e.mitigations,
            )
            for e in report.risk_exposures
        ],
        worst_case_scenario=report.worst_case_scenario,
        recommendations=report.recommendations,
        generated_at=report.generated_at.isoformat() if report.generated_at else None,
    )


def _run_to_schema(run: SimulationRun) -> SimulationRunSchema:
    """Convert SimulationRun to schema."""
    return SimulationRunSchema(
        id=str(run.id),
        scenario_id=str(run.scenario_id),
        iterations=run.iterations,
        confidence_level=run.confidence_level,
        status=run.status,
        results=[
            SimulationResultSchema(
                id=str(r.id),
                run_id=str(r.run_id),
                metric=r.metric,
                p50=r.p50,
                p95=r.p95,
                p99=r.p99,
                mean=r.mean,
                std_dev=r.std_dev,
                distribution=r.distribution,
            )
            for r in run.results
        ],
        started_at=run.started_at.isoformat() if run.started_at else None,
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
    )
