"""Compliance training mode API endpoints."""

from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep, CurrentOrganization, OrgMember
from app.services.training import (
    TrainingService,
    CertificateStatus,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---

class ModuleSummarySchema(BaseModel):
    """Training module summary."""
    id: str
    title: str
    description: str
    framework: str
    difficulty: str
    estimated_minutes: int
    section_count: int
    quiz_count: int


class ModuleDetailSchema(ModuleSummarySchema):
    """Detailed training module."""
    learning_objectives: list[str]
    requirements_covered: list[str]
    sections: list[dict]
    prerequisites: list[str]


class ProgressSchema(BaseModel):
    """Training progress response."""
    module_id: str
    progress_percentage: float
    sections_completed: list[int]
    current_section: int
    is_complete: bool
    best_quiz_score: float


class QuizSchema(BaseModel):
    """Quiz for taking."""
    id: str
    title: str
    description: str
    question_count: int
    time_limit_minutes: int | None
    passing_score: float
    attempts_remaining: int


class QuestionSchema(BaseModel):
    """Quiz question."""
    id: str
    question_type: str
    text: str
    code_snippet: str | None = None
    options: list[dict]
    points: int


class SubmitAnswersRequest(BaseModel):
    """Request to submit quiz answers."""
    answers: dict[str, list[int]] = Field(..., description="Question ID to selected option indices")


class QuizResultSchema(BaseModel):
    """Quiz result response."""
    attempt_id: str
    score: float
    passed: bool
    questions: list[dict]


class CertificateSchema(BaseModel):
    """Certificate response."""
    id: str
    title: str
    framework: str
    issued_at: str
    expires_at: str
    status: str
    score: float
    verification_code: str


class UserProfileSchema(BaseModel):
    """User training profile."""
    total_modules_completed: int
    total_training_hours: float
    certificates: list[CertificateSchema]
    streak_days: int
    framework_scores: dict[str, float]


# --- Helper Functions ---

def _module_to_summary(module, module_id: UUID) -> ModuleSummarySchema:
    return ModuleSummarySchema(
        id=str(module_id),
        title=module.title,
        description=module.description,
        framework=module.framework,
        difficulty=module.difficulty,
        estimated_minutes=module.estimated_minutes,
        section_count=len(module.sections),
        quiz_count=len(module.quizzes),
    )


def _cert_to_schema(cert) -> CertificateSchema:
    return CertificateSchema(
        id=str(cert.id),
        title=cert.title,
        framework=cert.framework,
        issued_at=cert.issued_at.isoformat(),
        expires_at=cert.expires_at.isoformat(),
        status=cert.status.value,
        score=cert.score,
        verification_code=cert.verification_code,
    )


# --- Module Endpoints ---

@router.get(
    "/modules",
    response_model=list[ModuleSummarySchema],
    summary="List training modules",
    description="Get available compliance training modules",
)
async def list_modules(
    db: DB,
    copilot: CopilotDep,
    framework: str | None = None,
    difficulty: str | None = None,
) -> list[ModuleSummarySchema]:
    """List available training modules."""
    service = TrainingService(db=db, copilot=copilot)
    modules = await service.list_modules(framework=framework, difficulty=difficulty)
    
    # Get IDs from internal storage
    result = []
    for module_id, module in service._modules.items():
        if (not framework or module.framework == framework) and \
           (not difficulty or module.difficulty == difficulty):
            result.append(_module_to_summary(module, module_id))
    
    return result


@router.get(
    "/modules/{module_id}",
    response_model=ModuleDetailSchema,
    summary="Get training module",
    description="Get detailed information about a training module",
)
async def get_module(
    module_id: str,
    db: DB,
    copilot: CopilotDep,
) -> ModuleDetailSchema:
    """Get module details."""
    service = TrainingService(db=db, copilot=copilot)
    module = await service.get_module(UUID(module_id))
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found",
        )
    
    return ModuleDetailSchema(
        id=module_id,
        title=module.title,
        description=module.description,
        framework=module.framework,
        difficulty=module.difficulty,
        estimated_minutes=module.estimated_minutes,
        section_count=len(module.sections),
        quiz_count=len(module.quizzes),
        learning_objectives=module.learning_objectives,
        requirements_covered=module.requirements_covered,
        sections=module.sections,
        prerequisites=[str(p) for p in module.prerequisites],
    )


