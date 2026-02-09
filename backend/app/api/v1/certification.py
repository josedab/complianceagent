"""AI Compliance Training Certification Program API endpoints."""

from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep, OrgMember
from app.services.certification import (
    CertificateStatus,
    CertificationService,
)


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---

class QuestionSchema(BaseModel):
    """Quiz question (without correct answer)."""
    id: str
    type: str
    question_text: str
    options: list[str]
    code_snippet: str | None = None
    points: int


class ModuleSchema(BaseModel):
    """Course module summary."""
    id: str
    title: str
    type: str
    order: int
    duration_minutes: int
    question_count: int
    passing_score: float


class CourseSummarySchema(BaseModel):
    """Course listing summary."""
    id: str
    title: str
    description: str
    regulation: str
    level: str
    estimated_hours: float
    module_count: int
    is_free: bool
    enrolled_count: int
    completion_rate: float
    rating: float


class CourseDetailSchema(CourseSummarySchema):
    """Full course details."""
    modules: list[ModuleSchema]
    prerequisites: list[str]
    learning_objectives: list[str]


class EnrollmentSchema(BaseModel):
    """Enrollment response."""
    id: str
    course_id: str
    started_at: str
    progress_pct: float
    current_module: str
    completed_modules: list[str]
    quiz_scores: dict[str, float]
    status: str


class CertificateSchema(BaseModel):
    """Certificate response."""
    id: str
    course_id: str
    certificate_number: str
    issued_at: str
    expires_at: str
    status: str
    score: float
    verification_url: str
    credential_id: str


class TutorQuestionRequest(BaseModel):
    """Request to ask the AI tutor."""
    module_id: str
    question: str = Field(..., description="Question for the AI tutor")


class TutorResponseSchema(BaseModel):
    """AI tutor response."""
    id: str
    question: str
    answer: str
    context: str
    created_at: str


class QuizSubmitRequest(BaseModel):
    """Request to submit quiz answers."""
    answers: list[dict] = Field(..., description="List of {question_id, answer}")


class ExamSubmitRequest(BaseModel):
    """Request to submit final exam answers."""
    answers: list[dict] = Field(..., description="List of {question_id, answer}")


class ModuleCompleteRequest(BaseModel):
    """Request to complete a module."""
    answers: dict = Field(default_factory=dict, description="Optional answers for the module")


class LearningPathSchema(BaseModel):
    """Learning path response."""
    id: str
    title: str
    description: str
    courses: list[str]
    estimated_hours: float
    target_role: str


class CourseProgressSchema(BaseModel):
    """Course progress response."""
    modules_completed: int
    total_modules: int
    avg_quiz_score: float
    time_spent_minutes: int
    last_activity: str


# --- Helper Functions ---

def _course_to_summary(course) -> CourseSummarySchema:
    return CourseSummarySchema(
        id=str(course.id),
        title=course.title,
        description=course.description,
        regulation=course.regulation,
        level=course.level.value,
        estimated_hours=course.estimated_hours,
        module_count=len(course.modules),
        is_free=course.is_free,
        enrolled_count=course.enrolled_count,
        completion_rate=course.completion_rate,
        rating=course.rating,
    )


def _module_to_schema(module) -> ModuleSchema:
    return ModuleSchema(
        id=str(module.id),
        title=module.title,
        type=module.type.value,
        order=module.order,
        duration_minutes=module.duration_minutes,
        question_count=len(module.questions),
        passing_score=module.passing_score,
    )


def _enrollment_to_schema(enrollment) -> EnrollmentSchema:
    return EnrollmentSchema(
        id=str(enrollment.id),
        course_id=str(enrollment.course_id),
        started_at=enrollment.started_at.isoformat(),
        progress_pct=enrollment.progress_pct,
        current_module=enrollment.current_module,
        completed_modules=enrollment.completed_modules,
        quiz_scores=enrollment.quiz_scores,
        status=enrollment.status.value,
    )


