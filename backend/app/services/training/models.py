"""Training mode data models."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class QuestionType(str, Enum):
    """Types of quiz questions."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    MULTI_SELECT = "multi_select"
    CODE_REVIEW = "code_review"
    SCENARIO = "scenario"


class CertificateStatus(str, Enum):
    """Certificate status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class Question:
    """Quiz question."""
    id: UUID = field(default_factory=uuid4)
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    text: str = ""
    code_snippet: str | None = None
    options: list[dict] = field(default_factory=list)
    correct_answers: list[int] = field(default_factory=list)
    explanation: str = ""
    points: int = 10
    difficulty: str = "medium"
    tags: list[str] = field(default_factory=list)
    framework: str = ""
    requirement_id: str = ""


@dataclass
class Quiz:
    """Training quiz."""
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    framework: str = ""
    questions: list[Question] = field(default_factory=list)
    passing_score: float = 70.0
    time_limit_minutes: int | None = None
    max_attempts: int = 3
    shuffle_questions: bool = True
    show_correct_answers: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class QuizAttempt:
    """Record of a quiz attempt."""
    id: UUID = field(default_factory=uuid4)
    quiz_id: UUID | None = None
    user_id: UUID | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    answers: dict[str, list[int]] = field(default_factory=dict)
    score: float = 0.0
    passed: bool = False
    time_taken_seconds: int = 0
    attempt_number: int = 1


@dataclass
class TrainingModule:
    """Training module with content and quizzes."""
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    framework: str = ""
    difficulty: str = "beginner"
    estimated_minutes: int = 30
    
    # Content sections
    sections: list[dict] = field(default_factory=list)
    
    # Associated quizzes
    quizzes: list[Quiz] = field(default_factory=list)
    
    # Prerequisites
    prerequisites: list[UUID] = field(default_factory=list)
    
    # Learning objectives
    learning_objectives: list[str] = field(default_factory=list)
    
    # Requirements covered
    requirements_covered: list[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0.0"


@dataclass
class TrainingProgress:
    """User's progress in a training module."""
    id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    module_id: UUID | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    sections_completed: list[int] = field(default_factory=list)
    quiz_attempts: list[QuizAttempt] = field(default_factory=list)
    current_section: int = 0
    progress_percentage: float = 0.0
    is_complete: bool = False
    best_quiz_score: float = 0.0


@dataclass
class Certificate:
    """Training completion certificate."""
    id: UUID = field(default_factory=uuid4)
    user_id: UUID | None = None
    organization_id: UUID | None = None
    module_id: UUID | None = None
    framework: str = ""
    title: str = ""
    issued_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=365))
    status: CertificateStatus = CertificateStatus.ACTIVE
    score: float = 0.0
    verification_code: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class UserTrainingProfile:
    """User's overall training profile."""
    user_id: UUID | None = None
    organization_id: UUID | None = None
    total_modules_completed: int = 0
    total_training_hours: float = 0.0
    certificates: list[Certificate] = field(default_factory=list)
    current_enrollments: list[TrainingProgress] = field(default_factory=list)
    badges: list[str] = field(default_factory=list)
    streak_days: int = 0
    last_activity: datetime | None = None
    framework_scores: dict[str, float] = field(default_factory=dict)
