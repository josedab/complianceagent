"""API endpoints for Training Simulator."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.training_simulator import TrainingSimulatorService


logger = structlog.get_logger()
router = APIRouter()


class SessionStartRequest(BaseModel):
    user_id: str = Field(...)
    scenario_id: str = Field(...)


class TraineeResponseRequest(BaseModel):
    step_index: int = Field(...)
    response: str = Field(...)


@router.get("/scenarios", summary="List training scenarios")
async def list_scenarios(
    db: DB,
    category: str | None = None,
    difficulty: str | None = None,
) -> list[dict]:
    """List training scenarios with optional filters."""
    service = TrainingSimulatorService(db=db)
    scenarios = await service.list_scenarios(
        category=category,
        difficulty=difficulty,
    )
    return [
        {
            "id": s.id,
            "title": s.title,
            "category": s.category.value,
            "difficulty": s.difficulty.value,
            "description": s.description,
            "time_limit_minutes": s.time_limit_minutes,
            "steps": len(s.steps),
            "passing_score": s.passing_score,
        }
        for s in scenarios
    ]


@router.post("/sessions", status_code=status.HTTP_201_CREATED, summary="Start simulation")
async def start_session(request: SessionStartRequest, db: DB) -> dict:
    """Start a new simulation session."""
    service = TrainingSimulatorService(db=db)
    try:
        result = await service.start_simulation(
            user_id=request.user_id,
            scenario_id=request.scenario_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return {
        "id": str(result.id),
        "user_id": result.user_id,
        "scenario_id": result.scenario_id,
        "status": result.status.value,
        "current_step": result.current_step,
        "score": result.score,
        "started_at": result.started_at.isoformat() if result.started_at else None,
    }


@router.post("/sessions/{session_id}/respond", summary="Submit response")
async def submit_response(session_id: UUID, request: TraineeResponseRequest, db: DB) -> dict:
    """Submit a response for a simulation step."""
    service = TrainingSimulatorService(db=db)
    try:
        result = await service.submit_response(
            session_id=session_id,
            step_index=request.step_index,
            response=request.response,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return {
        "id": str(result.id),
        "status": result.status.value,
        "current_step": result.current_step,
        "score": result.score,
        "time_elapsed_seconds": result.time_elapsed_seconds,
    }


@router.post("/sessions/{session_id}/complete", summary="Complete simulation")
async def complete_session(session_id: UUID, db: DB) -> dict:
    """Complete a simulation and optionally issue a certificate."""
    service = TrainingSimulatorService(db=db)
    try:
        result = await service.complete_simulation(session_id=session_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    # Result can be SimulationSession or TrainingCertificate
    if hasattr(result, "valid_until"):
        return {
            "type": "certificate",
            "id": str(result.id),
            "user_id": result.user_id,
            "scenario_id": result.scenario_id,
            "score": result.score,
            "issued_at": result.issued_at.isoformat() if result.issued_at else None,
            "valid_until": result.valid_until.isoformat() if result.valid_until else None,
        }
    return {
        "type": "session",
        "id": str(result.id),
        "status": result.status.value,
        "score": result.score,
    }


@router.get("/sessions/{session_id}", summary="Get session")
async def get_session(session_id: UUID, db: DB) -> dict:
    """Get a simulation session by ID."""
    service = TrainingSimulatorService(db=db)
    result = await service.get_session(session_id=session_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    return {
        "id": str(result.id),
        "user_id": result.user_id,
        "scenario_id": result.scenario_id,
        "status": result.status.value,
        "current_step": result.current_step,
        "score": result.score,
        "time_elapsed_seconds": result.time_elapsed_seconds,
        "started_at": result.started_at.isoformat() if result.started_at else None,
        "completed_at": result.completed_at.isoformat() if result.completed_at else None,
    }


@router.get("/stats", summary="Get stats")
async def get_stats(db: DB) -> dict:
    """Get training simulator statistics."""
    service = TrainingSimulatorService(db=db)
    stats = await service.get_stats()
    return {
        "total_sessions": stats.total_sessions,
        "completed": stats.completed,
        "pass_rate": stats.pass_rate,
        "avg_score": stats.avg_score,
        "by_category": stats.by_category,
        "certificates_issued": stats.certificates_issued,
    }
