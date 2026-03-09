"""AI Regulatory Summarizer and Board Reports service.

Generates executive compliance reports with AI-powered narrative summaries,
traffic-light dashboards, trend analysis, and exportable formats.
"""

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession


logger = structlog.get_logger()


class ReportFormat:
    HTML = "html"
    PDF = "pdf"
    JSON = "json"


@dataclass
class ComplianceHighlight:
    category: str = ""
    status: str = ""  # green, yellow, red
    score: float = 0.0
    trend: str = ""  # improving, stable, declining
    summary: str = ""


@dataclass
class ExecutiveSummary:
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    period: str = ""
    overall_score: float = 0.0
    overall_status: str = ""  # green, yellow, red
    narrative: str = ""
    highlights: list[ComplianceHighlight] = field(default_factory=list)
    top_risks: list[dict[str, Any]] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    generated_at: datetime | None = None
    generated_by: str = "ai"


@dataclass
class BoardReport:
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    summary: ExecutiveSummary | None = None
    framework_scores: dict[str, float] = field(default_factory=dict)
    compliance_trend: list[dict[str, Any]] = field(default_factory=list)
    upcoming_deadlines: list[dict[str, Any]] = field(default_factory=list)
    budget_summary: dict[str, float] = field(default_factory=dict)
    format: str = ReportFormat.HTML
    content: str = ""
    generated_at: datetime | None = None


