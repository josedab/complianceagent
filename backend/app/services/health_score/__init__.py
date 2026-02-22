"""Compliance Health Score API service."""

from app.services.health_score.badge import (
    BadgeGenerator,
    get_badge_generator,
)
from app.services.health_score.calculator import (
    ScoreCalculator,
    get_score_calculator,
)
from app.services.health_score.cicd import (
    CICDIntegrationService,
    get_cicd_service,
)
from app.services.health_score.models import (
    DEFAULT_WEIGHTS,
    GRADE_THRESHOLDS,
    Badge,
    BadgeConfig,
    BadgeStyle,
    CategoryScore,
    CICDIntegration,
    CICDResult,
    HealthScore,
    ScoreCategory,
    ScoreGrade,
    ScoreHistory,
    TrendDirection,
    score_to_color,
    score_to_grade,
)


__all__ = [
    "DEFAULT_WEIGHTS",
    "GRADE_THRESHOLDS",
    # Models
    "Badge",
    "BadgeConfig",
    # Badge
    "BadgeGenerator",
    "BadgeStyle",
    "CICDIntegration",
    # CI/CD
    "CICDIntegrationService",
    "CICDResult",
    "CategoryScore",
    "HealthScore",
    # Calculator
    "ScoreCalculator",
    "ScoreCategory",
    "ScoreGrade",
    "ScoreHistory",
    "TrendDirection",
    "get_badge_generator",
    "get_cicd_service",
    "get_score_calculator",
    "score_to_color",
    "score_to_grade",
]
