"""Compliance Health Score API service."""

from app.services.health_score.models import (
    Badge,
    BadgeConfig,
    BadgeStyle,
    CategoryScore,
    CICDIntegration,
    CICDResult,
    DEFAULT_WEIGHTS,
    GRADE_THRESHOLDS,
    HealthScore,
    ScoreCategory,
    ScoreGrade,
    ScoreHistory,
    TrendDirection,
    score_to_color,
    score_to_grade,
)
from app.services.health_score.calculator import (
    ScoreCalculator,
    get_score_calculator,
)
from app.services.health_score.badge import (
    BadgeGenerator,
    get_badge_generator,
)
from app.services.health_score.cicd import (
    CICDIntegrationService,
    get_cicd_service,
)

__all__ = [
    # Models
    "Badge",
    "BadgeConfig",
    "BadgeStyle",
    "CategoryScore",
    "CICDIntegration",
    "CICDResult",
    "DEFAULT_WEIGHTS",
    "GRADE_THRESHOLDS",
    "HealthScore",
    "ScoreCategory",
    "ScoreGrade",
    "ScoreHistory",
    "TrendDirection",
    "score_to_color",
    "score_to_grade",
    # Calculator
    "ScoreCalculator",
    "get_score_calculator",
    # Badge
    "BadgeGenerator",
    "get_badge_generator",
    # CI/CD
    "CICDIntegrationService",
    "get_cicd_service",
]
