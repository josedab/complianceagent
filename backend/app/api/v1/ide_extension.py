"""API endpoints for Compliance Copilot IDE Extension."""

from typing import Any

import structlog
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.ide_extension import IDEExtensionService


logger = structlog.get_logger()
router = APIRouter()


class AnalyzeFileRequest(BaseModel):
    file_path: str = Field(...)
    content: str = Field(...)
    frameworks: list[str] = Field(default_factory=list)


class DiagnosticSchema(BaseModel):
    id: str
    file_path: str
    line_start: int
    rule_id: str
    framework: str
    article_ref: str
    severity: str
    message: str
    quick_fixes: list[dict[str, Any]]


class TooltipSchema(BaseModel):
    regulation: str
    article: str
    title: str
    summary: str
    url: str
    obligation_level: str


class PostureSchema(BaseModel):
    file_path: str
    file_score: float
    file_grade: str
    violations: int
    frameworks_affected: list[str]
    repo_score: float
    repo_grade: str


class ExtStatsSchema(BaseModel):
    active_sessions: int
    diagnostics_shown: int
    quick_fixes_applied: int
    tooltips_displayed: int
    files_analyzed: int


@router.post("/analyze-file", response_model=list[DiagnosticSchema], summary="Analyze file for compliance")
async def analyze_file(request: AnalyzeFileRequest, db: DB) -> list[DiagnosticSchema]:
    service = IDEExtensionService(db=db)
    diags = await service.analyze_file(file_path=request.file_path, content=request.content, frameworks=request.frameworks or None)
    return [DiagnosticSchema(id=str(d.id), file_path=d.file_path, line_start=d.line_start, rule_id=d.rule_id, framework=d.framework, article_ref=d.article_ref, severity=d.severity.value, message=d.message, quick_fixes=d.quick_fixes) for d in diags]


@router.get("/tooltip/{regulation}/{article}", response_model=TooltipSchema | None, summary="Get regulation tooltip")
async def get_tooltip(regulation: str, article: str, db: DB) -> TooltipSchema | None:
    service = IDEExtensionService(db=db)
    t = service.get_tooltip(regulation, article)
    if not t:
        return None
    return TooltipSchema(regulation=t.regulation, article=t.article, title=t.title, summary=t.summary, url=t.url, obligation_level=t.obligation_level)


@router.get("/posture/{file_path:path}", response_model=PostureSchema, summary="Get file posture")
async def get_posture(file_path: str, db: DB) -> PostureSchema:
    service = IDEExtensionService(db=db)
    p = service.get_posture_sidebar(file_path)
    return PostureSchema(file_path=p.file_path, file_score=p.file_score, file_grade=p.file_grade, violations=p.violations, frameworks_affected=p.frameworks_affected, repo_score=p.repo_score, repo_grade=p.repo_grade)


@router.get("/stats", response_model=ExtStatsSchema, summary="Get extension stats")
async def get_stats(db: DB) -> ExtStatsSchema:
    service = IDEExtensionService(db=db)
    s = service.get_stats()
    return ExtStatsSchema(active_sessions=s.active_sessions, diagnostics_shown=s.diagnostics_shown, quick_fixes_applied=s.quick_fixes_applied, tooltips_displayed=s.tooltips_displayed, files_analyzed=s.files_analyzed)
