"""Compliance Simulation Game Engine service."""

from __future__ import annotations

from uuid import UUID, uuid4

import structlog

from app.services.game_engine.models import (
    Achievement,
    AchievementTier,
    GameDecision,
    GameScenario,
    LeaderboardEntry,
    PlayerProgress,
    ScenarioCategory,
    ScenarioDifficulty,
)

logger = structlog.get_logger()

_SCENARIOS: list[GameScenario] = [
    GameScenario(
        id="gdpr-breach-response",
        title="GDPR Data Breach Response",
        description="A production database containing EU citizen PII has been exposed. Navigate the 72-hour breach notification process.",
        category=ScenarioCategory.DATA_BREACH,
        difficulty=ScenarioDifficulty.MEDIUM,
        estimated_minutes=20, max_score=100,
        frameworks=["GDPR"],
        learning_objectives=["Understand 72-hour notification deadline", "Identify required authorities", "Draft breach notification"],
        decisions=[
            GameDecision(id="d1", prompt="You discover a database backup was publicly accessible for 6 hours. What is your first action?",
                options=["Immediately notify the DPA", "Assess the scope and impact first", "Delete the backup and hope no one noticed", "Email the engineering team"],
                correct_option=1, points=20, explanation="GDPR Art. 33 requires assessment before notification. You need to understand scope first.",
                regulation_reference="GDPR Article 33"),
            GameDecision(id="d2", prompt="Your assessment reveals 12,000 EU citizens' data was exposed. Within how many hours must you notify the supervisory authority?",
                options=["24 hours", "48 hours", "72 hours", "7 days"],
                correct_option=2, points=20, explanation="GDPR Article 33(1) requires notification within 72 hours of becoming aware.",
                regulation_reference="GDPR Article 33(1)"),
            GameDecision(id="d3", prompt="Which of the following must be included in your breach notification?",
                options=["Only the date of the breach", "Nature of breach, categories of data, likely consequences, measures taken", "Just the number of affected individuals", "A formal apology letter"],
                correct_option=1, points=25, explanation="Art. 33(3) requires: nature, categories, consequences, and measures taken or proposed.",
                regulation_reference="GDPR Article 33(3)"),
        ],
    ),
    GameScenario(
        id="hipaa-audit-prep",
        title="HIPAA Audit Preparation",
        description="OCR has scheduled a HIPAA compliance audit of your healthcare SaaS platform. Prepare the required documentation and evidence.",
        category=ScenarioCategory.AUDIT_RESPONSE,
        difficulty=ScenarioDifficulty.HARD,
        estimated_minutes=25, max_score=120,
        frameworks=["HIPAA"],
        learning_objectives=["Prepare audit documentation", "Identify required safeguards", "Handle auditor requests"],
        decisions=[
            GameDecision(id="d1", prompt="The auditor requests your Risk Analysis documentation. What should this include?",
                options=["Just a list of servers", "Threats, vulnerabilities, likelihood, impact for all ePHI", "Your latest penetration test report", "Employee training records"],
                correct_option=1, points=25, explanation="45 CFR § 164.308(a)(1) requires comprehensive risk analysis covering all ePHI.",
                regulation_reference="45 CFR § 164.308(a)(1)"),
            GameDecision(id="d2", prompt="The auditor finds that your application logs contain patient names in plaintext. What is the correct response?",
                options=["It's fine since logs are internal", "Acknowledge the finding and implement log scrubbing immediately", "Argue that log data isn't ePHI", "Ask for a 30-day remediation window"],
                correct_option=1, points=30, explanation="Patient names in logs constitute ePHI exposure. Immediate remediation is expected.",
                regulation_reference="45 CFR § 164.312(a)(1)"),
        ],
    ),
    GameScenario(
        id="ransomware-response",
        title="Ransomware Attack Response",
        description="Your systems have been hit by ransomware. Navigate the incident response while maintaining compliance obligations.",
        category=ScenarioCategory.RANSOMWARE,
        difficulty=ScenarioDifficulty.EXPERT,
        estimated_minutes=30, max_score=150,
        frameworks=["GDPR", "HIPAA", "PCI-DSS"],
        learning_objectives=["Execute incident response plan", "Meet notification requirements", "Preserve forensic evidence"],
        decisions=[
            GameDecision(id="d1", prompt="Ransomware has encrypted your production database. What is your immediate priority?",
                options=["Pay the ransom to recover data", "Isolate affected systems to prevent spread", "Restore from backups immediately", "Call law enforcement first"],
                correct_option=1, points=30, explanation="Containment is the first priority to prevent lateral movement.",
                regulation_reference="NIST SP 800-61r2"),
            GameDecision(id="d2", prompt="After containment, you discover PCI cardholder data may have been exfiltrated. What must you do?",
                options=["Wait for forensic analysis to complete", "Notify your acquiring bank and payment brands within 24 hours", "Only notify if data was confirmed stolen", "Reset all passwords and move on"],
                correct_option=1, points=35, explanation="PCI-DSS requires immediate notification to acquirer and payment brands.",
                regulation_reference="PCI-DSS IR 12.10"),
        ],
    ),
    GameScenario(
        id="api-data-leak",
        title="API Data Leak Investigation",
        description="A security researcher reports that your public API is leaking user data through verbose error messages. Investigate and remediate.",
        category=ScenarioCategory.API_DATA_LEAK,
        difficulty=ScenarioDifficulty.EASY,
        estimated_minutes=15, max_score=80,
        frameworks=["GDPR", "SOC 2"],
        learning_objectives=["Identify data exposure vectors", "Apply data minimization", "Implement secure error handling"],
        decisions=[
            GameDecision(id="d1", prompt="The error response includes user email, IP address, and stack trace. Which data should be removed first?",
                options=["Stack trace only", "All PII (email, IP) and stack trace", "Just the email", "None - it helps debugging"],
                correct_option=1, points=20, explanation="All PII and internal details must be removed from error responses per data minimization principles.",
                regulation_reference="GDPR Article 5(1)(c)"),
        ],
    ),
    GameScenario(
        id="vendor-violation",
        title="Third-Party Vendor Violation",
        description="Your cloud vendor has suffered a breach affecting data you process. Navigate the shared responsibility model.",
        category=ScenarioCategory.VENDOR_VIOLATION,
        difficulty=ScenarioDifficulty.MEDIUM,
        estimated_minutes=20, max_score=100,
        frameworks=["GDPR", "SOC 2"],
        learning_objectives=["Understand processor obligations", "Assess shared responsibility", "Execute vendor incident workflow"],
        decisions=[
            GameDecision(id="d1", prompt="Your cloud vendor notifies you of a breach. As the data controller, what is your obligation?",
                options=["Nothing - it's the vendor's responsibility", "Conduct your own assessment and notify your supervisory authority if required", "Sue the vendor immediately", "Switch vendors and don't notify anyone"],
                correct_option=1, points=25, explanation="As controller, you remain responsible for PII even when processed by a vendor.",
                regulation_reference="GDPR Article 28"),
        ],
    ),
]

