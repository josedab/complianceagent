"""Compliance Simulation Game Engine models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID


class ScenarioDifficulty(str, Enum):
    """Difficulty levels for game scenarios."""

    TUTORIAL = "tutorial"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class ScenarioCategory(str, Enum):
    """Categories of compliance scenarios."""

    DATA_BREACH = "data_breach"
    AUDIT_RESPONSE = "audit_response"
    RANSOMWARE = "ransomware"
    API_DATA_LEAK = "api_data_leak"
    VENDOR_VIOLATION = "vendor_violation"
    INSIDER_THREAT = "insider_threat"
    GDPR_REQUEST = "gdpr_request"
    INCIDENT_RESPONSE = "incident_response"


class AchievementTier(str, Enum):
    """Achievement tiers."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


@dataclass
class GameDecision:
    """A decision point in a scenario."""

    id: str
    prompt: str
    options: list[str] = field(default_factory=list)
    correct_option: int = 0
    points: int = 10
    explanation: str = ""
    time_limit_seconds: int = 120
    regulation_reference: str = ""


@dataclass
class GameScenario:
    """A compliance training scenario."""

    id: str
    title: str
    description: str
    category: ScenarioCategory
    difficulty: ScenarioDifficulty
    estimated_minutes: int = 15
    max_score: int = 100
    decisions: list[GameDecision] = field(default_factory=list)
    learning_objectives: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)


@dataclass
class PlayerProgress:
    """A player's progress through a scenario."""

    player_id: UUID
    scenario_id: str
    score: int = 0
    decisions_made: int = 0
    correct_decisions: int = 0
    time_spent_seconds: int = 0
    completed: bool = False
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


@dataclass
class Achievement:
    """A player achievement/badge."""

    id: str
    name: str
    description: str
    tier: AchievementTier
    icon: str = "🏆"
    xp_reward: int = 50
    requirement: str = ""


@dataclass
class LeaderboardEntry:
    """A leaderboard entry."""

    player_id: UUID
    display_name: str
    organization: str
    total_xp: int = 0
    level: int = 1
    scenarios_completed: int = 0
    achievements_count: int = 0
    accuracy_rate: float = 0.0
    rank: int = 0