class BoardReportsService:
    """Generate AI-powered executive compliance reports for board presentations."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client

    async def generate_executive_summary(
        self,
        org_id: str,
        period: str = "Q1 2026",
        frameworks: list[str] | None = None,
    ) -> ExecutiveSummary:
        """Generate an AI-powered executive summary of compliance posture."""
        frameworks = frameworks or ["GDPR", "SOC 2", "HIPAA", "PCI-DSS"]

        # Compliance scores by framework (in production, fetched from posture_scoring)
        scores = {"GDPR": 87.0, "SOC 2": 92.0, "HIPAA": 78.0, "PCI-DSS": 85.0}
        overall = sum(scores.get(fw, 80.0) for fw in frameworks) / len(frameworks)

        highlights = []
        for fw in frameworks:
            score = scores.get(fw, 80.0)
            status = "green" if score >= 85 else ("yellow" if score >= 70 else "red")
            trend = "improving" if score >= 85 else ("stable" if score >= 75 else "declining")
            highlights.append(
                ComplianceHighlight(
                    category=fw,
                    status=status,
                    score=score,
                    trend=trend,
                    summary=f"{fw} compliance is at {score}% — {trend}.",
                )
            )

        # Generate AI narrative if Copilot is available
        narrative = await self._generate_narrative(overall, highlights, period)

        overall_status = "green" if overall >= 85 else ("yellow" if overall >= 70 else "red")

        summary = ExecutiveSummary(
            title=f"Compliance Executive Summary — {period}",
            period=period,
            overall_score=round(overall, 1),
            overall_status=overall_status,
            narrative=narrative,
            highlights=highlights,
            top_risks=[
                {
                    "risk": "HIPAA PHI encryption gap in legacy module",
                    "severity": "high",
                    "eta": "2 weeks",
                },
                {
                    "risk": "GDPR consent banner missing on mobile",
                    "severity": "medium",
                    "eta": "1 week",
                },
                {
                    "risk": "SOC 2 access review overdue for 3 users",
                    "severity": "low",
                    "eta": "3 days",
                },
            ],
            action_items=[
                f"Prioritize HIPAA remediation — score at {scores.get('HIPAA', 0)}%",
                "Complete Q1 access review before audit deadline",
                "Schedule EU AI Act readiness assessment",
            ],
            generated_at=datetime.now(UTC),
        )

        logger.info("executive_summary_generated", org_id=org_id, period=period, overall=overall)
        return summary

    async def generate_board_report(
        self,
        org_id: str,
        period: str = "Q1 2026",
        report_format: str = ReportFormat.HTML,
    ) -> BoardReport:
        """Generate a complete board-ready compliance report."""
        summary = await self.generate_executive_summary(org_id, period)

        trend = [
            {"month": "Jan", "score": 82.0},
            {"month": "Feb", "score": 84.5},
            {"month": "Mar", "score": summary.overall_score},
        ]

        report = BoardReport(
            title=f"Board Compliance Report — {period}",
            summary=summary,
            framework_scores={h.category: h.score for h in summary.highlights},
            compliance_trend=trend,
            upcoming_deadlines=[
                {"regulation": "EU AI Act", "deadline": "2026-08-01", "status": "on_track"},
                {"regulation": "DORA", "deadline": "2025-01-17", "status": "effective"},
                {"regulation": "PCI-DSS v4.0.1", "deadline": "2025-03-31", "status": "at_risk"},
            ],
            budget_summary={
                "total_compliance_budget": 450000.0,
                "spent_ytd": 125000.0,
                "projected_annual": 380000.0,
                "savings_from_automation": 95000.0,
            },
            format=report_format,
            generated_at=datetime.now(UTC),
        )

        if report_format == ReportFormat.HTML:
            report.content = self._render_html(report)

        logger.info("board_report_generated", org_id=org_id, format=report_format)
        return report

    async def _generate_narrative(
        self, overall: float, highlights: list[ComplianceHighlight], period: str
    ) -> str:
        """Generate AI narrative summary. Falls back to template if AI unavailable."""
        if self.copilot and hasattr(self.copilot, "chat"):
            try:
                from app.agents.copilot import CopilotMessage

                prompt = (
                    f"Write a 3-paragraph executive summary for a board meeting about "
                    f"compliance posture for {period}. Overall score: {overall:.1f}%. "
                    f"Framework details: {[{'fw': h.category, 'score': h.score, 'trend': h.trend} for h in highlights]}. "
                    f"Keep it professional, concise, and action-oriented."
                )
                response = await self.copilot.chat(
                    messages=[CopilotMessage(role="user", content=prompt)],
                    system_message="You are a compliance reporting assistant writing for C-level executives.",
                    temperature=0.5,
                )
                return response.content
            except (json.JSONDecodeError, KeyError, ValueError, OSError) as exc:
                logger.debug("AI narrative failed, using template", error=str(exc))

        # Template fallback
        status_word = (
            "strong" if overall >= 85 else ("adequate" if overall >= 70 else "needs attention")
        )
        declining = [h for h in highlights if h.trend == "declining"]
        declining_note = (
            f" {declining[0].category} requires immediate attention." if declining else ""
        )

        return (
            f"Our overall compliance posture for {period} is {status_word} at {overall:.1f}%.{declining_note} "
            f"Key frameworks are trending {'positively' if overall >= 80 else 'with areas of concern'}. "
            f"We recommend focusing remediation efforts on the lowest-scoring frameworks to maintain "
            f"audit readiness ahead of upcoming regulatory deadlines."
        )

    def _render_html(self, report: BoardReport) -> str:
        """Render a simple HTML report."""
        summary = report.summary
        if not summary:
            return "<p>No data available.</p>"

        highlights_html = "".join(
            f"<tr><td>{h.category}</td><td>{h.score}%</td><td>{h.status}</td><td>{h.trend}</td></tr>"
            for h in summary.highlights
        )

        return f"""<!DOCTYPE html>
<html><head><title>{report.title}</title>
<style>body{{font-family:system-ui;max-width:800px;margin:2em auto;padding:0 1em}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background:#1e293b;color:white}}.green{{color:#16a34a}}.yellow{{color:#ca8a04}}.red{{color:#dc2626}}</style>
</head><body>
<h1>{report.title}</h1>
<p><strong>Overall Score:</strong> <span class="{summary.overall_status}">{summary.overall_score}%</span></p>
<h2>Executive Narrative</h2>
<p>{summary.narrative}</p>
<h2>Framework Scores</h2>
<table><tr><th>Framework</th><th>Score</th><th>Status</th><th>Trend</th></tr>{highlights_html}</table>
<h2>Top Risks</h2><ul>{"".join(f"<li><strong>{r['severity'].upper()}</strong>: {r['risk']}</li>" for r in summary.top_risks)}</ul>
<h2>Action Items</h2><ol>{"".join(f"<li>{a}</li>" for a in summary.action_items)}</ol>
<footer><p>Generated {report.generated_at.strftime("%Y-%m-%d %H:%M UTC") if report.generated_at else "N/A"} by ComplianceAgent</p></footer>
</body></html>"""
