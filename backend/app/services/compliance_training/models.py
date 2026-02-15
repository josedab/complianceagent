"""Continuous Compliance Training Copilot models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class TrainingTrigger(str, Enum):
    """What triggered the training assignment."""

    PR_VIOLATION = "pr_violation"
    SCHEDULED = "scheduled"
    ONBOARDING = "onboarding"
    CERTIFICATION_RENEWAL = "certification_renewal"
    REGULATION_UPDATE = "regulation_update"


class ContentFormat(str, Enum):
    """Training content format."""

    MICRO_LESSON = "micro_lesson"
    QUIZ = "quiz"
    INTERACTIVE_SCENARIO = "interactive_scenario"
    CODE_REVIEW = "code_review"
    VIDEO_SUMMARY = "video_summary"


class SkillLevel(str, Enum):
    """Developer skill level."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class TrainingModule:
    """A compliance training module."""

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    regulation: str = ""
    topic: str = ""
    format: ContentFormat = ContentFormat.MICRO_LESSON
    content: str = ""
    quiz_questions: list[dict] = field(default_factory=list)
    duration_minutes: int = 15
    skill_level: SkillLevel = SkillLevel.BEGINNER
    tags: list[str] = field(default_factory=list)
    created_at: datetime | None = None


@dataclass
class DeveloperProfile:
    """A developer's compliance training profile."""

    id: UUID = field(default_factory=uuid4)
    developer_id: str = ""
    name: str = ""
    skill_level: SkillLevel = SkillLevel.BEGINNER
    completed_modules: list[str] = field(default_factory=list)
    quiz_scores: dict[str, float] = field(default_factory=dict)
    violations_triggered: int = 0
    last_violation_at: datetime | None = None
    compliance_score: float = 50.0
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)


@dataclass
class TrainingAssignment:
    """A training assignment for a developer."""

    id: UUID = field(default_factory=uuid4)
    developer_id: str = ""
    module_id: UUID = field(default_factory=uuid4)
    trigger: TrainingTrigger = TrainingTrigger.SCHEDULED
    assigned_at: datetime | None = None
    completed_at: datetime | None = None
    quiz_score: float | None = None
    status: str = "assigned"


@dataclass
class TeamReport:
    """Team compliance training report."""

    team: str = ""
    total_developers: int = 0
    avg_score: float = 0.0
    modules_completed: int = 0
    violation_reduction_pct: float = 0.0
    skill_distribution: dict = field(default_factory=dict)
    top_gaps: list[str] = field(default_factory=list)
    generated_at: datetime | None = None
