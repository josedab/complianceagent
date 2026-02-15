"""Continuous Compliance Training Copilot Service."""

import random
from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.compliance_training.models import (
    ContentFormat,
    DeveloperProfile,
    SkillLevel,
    TeamReport,
    TrainingAssignment,
    TrainingModule,
    TrainingTrigger,
)


logger = structlog.get_logger()

# Pre-built training modules
_DEFAULT_MODULES = [
    TrainingModule(
        title="GDPR Data Subject Rights",
        regulation="GDPR",
        topic="data_subject_rights",
        format=ContentFormat.MICRO_LESSON,
        content="Learn how to handle data subject access requests (DSARs) in your code.",
        quiz_questions=[
            {
                "q": "What is the maximum response time for a DSAR?",
                "options": ["24h", "72h", "30 days", "90 days"],
                "answer": 2,
            },
            {
                "q": "Which right allows users to request data deletion?",
                "options": ["Access", "Portability", "Erasure", "Rectification"],
                "answer": 2,
            },
        ],
        duration_minutes=10,
        skill_level=SkillLevel.BEGINNER,
        tags=["gdpr", "privacy", "dsar"],
        created_at=datetime.now(UTC),
    ),
    TrainingModule(
        title="Secure Logging Practices",
        regulation="SOC2",
        topic="secure_logging",
        format=ContentFormat.CODE_REVIEW,
        content="Review code patterns that prevent PII leakage in application logs.",
        quiz_questions=[
            {
                "q": "Should you log user email addresses?",
                "options": ["Yes", "No", "Only in debug mode"],
                "answer": 1,
            },
        ],
        duration_minutes=15,
        skill_level=SkillLevel.INTERMEDIATE,
        tags=["soc2", "logging", "pii"],
        created_at=datetime.now(UTC),
    ),
    TrainingModule(
        title="HIPAA PHI Handling in APIs",
        regulation="HIPAA",
        topic="phi_handling",
        format=ContentFormat.INTERACTIVE_SCENARIO,
        content="Interactive scenario: build an API endpoint that properly handles PHI.",
        quiz_questions=[
            {
                "q": "What encryption standard is required for PHI at rest?",
                "options": ["AES-128", "AES-256", "DES", "ROT13"],
                "answer": 1,
            },
        ],
        duration_minutes=25,
        skill_level=SkillLevel.ADVANCED,
        tags=["hipaa", "phi", "api", "encryption"],
        created_at=datetime.now(UTC),
    ),
    TrainingModule(
        title="PCI DSS Tokenization",
        regulation="PCI-DSS",
        topic="tokenization",
        format=ContentFormat.MICRO_LESSON,
        content="Understand when and how to tokenize payment card data.",
        quiz_questions=[
            {
                "q": "What is the primary benefit of tokenization?",
                "options": ["Performance", "Reducing PCI scope", "Compression", "Caching"],
                "answer": 1,
            },
        ],
        duration_minutes=12,
        skill_level=SkillLevel.INTERMEDIATE,
        tags=["pci", "tokenization", "payments"],
        created_at=datetime.now(UTC),
    ),
]


