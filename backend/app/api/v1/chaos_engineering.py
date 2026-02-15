"""API endpoints for Compliance Chaos Engineering."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.services.chaos_engineering import (
    ChaosEngineeringService,
    ExperimentStatus,
    ExperimentType,
)

logger = structlog.get_logger()
router = APIRouter()


# --- Request/Response Models ---

class CreateExperimentRequest(BaseModel):
    name: str = Field(..., description="Experiment name")
    description: str = Field(..., description="Experiment description")
    experiment_type: str = Field(..., description="Type of chaos experiment")
    target_service: str = Field(..., description="Target service name")
    target_environment: str = Field("staging", description="Target environment (never production)")


class ExperimentSchema(BaseModel):
    id: str
    name: str
    description: str
    experiment_type: str
    status: str
    target_service: str
    target_environment: str
    blast_radius: str
    affected_frameworks: list[str]
    time_to_detect_seconds: float | None
    time_to_remediate_seconds: float | None
    detection_method: str
    auto_rollback: bool


class GameDaySchema(BaseModel):
    id: str
    name: str
    description: str
    total_experiments: int
    experiments_detected: int
    team_readiness_score: float
    avg_detection_time_seconds: float
    avg_remediation_time_seconds: float


class ChaosStatsSchema(BaseModel):
    total_experiments: int
    experiments_detected: int
    experiments_undetected: int
    avg_mttd_seconds: float
    avg_mttr_seconds: float
    detection_rate: float
    game_days_completed: int
    controls_validated: int
    blind_spots_found: int


# --- Endpoints ---

@router.get("/experiments", response_model=list[ExperimentSchema])
async def list_experiments(
    exp_status: str | None = Query(None, alias="status"),
) -> list[dict]:
    svc = ChaosEngineeringService()
    try:
        st = ExperimentStatus(exp_status) if exp_status else None
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid status: {exp_status}")
    experiments = await svc.list_experiments(status=st)
    return [
        {"id": str(e.id), "name": e.name, "description": e.description,
         "experiment_type": e.experiment_type.value, "status": e.status.value,
         "target_service": e.target_service, "target_environment": e.target_environment,
         "blast_radius": e.blast_radius, "affected_frameworks": e.affected_frameworks,
         "time_to_detect_seconds": e.time_to_detect_seconds,
         "time_to_remediate_seconds": e.time_to_remediate_seconds,
         "detection_method": e.detection_method, "auto_rollback": e.auto_rollback}
        for e in experiments
    ]


@router.post("/experiments", response_model=ExperimentSchema, status_code=status.HTTP_201_CREATED)
async def create_experiment(req: CreateExperimentRequest) -> dict:
    svc = ChaosEngineeringService()
    try:
        experiment_type = ExperimentType(req.experiment_type)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid experiment_type: {req.experiment_type}")
    e = await svc.create_experiment(
        name=req.name, description=req.description,
        experiment_type=experiment_type,
        target_service=req.target_service,
        target_environment=req.target_environment,
    )
    return {
        "id": str(e.id), "name": e.name, "description": e.description,
        "experiment_type": e.experiment_type.value, "status": e.status.value,
        "target_service": e.target_service, "target_environment": e.target_environment,
        "blast_radius": e.blast_radius, "affected_frameworks": e.affected_frameworks,
        "time_to_detect_seconds": e.time_to_detect_seconds,
        "time_to_remediate_seconds": e.time_to_remediate_seconds,
        "detection_method": e.detection_method, "auto_rollback": e.auto_rollback,
    }


@router.post("/experiments/{experiment_id}/run", response_model=ExperimentSchema)
async def run_experiment(experiment_id: UUID) -> dict:
    svc = ChaosEngineeringService()
    try:
        e = await svc.run_experiment(experiment_id)
    except ValueError as e_err:
        raise HTTPException(status_code=400, detail=str(e_err))
    if not e:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {
        "id": str(e.id), "name": e.name, "description": e.description,
        "experiment_type": e.experiment_type.value, "status": e.status.value,
        "target_service": e.target_service, "target_environment": e.target_environment,
        "blast_radius": e.blast_radius, "affected_frameworks": e.affected_frameworks,
        "time_to_detect_seconds": e.time_to_detect_seconds,
        "time_to_remediate_seconds": e.time_to_remediate_seconds,
        "detection_method": e.detection_method, "auto_rollback": e.auto_rollback,
    }


@router.get("/game-days", response_model=list[GameDaySchema])
async def list_game_days() -> list[dict]:
    svc = ChaosEngineeringService()
    days = await svc.list_game_days()
    return [
        {"id": str(d.id), "name": d.name, "description": d.description,
         "total_experiments": d.total_experiments, "experiments_detected": d.experiments_detected,
         "team_readiness_score": d.team_readiness_score,
         "avg_detection_time_seconds": d.avg_detection_time_seconds,
         "avg_remediation_time_seconds": d.avg_remediation_time_seconds}
        for d in days
    ]


@router.get("/stats", response_model=ChaosStatsSchema)
async def get_stats() -> dict:
    svc = ChaosEngineeringService()
    s = await svc.get_stats()
    return {
        "total_experiments": s.total_experiments, "experiments_detected": s.experiments_detected,
        "experiments_undetected": s.experiments_undetected,
        "avg_mttd_seconds": s.avg_mttd_seconds, "avg_mttr_seconds": s.avg_mttr_seconds,
        "detection_rate": s.detection_rate, "game_days_completed": s.game_days_completed,
        "controls_validated": s.controls_validated, "blind_spots_found": s.blind_spots_found,
    }
