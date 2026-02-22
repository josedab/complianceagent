"""Board Reports API endpoints."""

import structlog
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from app.api.v1.deps import DB, CopilotDep
from app.services.board_reports import BoardReportsService


logger = structlog.get_logger()
router = APIRouter()


@router.get("/executive-summary")
async def get_executive_summary(
    db: DB,
    copilot: CopilotDep,
    org_id: str = Query("default"),
    period: str = Query("Q1 2026"),
) -> dict:
    """Generate an AI-powered executive compliance summary."""
    svc = BoardReportsService(db, copilot_client=copilot)
    summary = await svc.generate_executive_summary(org_id, period)
    return {
        "title": summary.title,
        "period": summary.period,
        "overall_score": summary.overall_score,
        "overall_status": summary.overall_status,
        "narrative": summary.narrative,
        "highlights": [{"category": h.category, "score": h.score, "status": h.status, "trend": h.trend} for h in summary.highlights],
        "top_risks": summary.top_risks,
        "action_items": summary.action_items,
    }


@router.get("/report", response_class=HTMLResponse)
async def get_board_report_html(
    db: DB,
    copilot: CopilotDep,
    org_id: str = Query("default"),
    period: str = Query("Q1 2026"),
) -> HTMLResponse:
    """Generate a board-ready HTML compliance report."""
    svc = BoardReportsService(db, copilot_client=copilot)
    report = await svc.generate_board_report(org_id, period, report_format="html")
    return HTMLResponse(content=report.content)


@router.get("/report/json")
async def get_board_report_json(
    db: DB,
    copilot: CopilotDep,
    org_id: str = Query("default"),
    period: str = Query("Q1 2026"),
) -> dict:
    """Generate a board-ready compliance report as JSON."""
    svc = BoardReportsService(db, copilot_client=copilot)
    report = await svc.generate_board_report(org_id, period, report_format="json")
    return {
        "title": report.title,
        "framework_scores": report.framework_scores,
        "compliance_trend": report.compliance_trend,
        "upcoming_deadlines": report.upcoming_deadlines,
        "budget_summary": report.budget_summary,
    }