_ACHIEVEMENTS: list[Achievement] = [
    Achievement(id="gdpr-guardian", name="GDPR Guardian", description="Complete all GDPR scenarios", tier=AchievementTier.GOLD, icon="🛡️", xp_reward=100),
    Achievement(id="breach-responder", name="Breach Responder", description="Score 90%+ on a breach scenario", tier=AchievementTier.SILVER, icon="🚨", xp_reward=75),
    Achievement(id="speed-demon", name="Speed Demon", description="Complete a scenario in under 5 minutes", tier=AchievementTier.BRONZE, icon="⚡", xp_reward=50),
    Achievement(id="perfect-score", name="Perfect Score", description="Achieve 100% on any scenario", tier=AchievementTier.PLATINUM, icon="💎", xp_reward=200),
    Achievement(id="multi-framework", name="Multi-Framework Expert", description="Complete scenarios across 3+ frameworks", tier=AchievementTier.GOLD, icon="🌐", xp_reward=100),
]

_LEADERBOARD: list[LeaderboardEntry] = [
    LeaderboardEntry(player_id=uuid4(), display_name="ComplianceNinja", organization="Acme Corp", total_xp=2450, level=12, scenarios_completed=8, achievements_count=4, accuracy_rate=0.92, rank=1),
    LeaderboardEntry(player_id=uuid4(), display_name="RegTechPro", organization="FinanceHQ", total_xp=1890, level=9, scenarios_completed=6, achievements_count=3, accuracy_rate=0.85, rank=2),
    LeaderboardEntry(player_id=uuid4(), display_name="PrivacyChampion", organization="HealthCo", total_xp=1520, level=7, scenarios_completed=5, achievements_count=2, accuracy_rate=0.88, rank=3),
    LeaderboardEntry(player_id=uuid4(), display_name="AuditAce", organization="TechStartup", total_xp=980, level=5, scenarios_completed=3, achievements_count=1, accuracy_rate=0.78, rank=4),
]


class GameEngineService:
    """Service for compliance simulation game engine."""

    async def list_scenarios(
        self, category: ScenarioCategory | None = None,
        difficulty: ScenarioDifficulty | None = None,
    ) -> list[GameScenario]:
        result = list(_SCENARIOS)
        if category:
            result = [s for s in result if s.category == category]
        if difficulty:
            result = [s for s in result if s.difficulty == difficulty]
        return result

    async def get_scenario(self, scenario_id: str) -> GameScenario | None:
        return next((s for s in _SCENARIOS if s.id == scenario_id), None)

    async def submit_decision(
        self, scenario_id: str, decision_id: str, selected_option: int,
    ) -> dict:
        scenario = await self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")
        decision = next((d for d in scenario.decisions if d.id == decision_id), None)
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")
        if selected_option < 0 or selected_option >= len(decision.options):
            raise ValueError(f"selected_option {selected_option} out of bounds (0 to {len(decision.options) - 1})")

        correct = selected_option == decision.correct_option
        points = decision.points if correct else 0
        return {
            "correct": correct,
            "points_earned": points,
            "explanation": decision.explanation,
            "regulation_reference": decision.regulation_reference,
            "correct_option": decision.correct_option,
        }

    async def get_leaderboard(self, limit: int = 10) -> list[LeaderboardEntry]:
        if limit <= 0:
            raise ValueError("Leaderboard limit must be greater than 0")
        return sorted(_LEADERBOARD, key=lambda e: e.total_xp, reverse=True)[:limit]

    async def get_achievements(self) -> list[Achievement]:
        return list(_ACHIEVEMENTS)

    async def get_player_progress(self, player_id: UUID) -> list[PlayerProgress]:
        return [
            PlayerProgress(player_id=player_id, scenario_id="gdpr-breach-response", score=85, decisions_made=3, correct_decisions=2, time_spent_seconds=720, completed=True),
            PlayerProgress(player_id=player_id, scenario_id="hipaa-audit-prep", score=55, decisions_made=2, correct_decisions=1, time_spent_seconds=480, completed=False),
        ]