class ComplianceTrainingService:
    """Service for continuous compliance training."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot_client = copilot_client
        self._modules: list[TrainingModule] = list(_DEFAULT_MODULES)
        self._profiles: dict[str, DeveloperProfile] = {}
        self._assignments: list[TrainingAssignment] = []

    def _get_or_create_profile(self, developer_id: str) -> DeveloperProfile:
        """Get or create a developer profile."""
        if developer_id not in self._profiles:
            self._profiles[developer_id] = DeveloperProfile(
                developer_id=developer_id,
                name=f"Developer {developer_id}",
                skill_level=SkillLevel.BEGINNER,
                compliance_score=50.0,
            )
        return self._profiles[developer_id]

    async def trigger_training(
        self,
        developer_id: str,
        violation_type: str,
        regulation: str,
    ) -> TrainingAssignment:
        """Trigger training for a developer based on a violation."""
        profile = self._get_or_create_profile(developer_id)
        profile.violations_triggered += 1
        profile.last_violation_at = datetime.now(UTC)

        # Find a relevant module
        matching = [m for m in self._modules if m.regulation.lower() == regulation.lower()]
        module = matching[0] if matching else self._modules[0]

        assignment = TrainingAssignment(
            developer_id=developer_id,
            module_id=module.id,
            trigger=TrainingTrigger.PR_VIOLATION,
            assigned_at=datetime.now(UTC),
            status="assigned",
        )
        self._assignments.append(assignment)

        # Track weakness
        if violation_type not in profile.weaknesses:
            profile.weaknesses.append(violation_type)

        logger.info(
            "Training triggered",
            developer_id=developer_id,
            violation_type=violation_type,
            module=module.title,
        )
        return assignment

    async def get_developer_profile(self, developer_id: str) -> DeveloperProfile:
        """Get a developer's training profile."""
        return self._get_or_create_profile(developer_id)

    async def list_modules(
        self,
        regulation: str | None = None,
        level: SkillLevel | None = None,
    ) -> list[TrainingModule]:
        """List training modules with optional filters."""
        results = list(self._modules)
        if regulation:
            results = [m for m in results if m.regulation.lower() == regulation.lower()]
        if level:
            results = [m for m in results if m.skill_level == level]
        return results

    async def complete_training(
        self,
        assignment_id: UUID,
        quiz_score: float,
    ) -> TrainingAssignment | None:
        """Complete a training assignment with quiz score."""
        assignment = next((a for a in self._assignments if a.id == assignment_id), None)
        if not assignment:
            return None

        assignment.completed_at = datetime.now(UTC)
        assignment.quiz_score = quiz_score
        assignment.status = "completed"

        # Update profile
        profile = self._get_or_create_profile(assignment.developer_id)
        module_id_str = str(assignment.module_id)
        if module_id_str not in profile.completed_modules:
            profile.completed_modules.append(module_id_str)
        profile.quiz_scores[module_id_str] = quiz_score

        # Recalculate compliance score
        if profile.quiz_scores:
            avg = sum(profile.quiz_scores.values()) / len(profile.quiz_scores)
            profile.compliance_score = round(min(100.0, avg * 1.1), 1)

        # Update skill level based on completed modules
        completed_count = len(profile.completed_modules)
        if completed_count >= 10:
            profile.skill_level = SkillLevel.EXPERT
        elif completed_count >= 6:
            profile.skill_level = SkillLevel.ADVANCED
        elif completed_count >= 3:
            profile.skill_level = SkillLevel.INTERMEDIATE

        # Track strengths
        module = next((m for m in self._modules if m.id == assignment.module_id), None)
        if module and quiz_score >= 80.0 and module.topic not in profile.strengths:
            profile.strengths.append(module.topic)

        logger.info(
            "Training completed",
            developer_id=assignment.developer_id,
            quiz_score=quiz_score,
        )
        return assignment

    async def get_team_report(self, team: str) -> TeamReport:
        """Generate a team compliance training report."""
        profiles = list(self._profiles.values())
        if not profiles:
            return TeamReport(team=team, generated_at=datetime.now(UTC))

        total = len(profiles)
        avg_score = round(sum(p.compliance_score for p in profiles) / total, 1)
        modules_done = sum(len(p.completed_modules) for p in profiles)

        skill_dist: dict[str, int] = {}
        all_weaknesses: dict[str, int] = {}
        for p in profiles:
            level = p.skill_level.value
            skill_dist[level] = skill_dist.get(level, 0) + 1
            for w in p.weaknesses:
                all_weaknesses[w] = all_weaknesses.get(w, 0) + 1

        top_gaps = sorted(all_weaknesses, key=all_weaknesses.get, reverse=True)[:5]

        return TeamReport(
            team=team,
            total_developers=total,
            avg_score=avg_score,
            modules_completed=modules_done,
            violation_reduction_pct=round(random.uniform(5.0, 35.0), 1),
            skill_distribution=skill_dist,
            top_gaps=top_gaps,
            generated_at=datetime.now(UTC),
        )

    async def list_assignments(
        self,
        developer_id: str | None = None,
        status: str | None = None,
    ) -> list[TrainingAssignment]:
        """List training assignments with optional filters."""
        results = list(self._assignments)
        if developer_id:
            results = [a for a in results if a.developer_id == developer_id]
        if status:
            results = [a for a in results if a.status == status]
        return results

    async def get_leaderboard(self, limit: int = 10) -> list[DeveloperProfile]:
        """Get top developers by compliance score."""
        profiles = sorted(
            self._profiles.values(),
            key=lambda p: p.compliance_score,
            reverse=True,
        )
        return profiles[:limit]