# --- Progress Endpoints ---

@router.post(
    "/modules/{module_id}/enroll",
    response_model=ProgressSchema,
    summary="Enroll in module",
    description="Enroll in a training module",
)
async def enroll_in_module(
    module_id: str,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> ProgressSchema:
    """Enroll in a training module."""
    service = TrainingService(db=db, copilot=copilot)
    
    try:
        progress = await service.enroll(member.user_id, UUID(module_id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    
    return ProgressSchema(
        module_id=module_id,
        progress_percentage=progress.progress_percentage,
        sections_completed=progress.sections_completed,
        current_section=progress.current_section,
        is_complete=progress.is_complete,
        best_quiz_score=progress.best_quiz_score,
    )


@router.get(
    "/modules/{module_id}/progress",
    response_model=ProgressSchema,
    summary="Get progress",
    description="Get your progress in a module",
)
async def get_progress(
    module_id: str,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> ProgressSchema:
    """Get progress in a module."""
    service = TrainingService(db=db, copilot=copilot)
    progress = await service.get_progress(member.user_id, UUID(module_id))
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not enrolled in this module",
        )
    
    return ProgressSchema(
        module_id=module_id,
        progress_percentage=progress.progress_percentage,
        sections_completed=progress.sections_completed,
        current_section=progress.current_section,
        is_complete=progress.is_complete,
        best_quiz_score=progress.best_quiz_score,
    )


@router.post(
    "/modules/{module_id}/sections/{section_index}/complete",
    response_model=ProgressSchema,
    summary="Complete section",
    description="Mark a section as complete",
)
async def complete_section(
    module_id: str,
    section_index: int,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> ProgressSchema:
    """Mark a section as complete."""
    service = TrainingService(db=db, copilot=copilot)
    
    progress = await service.update_progress(
        member.user_id,
        UUID(module_id),
        section_index,
    )
    
    return ProgressSchema(
        module_id=module_id,
        progress_percentage=progress.progress_percentage,
        sections_completed=progress.sections_completed,
        current_section=progress.current_section,
        is_complete=progress.is_complete,
        best_quiz_score=progress.best_quiz_score,
    )


# --- Quiz Endpoints ---

@router.get(
    "/modules/{module_id}/quizzes/{quiz_index}",
    response_model=QuizSchema,
    summary="Get quiz",
    description="Get quiz information before starting",
)
async def get_quiz(
    module_id: str,
    quiz_index: int,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> QuizSchema:
    """Get quiz information."""
    service = TrainingService(db=db, copilot=copilot)
    module = await service.get_module(UUID(module_id))
    
    if not module or quiz_index >= len(module.quizzes):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )
    
    quiz = module.quizzes[quiz_index]
    
    # Calculate remaining attempts
    progress = await service.get_progress(member.user_id, UUID(module_id))
    attempts_used = 0
    if progress:
        attempts_used = len([
            a for a in progress.quiz_attempts
            if a.quiz_id == quiz.id
        ])
    
    return QuizSchema(
        id=str(quiz.id),
        title=quiz.title,
        description=quiz.description,
        question_count=len(quiz.questions),
        time_limit_minutes=quiz.time_limit_minutes,
        passing_score=quiz.passing_score,
        attempts_remaining=quiz.max_attempts - attempts_used,
    )


@router.post(
    "/modules/{module_id}/quizzes/{quiz_index}/start",
    summary="Start quiz",
    description="Start a quiz attempt and get questions",
)
async def start_quiz(
    module_id: str,
    quiz_index: int,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> dict:
    """Start a quiz and get questions."""
    service = TrainingService(db=db, copilot=copilot)
    
    try:
        attempt = await service.start_quiz(
            member.user_id,
            UUID(module_id),
            quiz_index,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    module = await service.get_module(UUID(module_id))
    quiz = module.quizzes[quiz_index]
    
    questions = [
        QuestionSchema(
            id=str(q.id),
            question_type=q.question_type.value,
            text=q.text,
            code_snippet=q.code_snippet,
            options=q.options,
            points=q.points,
        )
        for q in quiz.questions
    ]
    
    return {
        "attempt_id": str(attempt.id),
        "quiz_id": str(quiz.id),
        "time_limit_minutes": quiz.time_limit_minutes,
        "questions": [q.dict() for q in questions],
    }


@router.post(
    "/modules/{module_id}/quizzes/{quiz_index}/submit",
    response_model=QuizResultSchema,
    summary="Submit quiz",
    description="Submit quiz answers and get results",
)
async def submit_quiz(
    module_id: str,
    quiz_index: int,
    request: SubmitAnswersRequest,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> QuizResultSchema:
    """Submit quiz answers."""
    service = TrainingService(db=db, copilot=copilot)
    
    attempt = await service.submit_quiz(
        member.user_id,
        UUID(module_id),
        quiz_index,
        request.answers,
    )
    
    results = await service.get_quiz_results(
        member.user_id,
        UUID(module_id),
        quiz_index,
        attempt.id,
    )
    
    return QuizResultSchema(
        attempt_id=str(attempt.id),
        score=attempt.score,
        passed=attempt.passed,
        questions=results["questions"],
    )


# --- Certificate Endpoints ---

@router.get(
    "/certificates",
    response_model=list[CertificateSchema],
    summary="List certificates",
    description="Get your certificates",
)
async def list_certificates(
    member: OrgMember,
    organization: CurrentOrganization,
    db: DB,
    copilot: CopilotDep,
) -> list[CertificateSchema]:
    """List user's certificates."""
    service = TrainingService(db=db, copilot=copilot)
    certs = await service.list_certificates(user_id=member.user_id)
    return [_cert_to_schema(c) for c in certs]


@router.get(
    "/certificates/verify/{code}",
    summary="Verify certificate",
    description="Verify a certificate by its code",
)
async def verify_certificate(
    code: str,
    db: DB,
    copilot: CopilotDep,
) -> dict:
    """Verify a certificate."""
    service = TrainingService(db=db, copilot=copilot)
    cert = await service.verify_certificate(code)
    
    if not cert:
        return {"valid": False, "message": "Certificate not found"}
    
    if cert.status == CertificateStatus.EXPIRED:
        return {"valid": False, "message": "Certificate has expired"}
    
    if cert.status == CertificateStatus.REVOKED:
        return {"valid": False, "message": "Certificate has been revoked"}
    
    return {
        "valid": True,
        "certificate": _cert_to_schema(cert).dict(),
    }


# --- Profile Endpoints ---

@router.get(
    "/profile",
    response_model=UserProfileSchema,
    summary="Get training profile",
    description="Get your training profile and progress",
)
async def get_training_profile(
    member: OrgMember,
    organization: CurrentOrganization,
    db: DB,
    copilot: CopilotDep,
) -> UserProfileSchema:
    """Get user's training profile."""
    service = TrainingService(db=db, copilot=copilot)
    profile = await service.get_user_profile(
        member.user_id,
        organization.id,
    )
    
    return UserProfileSchema(
        total_modules_completed=profile.total_modules_completed,
        total_training_hours=profile.total_training_hours,
        certificates=[_cert_to_schema(c) for c in profile.certificates],
        streak_days=profile.streak_days,
        framework_scores=profile.framework_scores,
    )


# --- Admin Endpoints ---

@router.post(
    "/generate-quiz",
    summary="Generate quiz",
    description="Generate a quiz using AI (admin only)",
)
async def generate_quiz(
    framework: str,
    topics: list[str],
    num_questions: int = 10,
    difficulty: str = "medium",
    db: DB = None,
    copilot: CopilotDep = None,
) -> dict:
    """Generate a quiz using AI."""
    service = TrainingService(db=db, copilot=copilot)
    quiz = await service.generate_quiz(
        framework=framework,
        topics=topics,
        num_questions=num_questions,
        difficulty=difficulty,
    )
    
    return {
        "id": str(quiz.id),
        "title": quiz.title,
        "question_count": len(quiz.questions),
    }
