"""Compliance Badge & Scorecard Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.compliance_badge.models import (
    BadgeData,
    BadgeStyle,
    EmbedSnippet,
    Grade,
    PublicScorecard,
)


logger = structlog.get_logger()


def _score_to_grade(score: float) -> Grade:
    if score >= 97:
        return Grade.A_PLUS
    if score >= 93:
        return Grade.A
    if score >= 90:
        return Grade.A_MINUS
    if score >= 87:
        return Grade.B_PLUS
    if score >= 83:
        return Grade.B
    if score >= 80:
        return Grade.B_MINUS
    if score >= 77:
        return Grade.C_PLUS
    if score >= 70:
        return Grade.C
    if score >= 60:
        return Grade.D
    return Grade.F


def _grade_to_color(grade: Grade) -> str:
    colors = {
        Grade.A_PLUS: "brightgreen", Grade.A: "brightgreen", Grade.A_MINUS: "green",
        Grade.B_PLUS: "green", Grade.B: "yellowgreen", Grade.B_MINUS: "yellowgreen",
        Grade.C_PLUS: "yellow", Grade.C: "yellow", Grade.D: "orange", Grade.F: "red",
    }
    return colors.get(grade, "lightgrey")


def _generate_svg(label: str, grade: str, color: str, style: BadgeStyle) -> str:
    """Generate shields.io-compatible SVG badge."""
    label_width = len(label) * 7 + 10
    value_width = len(grade) * 7 + 10
    total_width = label_width + value_width
    color_map = {
        "brightgreen": "#4c1", "green": "#97ca00", "yellowgreen": "#a4a61d",
        "yellow": "#dfb317", "orange": "#fe7d37", "red": "#e05d44", "lightgrey": "#9f9f9f",
    }
    hex_color = color_map.get(color, "#9f9f9f")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20">'
        f'<rect width="{label_width}" height="20" fill="#555"/>'
        f'<rect x="{label_width}" width="{value_width}" height="20" fill="{hex_color}"/>'
        f'<text x="{label_width // 2}" y="14" fill="#fff" text-anchor="middle" '
        f'font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">{label}</text>'
        f'<text x="{label_width + value_width // 2}" y="14" fill="#fff" text-anchor="middle" '
        f'font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">{grade}</text>'
        f'</svg>'
    )


class ComplianceBadgeService:
    """Service for compliance badges and public scorecards."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._scorecards: dict[str, PublicScorecard] = {}

    async def generate_badge(
        self,
        repo: str,
        style: str = "flat",
        label: str = "compliance",
    ) -> BadgeData:
        """Generate an SVG compliance badge for a repository."""
        scorecard = self._scorecards.get(repo)
        score = scorecard.overall_score if scorecard else 85.0
        grade = _score_to_grade(score)
        color = _grade_to_color(grade)
        badge_style = BadgeStyle(style) if style in BadgeStyle.__members__.values() else BadgeStyle.FLAT

        svg = _generate_svg(label, grade.value, color, badge_style)

        badge = BadgeData(
            repo=repo,
            grade=grade,
            score=score,
            label=label,
            color=color,
            style=badge_style,
            svg=svg,
            generated_at=datetime.now(UTC),
        )
        logger.info("Badge generated", repo=repo, grade=grade.value)
        return badge

    async def get_public_scorecard(self, repo: str) -> PublicScorecard:
        """Get or generate a public scorecard for a repository."""
        if repo in self._scorecards:
            return self._scorecards[repo]

        scorecard = PublicScorecard(
            repo=repo,
            overall_score=85.0,
            overall_grade=Grade.B_PLUS,
            frameworks=[
                {"name": "GDPR", "score": 88.0, "grade": "B+", "status": "compliant"},
                {"name": "HIPAA", "score": 82.0, "grade": "B", "status": "partial"},
                {"name": "PCI-DSS", "score": 90.0, "grade": "A-", "status": "compliant"},
                {"name": "SOC 2", "score": 78.0, "grade": "C+", "status": "in_progress"},
            ],
            trend=[
                {"date": "2026-02-15", "score": 82.0},
                {"date": "2026-02-16", "score": 83.5},
                {"date": "2026-02-17", "score": 84.0},
                {"date": "2026-02-18", "score": 85.0},
                {"date": "2026-02-19", "score": 84.5},
                {"date": "2026-02-20", "score": 85.0},
                {"date": "2026-02-21", "score": 85.0},
            ],
            last_scan_at=datetime.now(UTC),
            generated_at=datetime.now(UTC),
        )
        self._scorecards[repo] = scorecard
        return scorecard

    def get_embed_snippets(self, repo: str, base_url: str = "https://complianceagent.ai") -> list[EmbedSnippet]:
        """Get embed code snippets for badge integration."""
        badge_url = f"{base_url}/api/v1/compliance-badge/badge/{repo}.svg"
        scorecard_url = f"{base_url}/api/v1/compliance-badge/scorecard/{repo}"
        return [
            EmbedSnippet(
                format="markdown",
                code=f"[![Compliance]({badge_url})]({scorecard_url})",
                preview_url=badge_url,
            ),
            EmbedSnippet(
                format="html",
                code=f'<a href="{scorecard_url}"><img src="{badge_url}" alt="Compliance Score"/></a>',
                preview_url=badge_url,
            ),
            EmbedSnippet(
                format="rst",
                code=f".. image:: {badge_url}\n   :target: {scorecard_url}\n   :alt: Compliance Score",
                preview_url=badge_url,
            ),
        ]

    def list_scorecards(self, limit: int = 50) -> list[PublicScorecard]:
        return list(self._scorecards.values())[:limit]