def _cert_to_schema(cert) -> CertificateSchema:
    return CertificateSchema(
        id=str(cert.id),
        course_id=str(cert.course_id),
        certificate_number=cert.certificate_number,
        issued_at=cert.issued_at.isoformat(),
        expires_at=cert.expires_at.isoformat(),
        status=cert.status.value,
        score=cert.score,
        verification_url=cert.verification_url,
        credential_id=cert.credential_id,
    )


# --- Course Endpoints ---

@router.get(
    "/courses",
    response_model=list[CourseSummarySchema],
    summary="List courses",
    description="List available certification courses with optional filtering",
)
async def list_courses(
    db: DB,
    copilot: CopilotDep,
    level: str | None = None,
    regulation: str | None = None,
) -> list[CourseSummarySchema]:
    """List available certification courses."""
    service = CertificationService(db=db, copilot_client=copilot)
    courses = await service.list_courses(level=level, regulation=regulation)
    return [_course_to_summary(c) for c in courses]


@router.get(
    "/courses/{course_id}",
    response_model=CourseDetailSchema,
    summary="Get course details",
    description="Get detailed information about a certification course",
)
async def get_course(
    course_id: str,
    db: DB,
    copilot: CopilotDep,
) -> CourseDetailSchema:
    """Get course details."""
    service = CertificationService(db=db, copilot_client=copilot)
    course = await service.get_course(UUID(course_id))

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    return CourseDetailSchema(
        id=str(course.id),
        title=course.title,
        description=course.description,
        regulation=course.regulation,
        level=course.level.value,
        estimated_hours=course.estimated_hours,
        module_count=len(course.modules),
        is_free=course.is_free,
        enrolled_count=course.enrolled_count,
        completion_rate=course.completion_rate,
        rating=course.rating,
        modules=[_module_to_schema(m) for m in course.modules],
        prerequisites=course.prerequisites,
        learning_objectives=course.learning_objectives,
    )


# --- Enrollment Endpoints ---

