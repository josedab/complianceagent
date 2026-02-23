"""Compliance Learning Service — extended learning paths and quiz engine."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession


logger = structlog.get_logger()


class ContentType(str, Enum):
    """Types of learning content."""

    ARTICLE = "article"
    VIDEO = "video"
    INTERACTIVE = "interactive"
    QUIZ = "quiz"
    CODE_CHALLENGE = "code_challenge"


@dataclass
class QuizQuestion:
    """A single quiz question."""

    id: UUID = field(default_factory=uuid4)
    question: str = ""
    options: list[str] = field(default_factory=list)
    correct_answer: int = 0
    explanation: str = ""
    regulation_ref: str = ""


@dataclass
class LearningModule:
    """A module within a learning path."""

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    framework: str = ""
    content_type: ContentType = ContentType.ARTICLE
    quiz_questions: list[QuizQuestion] = field(default_factory=list)
    completion_rate: float = 0.0


@dataclass
class LearningPath:
    """A structured learning path for a compliance framework."""

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    frameworks: list[str] = field(default_factory=list)
    modules: list[LearningModule] = field(default_factory=list)
    estimated_hours: float = 0.0
    difficulty: str = "beginner"


@dataclass
class TeamProgress:
    """Team-level progress on compliance training."""

    team: str = ""
    members_total: int = 0
    members_certified: int = 0
    avg_score: float = 0.0
    completion_rate: float = 0.0


_GDPR_MODULES = [
    LearningModule(
        title="GDPR Fundamentals",
        framework="GDPR",
        content_type=ContentType.ARTICLE,
        quiz_questions=[
            QuizQuestion(
                question="What does GDPR stand for?",
                options=[
                    "General Data Protection Regulation",
                    "Global Data Privacy Rules",
                    "General Digital Privacy Regulation",
                    "Government Data Protection Requirements",
                ],
                correct_answer=0,
                explanation="GDPR is the General Data Protection Regulation.",
                regulation_ref="GDPR Preamble",
            ),
            QuizQuestion(
                question="What is the maximum fine under GDPR?",
                options=["$1M", "2% of revenue", "4% of global annual turnover or €20M", "€50M"],
                correct_answer=2,
                explanation="Maximum fine is 4% of global annual turnover or €20M, whichever is greater.",
                regulation_ref="Article 83",
            ),
        ],
        completion_rate=0.0,
    ),
    LearningModule(
        title="Data Subject Rights",
        framework="GDPR",
        content_type=ContentType.INTERACTIVE,
        quiz_questions=[
            QuizQuestion(
                question="How long to respond to a DSAR?",
                options=["24 hours", "72 hours", "30 days", "90 days"],
                correct_answer=2,
                explanation="Organizations must respond within 30 days.",
                regulation_ref="Article 12(3)",
            ),
        ],
        completion_rate=0.0,
    ),
    LearningModule(
        title="GDPR Code Patterns",
        framework="GDPR",
        content_type=ContentType.CODE_CHALLENGE,
        completion_rate=0.0,
    ),
]

_HIPAA_MODULES = [
    LearningModule(
        title="HIPAA Privacy Rule",
        framework="HIPAA",
        content_type=ContentType.ARTICLE,
        quiz_questions=[
            QuizQuestion(
                question="What is PHI?",
                options=[
                    "Personal Health Information",
                    "Protected Health Information",
                    "Private Hospital Information",
                    "Public Health Index",
                ],
                correct_answer=1,
                explanation="PHI stands for Protected Health Information.",
                regulation_ref="45 CFR 160.103",
            ),
        ],
        completion_rate=0.0,
    ),
    LearningModule(
        title="HIPAA Security Rule",
        framework="HIPAA",
        content_type=ContentType.VIDEO,
        quiz_questions=[
            QuizQuestion(
                question="What encryption is required for PHI at rest?",
                options=["AES-128", "AES-256", "DES", "None required"],
                correct_answer=1,
                explanation="AES-256 is the recommended standard for PHI encryption.",
                regulation_ref="45 CFR 164.312",
            ),
        ],
        completion_rate=0.0,
    ),
    LearningModule(
        title="HIPAA in Code Reviews",
        framework="HIPAA",
        content_type=ContentType.CODE_CHALLENGE,
        completion_rate=0.0,
    ),
]

_PCI_MODULES = [
    LearningModule(
        title="PCI-DSS Overview",
        framework="PCI-DSS",
        content_type=ContentType.ARTICLE,
        quiz_questions=[
            QuizQuestion(
                question="How many requirements does PCI-DSS have?",
                options=["6", "10", "12", "15"],
                correct_answer=2,
                explanation="PCI-DSS has 12 core requirements.",
                regulation_ref="PCI-DSS v4.0",
            ),
        ],
        completion_rate=0.0,
    ),
    LearningModule(
        title="Tokenization & Encryption",
        framework="PCI-DSS",
        content_type=ContentType.INTERACTIVE,
        quiz_questions=[
            QuizQuestion(
                question="What is the benefit of tokenization?",
                options=["Performance", "Reducing PCI scope", "Compression", "Caching"],
                correct_answer=1,
                explanation="Tokenization reduces PCI scope by replacing card data with tokens.",
                regulation_ref="PCI-DSS Req 3",
            ),
        ],
        completion_rate=0.0,
    ),
]

_EU_AI_MODULES = [
    LearningModule(
        title="EU AI Act Fundamentals",
        framework="EU-AI-Act",
        content_type=ContentType.ARTICLE,
        quiz_questions=[
            QuizQuestion(
                question="What risk categories does the EU AI Act define?",
                options=[
                    "Low and High",
                    "Unacceptable, High, Limited, Minimal",
                    "Critical, Major, Minor",
                    "Tier 1, 2, 3",
                ],
                correct_answer=1,
                explanation="The EU AI Act defines four risk categories.",
                regulation_ref="Article 6",
            ),
        ],
        completion_rate=0.0,
    ),
    LearningModule(
        title="AI Transparency Requirements",
        framework="EU-AI-Act",
        content_type=ContentType.VIDEO,
        quiz_questions=[
            QuizQuestion(
                question="Must AI-generated content be disclosed?",
                options=[
                    "Never",
                    "Only for high-risk",
                    "Yes, always for certain systems",
                    "Only in the EU",
                ],
                correct_answer=2,
                explanation="The EU AI Act requires disclosure of AI-generated content for certain systems.",
                regulation_ref="Article 52",
            ),
        ],
        completion_rate=0.0,
    ),
]

_BUILTIN_PATHS = [
    LearningPath(
        title="GDPR Compliance for Developers",
        frameworks=["GDPR"],
        modules=_GDPR_MODULES,
        estimated_hours=8.0,
        difficulty="intermediate",
    ),
    LearningPath(
        title="HIPAA Security & Privacy",
        frameworks=["HIPAA"],
        modules=_HIPAA_MODULES,
        estimated_hours=10.0,
        difficulty="advanced",
    ),
    LearningPath(
        title="PCI-DSS Essentials",
        frameworks=["PCI-DSS"],
        modules=_PCI_MODULES,
        estimated_hours=6.0,
        difficulty="beginner",
    ),
    LearningPath(
        title="EU AI Act Readiness",
        frameworks=["EU-AI-Act"],
        modules=_EU_AI_MODULES,
        estimated_hours=5.0,
        difficulty="intermediate",
    ),
]


class ComplianceLearningService:
    """Service for compliance learning paths and quiz-based training."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._paths: list[LearningPath] = list(_BUILTIN_PATHS)
        self._quiz_answers: dict[str, list[dict]] = {}
        self._team_progress: dict[str, TeamProgress] = {}

    async def get_learning_paths(self, framework: str | None = None) -> list[LearningPath]:
        """List available learning paths with optional framework filter."""
        results = list(self._paths)
        if framework:
            results = [p for p in results if framework in p.frameworks]
        return results

    async def get_path(self, path_id: UUID) -> LearningPath | None:
        """Get a specific learning path by ID."""
        return next((p for p in self._paths if p.id == path_id), None)

    async def get_module(self, module_id: UUID) -> LearningModule | None:
        """Get a specific learning module by ID."""
        for path in self._paths:
            for module in path.modules:
                if module.id == module_id:
                    return module
        return None

    async def submit_quiz_answer(
        self,
        user_id: str,
        question_id: UUID,
        selected_answer: int,
    ) -> dict:
        """Submit an answer to a quiz question and return feedback."""
        question: QuizQuestion | None = None
        for path in self._paths:
            for module in path.modules:
                for q in module.quiz_questions:
                    if q.id == question_id:
                        question = q
                        break

        if not question:
            return {"correct": False, "error": "Question not found"}

        correct = selected_answer == question.correct_answer
        answer_record = {
            "question_id": str(question_id),
            "selected": selected_answer,
            "correct": correct,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        if user_id not in self._quiz_answers:
            self._quiz_answers[user_id] = []
        self._quiz_answers[user_id].append(answer_record)

        logger.info("Quiz answer submitted", user_id=user_id, correct=correct)
        return {
            "correct": correct,
            "explanation": question.explanation,
            "regulation_ref": question.regulation_ref,
        }

    async def get_team_progress(self, team: str) -> TeamProgress:
        """Get training progress for a team."""
        if team in self._team_progress:
            return self._team_progress[team]

        # Deterministic defaults
        progress = TeamProgress(
            team=team,
            members_total=12,
            members_certified=4,
            avg_score=72.5,
            completion_rate=33.3,
        )
        self._team_progress[team] = progress
        return progress

    async def generate_personalized_path(
        self,
        user_id: str,
        frameworks: list[str],
        skill_level: str = "beginner",
    ) -> LearningPath:
        """Generate a personalized learning path based on user needs."""
        modules: list[LearningModule] = []
        for path in self._paths:
            for fw in frameworks:
                if fw in path.frameworks:
                    modules.extend(path.modules)

        # Deduplicate by title
        seen_titles: set[str] = set()
        unique_modules: list[LearningModule] = []
        for m in modules:
            if m.title not in seen_titles:
                seen_titles.add(m.title)
                unique_modules.append(m)

        total_hours = len(unique_modules) * 2.5

        personalized = LearningPath(
            title=f"Personalized Path for {', '.join(frameworks)}",
            frameworks=frameworks,
            modules=unique_modules,
            estimated_hours=total_hours,
            difficulty=skill_level,
        )

        logger.info(
            "Personalized path generated",
            user_id=user_id,
            frameworks=frameworks,
            modules=len(unique_modules),
        )
        return personalized
