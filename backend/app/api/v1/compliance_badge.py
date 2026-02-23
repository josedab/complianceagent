"""API endpoints for Compliance Badge & Scorecard."""

from typing import Any

import structlog
from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

from app.api.v1.deps import DB
from app.services.compliance_badge import ComplianceBadgeService


logger = structlog.get_logger()
router = APIRouter()


class BadgeSchema(BaseModel):
    repo: str
    grade: str
    score: float
    label: str
    color: str
    style: str

class ScorecardSchema(BaseModel):
    id: str
    repo: str
    overall_score: float
    overall_grade: str
    frameworks: list[dict[str, Any]]
    trend: list[dict[str, Any]]
    last_scan_at: str | None
    is_public: bool

class EmbedSnippetSchema(BaseModel):
    format: str
    code: str
    preview_url: str


@router.get("/badge/{repo:path}.svg", summary="Get SVG badge", response_class=Response)
async def get_badge_svg(repo: str, db: DB, style: str = "flat", label: str = "compliance") -> Response:
    service = ComplianceBadgeService(db=db)
    badge = await service.generate_badge(repo=repo, style=style, label=label)
    return Response(content=badge.svg, media_type="image/svg+xml", headers={"Cache-Control": "max-age=300"})

@router.get("/badge/{repo:path}", response_model=BadgeSchema, summary="Get badge data")
async def get_badge(repo: str, db: DB, style: str = "flat", label: str = "compliance") -> BadgeSchema:
    service = ComplianceBadgeService(db=db)
    badge = await service.generate_badge(repo=repo, style=style, label=label)
    return BadgeSchema(repo=badge.repo, grade=badge.grade.value, score=badge.score, label=badge.label, color=badge.color, style=badge.style.value)

@router.get("/scorecard/{repo:path}", response_model=ScorecardSchema, summary="Get public scorecard")
async def get_scorecard(repo: str, db: DB) -> ScorecardSchema:
    service = ComplianceBadgeService(db=db)
    sc = await service.get_public_scorecard(repo)
    return ScorecardSchema(
        id=str(sc.id), repo=sc.repo, overall_score=sc.overall_score,
        overall_grade=sc.overall_grade.value, frameworks=sc.frameworks,
        trend=sc.trend,
        last_scan_at=sc.last_scan_at.isoformat() if sc.last_scan_at else None,
        is_public=sc.is_public,
    )

@router.get("/embed/{repo:path}", response_model=list[EmbedSnippetSchema], summary="Get embed snippets")
async def get_embed_snippets(repo: str, db: DB) -> list[EmbedSnippetSchema]:
    service = ComplianceBadgeService(db=db)
    snippets = service.get_embed_snippets(repo)
    return [EmbedSnippetSchema(format=s.format, code=s.code, preview_url=s.preview_url) for s in snippets]