@router.post(
    "/courses/{course_id}/enroll",
    response_model=EnrollmentSchema,
    summary="Enroll in course",
    description="Enroll in a certification course",
)
async def enroll_in_course(
    course_id: str,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> EnrollmentSchema:
    """Enroll in a certification course."""
    service = CertificationService(db=db, copilot_client=copilot)

    try:
        enrollment = await service.enroll(member.user_id, UUID(course_id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return _enrollment_to_schema(enrollment)


@router.get(
    "/enrollments",
    response_model=list[EnrollmentSchema],
    summary="List enrollments",
    description="List your course enrollments",
)
async def list_enrollments(
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> list[EnrollmentSchema]:
    """List user's enrollments."""
    service = CertificationService(db=db, copilot_client=copilot)
    enrollments = await service.list_enrollments(member.user_id)
    return [_enrollment_to_schema(e) for e in enrollments]


# --- Module Endpoints ---

@router.post(
    "/courses/{course_id}/modules/{module_id}/complete",
    summary="Complete module",
    description="Mark a course module as complete",
)
async def complete_module(
    course_id: str,
    module_id: str,
    request: ModuleCompleteRequest,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> dict:
    """Complete a course module."""
    service = CertificationService(db=db, copilot_client=copilot)

    try:
        result = await service.complete_module(
            member.user_id,
            UUID(course_id),
            UUID(module_id),
            request.answers,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return result


@router.post(
    "/courses/{course_id}/modules/{module_id}/quiz",
    summary="Submit quiz",
    description="Submit quiz answers for a module",
)
async def submit_quiz(
    course_id: str,
    module_id: str,
    request: QuizSubmitRequest,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> dict:
    """Submit quiz answers."""
    service = CertificationService(db=db, copilot_client=copilot)

    try:
        result = await service.submit_quiz(
            member.user_id,
            UUID(course_id),
            UUID(module_id),
            request.answers,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return result


# --- AI Tutor Endpoints ---

@router.post(
    "/courses/{course_id}/tutor",
    response_model=TutorResponseSchema,
    summary="Ask AI tutor",
    description="Ask the AI compliance tutor a question",
)
async def ask_tutor(
    course_id: str,
    request: TutorQuestionRequest,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> TutorResponseSchema:
    """Ask the AI tutor a question."""
    service = CertificationService(db=db, copilot_client=copilot)

    try:
        conversation = await service.ask_tutor(
            member.user_id,
            UUID(course_id),
            UUID(request.module_id),
            request.question,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return TutorResponseSchema(
        id=str(conversation.id),
        question=conversation.question,
        answer=conversation.answer,
        context=conversation.context,
        created_at=conversation.created_at.isoformat(),
    )


# --- Exam Endpoints ---

@router.post(
    "/courses/{course_id}/exam",
    summary="Take final exam",
    description="Take the final certification exam",
)
async def take_final_exam(
    course_id: str,
    request: ExamSubmitRequest,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> dict:
    """Take the final certification exam."""
    service = CertificationService(db=db, copilot_client=copilot)

    try:
        result = await service.take_final_exam(
            member.user_id,
            UUID(course_id),
            request.answers,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return result


# --- Certificate Endpoints ---

@router.get(
    "/certificates",
    response_model=list[CertificateSchema],
    summary="Get certificates",
    description="Get your certification credentials",
)
async def get_certificates(
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> list[CertificateSchema]:
    """Get user's certificates."""
    service = CertificationService(db=db, copilot_client=copilot)
    certs = await service.get_user_certificates(member.user_id)
    return [_cert_to_schema(c) for c in certs]


@router.get(
    "/certificates/verify/{certificate_number}",
    summary="Verify certificate",
    description="Verify a certificate by its number",
)
async def verify_certificate(
    certificate_number: str,
    db: DB,
    copilot: CopilotDep,
) -> dict:
    """Verify a certificate."""
    service = CertificationService(db=db, copilot_client=copilot)
    cert = await service.verify_certificate(certificate_number)

    if not cert:
        return {"valid": False, "message": "Certificate not found"}

    if cert.status == CertificateStatus.EXPIRED:
        return {"valid": False, "message": "Certificate has expired"}

    return {
        "valid": True,
        "certificate": _cert_to_schema(cert).model_dump(),
    }


# --- Learning Path Endpoints ---

@router.get(
    "/learning-paths",
    response_model=list[LearningPathSchema],
    summary="List learning paths",
    description="Get curated learning paths for different roles",
)
async def list_learning_paths(
    db: DB,
    copilot: CopilotDep,
) -> list[LearningPathSchema]:
    """List available learning paths."""
    service = CertificationService(db=db, copilot_client=copilot)
    paths = await service.get_learning_paths()

    return [
        LearningPathSchema(
            id=str(p.id),
            title=p.title,
            description=p.description,
            courses=p.courses,
            estimated_hours=p.estimated_hours,
            target_role=p.target_role,
        )
        for p in paths
    ]


# --- Progress Endpoints ---

@router.get(
    "/progress/{course_id}",
    response_model=CourseProgressSchema,
    summary="Get course progress",
    description="Get your progress in a course",
)
async def get_course_progress(
    course_id: str,
    member: OrgMember,
    db: DB,
    copilot: CopilotDep,
) -> CourseProgressSchema:
    """Get course progress."""
    service = CertificationService(db=db, copilot_client=copilot)
    progress = await service.get_progress(member.user_id, UUID(course_id))

    return CourseProgressSchema(
        modules_completed=progress.modules_completed,
        total_modules=progress.total_modules,
        avg_quiz_score=progress.avg_quiz_score,
        time_spent_minutes=progress.time_spent_minutes,
        last_activity=progress.last_activity.isoformat(),
    )
