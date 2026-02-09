"""AI Compliance Training Certification Program data models."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4


class CourseLevel(str, Enum):
    """Course difficulty level."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ModuleType(str, Enum):
    """Type of course module."""
    LESSON = "lesson"
    QUIZ = "quiz"
    LAB = "lab"
    ASSESSMENT = "assessment"


class QuestionType(str, Enum):
    """Types of quiz questions."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    CODE_REVIEW = "code_review"
    FILL_IN = "fill_in"


class CertificateStatus(str, Enum):
    """Certificate lifecycle status."""
    IN_PROGRESS = "in_progress"
    EXAM_SCHEDULED = "exam_scheduled"
    PASSED = "passed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class Question:
    """Quiz or assessment question."""
    id: UUID = field(default_factory=uuid4)
    module_id: UUID | None = None
    type: QuestionType = QuestionType.MULTIPLE_CHOICE
    question_text: str = ""
    options: list[str] = field(default_factory=list)
    correct_answer: str = ""
    explanation: str = ""
    code_snippet: str | None = None
    points: int = 10


@dataclass
class Module:
    """Course module (lesson, quiz, lab, or assessment)."""
    id: UUID = field(default_factory=uuid4)
    course_id: UUID | None = None
    title: str = ""
    type: ModuleType = ModuleType.LESSON
    content: str = ""
    order: int = 0
    duration_minutes: int = 30
    questions: list[Question] = field(default_factory=list)
    passing_score: float = 70.0


@dataclass
class Course:
    """Certification course."""
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    regulation: str = ""
    level: CourseLevel = CourseLevel.BEGINNER
    modules: list[Module] = field(default_factory=list)
    estimated_hours: float = 0.0
    prerequisites: list[str] = field(default_factory=list)
    learning_objectives: list[str] = field(default_factory=list)
    price_usd: float = 0.0
    is_free: bool = True
    enrolled_count: int = 0
    completion_rate: float = 0.0
    rating: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Enrollment:
    """User enrollment in a course."""
    id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    course_id: UUID | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    progress_pct: float = 0.0
    current_module: str = ""
    completed_modules: list[str] = field(default_factory=list)
    quiz_scores: dict[str, float] = field(default_factory=dict)
    status: CertificateStatus = CertificateStatus.IN_PROGRESS


@dataclass
class Certificate:
    """Professional certification credential."""
    id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    course_id: UUID | None = None
    certificate_number: str = ""
    issued_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=730))
    status: CertificateStatus = CertificateStatus.PASSED
    score: float = 0.0
    verification_url: str = ""
    credential_id: str = ""


@dataclass
class TutorConversation:
    """AI tutor interaction record."""
    id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    course_id: UUID | None = None
    module_id: UUID | None = None
    question: str = ""
    answer: str = ""
    context: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LearningPath:
    """Curated sequence of courses for a target role."""
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    courses: list[str] = field(default_factory=list)
    estimated_hours: float = 0.0
    target_role: str = ""


@dataclass
class CourseProgress:
    """Detailed progress tracking for a user in a course."""
    id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    course_id: UUID | None = None
    modules_completed: int = 0
    total_modules: int = 0
    avg_quiz_score: float = 0.0
    time_spent_minutes: int = 0
    last_activity: datetime = field(default_factory=datetime.utcnow)
