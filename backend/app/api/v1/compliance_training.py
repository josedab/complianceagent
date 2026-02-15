"""API endpoints for Continuous Compliance Training Copilot."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.compliance_training import (
    ComplianceTrainingService,
    SkillLevel,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class TriggerTrainingRequest(BaseModel):
    """Request to trigger training."""

    developer_id: str = Field(..., description="Developer identifier")
    violation_type: str = Field(..., description="Type of violation")
    regulation: str = Field(..., description="Regulation identifier")


class CompleteTrainingRequest(BaseModel):
    """Request to complete training."""

    quiz_score: float = Field(..., ge=0.0, le=100.0, description="Quiz score percentage")


class TrainingModuleSchema(BaseModel):
    """Training module response."""

    id: str
    title: str
    regulation: str
    topic: str
    format: str
    content: str
    quiz_questions: list[dict[str, Any]]
    duration_minutes: int
    skill_level: str
    tags: list[str]
    created_at: str | None


class DeveloperProfileSchema(BaseModel):
    """Developer profile response."""

    id: str
    developer_id: str
    name: str
    skill_level: str
    completed_modules: list[str]
    quiz_scores: dict[str, float]
    violations_triggered: int
    last_violation_at: str | None
    compliance_score: float
    strengths: list[str]
    weaknesses: list[str]


class TrainingAssignmentSchema(BaseModel):
    """Training assignment response."""

    id: str
    developer_id: str
    module_id: str
    trigger: str
    assigned_at: str | None
    completed_at: str | None
    quiz_score: float | None
    status: str


class TeamReportSchema(BaseModel):
    """Team report response."""

    team: str
    total_developers: int
    avg_score: float
    modules_completed: int
    violation_reduction_pct: float
    skill_distribution: dict[str, Any]
    top_gaps: list[str]
    generated_at: str | None


# --- Helpers ---


def _assignment_to_schema(a) -> TrainingAssignmentSchema:
    return TrainingAssignmentSchema(
        id=str(a.id),
        developer_id=a.developer_id,
        module_id=str(a.module_id),
        trigger=a.trigger.value,
        assigned_at=a.assigned_at.isoformat() if a.assigned_at else None,
        completed_at=a.completed_at.isoformat() if a.completed_at else None,
        quiz_score=a.quiz_score,
        status=a.status,
    )


def _profile_to_schema(p) -> DeveloperProfileSchema:
    return DeveloperProfileSchema(
        id=str(p.id),
        developer_id=p.developer_id,
        name=p.name,
        skill_level=p.skill_level.value,
        completed_modules=p.completed_modules,
        quiz_scores=p.quiz_scores,
        violations_triggered=p.violations_triggered,
        last_violation_at=p.last_violation_at.isoformat() if p.last_violation_at else None,
        compliance_score=p.compliance_score,
        strengths=p.strengths,
        weaknesses=p.weaknesses,
    )


# --- Endpoints ---


@router.post(
    "/trigger",
    response_model=TrainingAssignmentSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger compliance training",
)
async def trigger_training(
    request: TriggerTrainingRequest,
    db: DB,
    copilot: CopilotDep,
) -> TrainingAssignmentSchema:
    """Trigger training for a developer based on a violation."""
    service = ComplianceTrainingService(db=db, copilot_client=copilot)
    assignment = await service.trigger_training(
        developer_id=request.developer_id,
        violation_type=request.violation_type,
        regulation=request.regulation,
    )
    return _assignment_to_schema(assignment)


@router.get(
    "/profile/{developer_id}",
    response_model=DeveloperProfileSchema,
    summary="Get developer profile",
)
async def get_developer_profile(
    developer_id: str,
    db: DB,
    copilot: CopilotDep,
) -> DeveloperProfileSchema:
    """Get a developer's compliance training profile."""
    service = ComplianceTrainingService(db=db, copilot_client=copilot)
    profile = await service.get_developer_profile(developer_id)
    return _profile_to_schema(profile)


@router.get(
    "/modules",
    response_model=list[TrainingModuleSchema],
    summary="List training modules",
)
async def list_modules(
    db: DB,
    copilot: CopilotDep,
    regulation: str | None = None,
    level: str | None = None,
) -> list[TrainingModuleSchema]:
    """List training modules with optional filters."""
    service = ComplianceTrainingService(db=db, copilot_client=copilot)
    sl = SkillLevel(level) if level else None
    modules = await service.list_modules(regulation=regulation, level=sl)
    return [
        TrainingModuleSchema(
            id=str(m.id),
            title=m.title,
            regulation=m.regulation,
            topic=m.topic,
            format=m.format.value,
            content=m.content,
            quiz_questions=m.quiz_questions,
            duration_minutes=m.duration_minutes,
            skill_level=m.skill_level.value,
            tags=m.tags,
            created_at=m.created_at.isoformat() if m.created_at else None,
        )
        for m in modules
    ]


@router.post(
    "/assignments/{assignment_id}/complete",
    response_model=TrainingAssignmentSchema,
    summary="Complete training assignment",
)
async def complete_training(
    assignment_id: UUID,
    request: CompleteTrainingRequest,
    db: DB,
    copilot: CopilotDep,
) -> TrainingAssignmentSchema:
    """Complete a training assignment with quiz score."""
    service = ComplianceTrainingService(db=db, copilot_client=copilot)
    assignment = await service.complete_training(assignment_id, quiz_score=request.quiz_score)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    return _assignment_to_schema(assignment)


@router.get(
    "/team-report/{team}",
    response_model=TeamReportSchema,
    summary="Get team training report",
)
async def get_team_report(
    team: str,
    db: DB,
    copilot: CopilotDep,
) -> TeamReportSchema:
    """Generate a team compliance training report."""
    service = ComplianceTrainingService(db=db, copilot_client=copilot)
    report = await service.get_team_report(team)
    return TeamReportSchema(
        team=report.team,
        total_developers=report.total_developers,
        avg_score=report.avg_score,
        modules_completed=report.modules_completed,
        violation_reduction_pct=report.violation_reduction_pct,
        skill_distribution=report.skill_distribution,
        top_gaps=report.top_gaps,
        generated_at=report.generated_at.isoformat() if report.generated_at else None,
    )


@router.get(
    "/assignments",
    response_model=list[TrainingAssignmentSchema],
    summary="List training assignments",
)
async def list_assignments(
    db: DB,
    copilot: CopilotDep,
    developer_id: str | None = None,
    status_filter: str | None = None,
) -> list[TrainingAssignmentSchema]:
    """List training assignments with optional filters."""
    service = ComplianceTrainingService(db=db, copilot_client=copilot)
    assignments = await service.list_assignments(developer_id=developer_id, status=status_filter)
    return [_assignment_to_schema(a) for a in assignments]


@router.get(
    "/leaderboard",
    response_model=list[DeveloperProfileSchema],
    summary="Get training leaderboard",
)
async def get_leaderboard(
    db: DB,
    copilot: CopilotDep,
    limit: int = 10,
) -> list[DeveloperProfileSchema]:
    """Get top developers by compliance score."""
    service = ComplianceTrainingService(db=db, copilot_client=copilot)
    profiles = await service.get_leaderboard(limit=limit)
    return [_profile_to_schema(p) for p in profiles]
