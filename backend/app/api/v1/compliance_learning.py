"""API endpoints for Compliance Learning Hub."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB


logger = structlog.get_logger()
router = APIRouter()


def _serialize(obj):
    """Convert a dataclass to a JSON-serializable dict."""
    from dataclasses import fields, is_dataclass

    if not is_dataclass(obj):
        return obj

    result = {}
    for f in fields(obj):
        v = getattr(obj, f.name)
        result[f.name] = _ser_val(v)
    return result


def _ser_val(v):
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


class LearningModuleResponse(BaseModel):
    model_config = {"extra": "ignore"}
    id: UUID | None = None
    title: str = ""
    description: str = ""
    duration_minutes: int = 0
    difficulty: str = ""
    content_type: str = ""
    content: dict[str, Any] = Field(default_factory=dict)


class LearningPathResponse(BaseModel):
    model_config = {"extra": "ignore"}
    id: UUID | None = None
    name: str = ""
    description: str = ""
    framework: str = ""
    modules: list[LearningModuleResponse] = Field(default_factory=list)
    total_duration_minutes: int = 0
    difficulty: str = ""


class LearningPathListResponse(BaseModel):
    model_config = {"extra": "ignore"}
    paths: list[LearningPathResponse] = Field(default_factory=list)
    total: int = 0


class QuizSubmitRequest(BaseModel):
    question_id: UUID = Field(..., description="ID of the quiz question")
    answer: str = Field(..., description="The submitted answer")


class QuizResultResponse(BaseModel):
    model_config = {"extra": "ignore"}
    question_id: UUID | None = None
    correct: bool = False
    correct_answer: str | None = None
    explanation: str | None = None
    score: float = 0.0


class TeamMemberProgress(BaseModel):
    member_name: str
    paths_completed: int
    modules_completed: int
    quiz_score_avg: float
    total_hours: float


class TeamProgressResponse(BaseModel):
    model_config = {"extra": "ignore"}
    total_members: int = 0
    avg_completion: float = 0.0
    avg_quiz_score: float = 0.0
    members: list[TeamMemberProgress] = Field(default_factory=list)


class PersonalizeRequest(BaseModel):
    frameworks: list[str] = Field(..., description="Compliance frameworks of interest")
    role: str = Field(..., description="Team role (e.g. 'developer', 'manager', 'auditor')")


class PersonalizedPathResponse(BaseModel):
    model_config = {"extra": "ignore"}
    path: LearningPathResponse | None = None
    reason: str = ""
    estimated_hours: float = 0.0
    priority_modules: list[str] = Field(default_factory=list)


# --- Endpoints ---


@router.get("/paths", response_model=LearningPathListResponse, summary="List learning paths")
async def list_learning_paths(db: DB) -> LearningPathListResponse:
    """List all available compliance learning paths."""
    from app.services.compliance_training.learning import ComplianceLearningService

    service = ComplianceLearningService(db=db)
    paths = await service.get_learning_paths()
    return LearningPathListResponse(
        paths=[LearningPathResponse(**_serialize(p)) for p in paths],
        total=len(paths),
    )


@router.get(
    "/paths/{path_id}", response_model=LearningPathResponse, summary="Get learning path details"
)
async def get_learning_path(path_id: UUID, db: DB) -> LearningPathResponse:
    """Get details of a specific learning path."""
    from app.services.compliance_training.learning import ComplianceLearningService

    service = ComplianceLearningService(db=db)
    path = await service.get_path(path_id=path_id)
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning path not found")
    return LearningPathResponse(**_serialize(path))


@router.get(
    "/modules/{module_id}", response_model=LearningModuleResponse, summary="Get module content"
)
async def get_module(module_id: UUID, db: DB) -> LearningModuleResponse:
    """Get the content of a specific learning module."""
    from app.services.compliance_training.learning import ComplianceLearningService

    service = ComplianceLearningService(db=db)
    module = await service.get_module(module_id=module_id)
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    return LearningModuleResponse(**_serialize(module))


@router.post("/quiz/submit", response_model=QuizResultResponse, summary="Submit a quiz answer")
async def submit_quiz_answer(request: QuizSubmitRequest, db: DB) -> QuizResultResponse:
    """Submit an answer to a quiz question."""
    from app.services.compliance_training.learning import ComplianceLearningService

    service = ComplianceLearningService(db=db)
    result = await service.submit_quiz_answer(
        question_id=request.question_id,
        answer=request.answer,
    )
    return QuizResultResponse(**_serialize(result))


@router.get("/team-progress", response_model=TeamProgressResponse, summary="Get team progress")
async def get_team_progress(db: DB) -> TeamProgressResponse:
    """Get the learning progress for the team."""
    from app.services.compliance_training.learning import ComplianceLearningService

    service = ComplianceLearningService(db=db)
    progress = await service.get_team_progress(team="default")
    return TeamProgressResponse(**_serialize(progress))


@router.post(
    "/personalize",
    response_model=PersonalizedPathResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate personalized learning path",
)
async def personalize_path(request: PersonalizeRequest, db: DB) -> PersonalizedPathResponse:
    """Generate a personalized learning path based on frameworks and role."""
    from app.services.compliance_training.learning import ComplianceLearningService

    service = ComplianceLearningService(db=db)
    result = await service.generate_personalized_path(
        frameworks=request.frameworks,
        role=request.role,
    )
    return PersonalizedPathResponse(**_serialize(result))
