"""API endpoints for Regulation Changelog Diff Viewer."""

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.regulation_diff import RegulationDiffService

logger = structlog.get_logger()
router = APIRouter()


# --- Response Models ---

class RegulationVersionSchema(BaseModel):
    id: str
    regulation: str
    version: str
    title: str
    effective_date: str
    total_articles: int
    total_words: int
    source_url: str


class ArticleChangeSchema(BaseModel):
    article: str
    section: str
    change_type: str
    severity: str
    old_text: str
    new_text: str
    summary: str
    impact_on_code: str
    affected_controls: list[str]


class RegulationDiffSchema(BaseModel):
    id: str
    regulation: str
    from_version: str
    to_version: str
    total_changes: int
    critical_changes: int
    articles_added: int
    articles_removed: int
    articles_modified: int
    ai_summary: str
    impact_assessment: str
    changes: list[ArticleChangeSchema]


class RegulationDiffSummarySchema(BaseModel):
    id: str
    regulation: str
    from_version: str
    to_version: str
    total_changes: int
    critical_changes: int
    ai_summary: str


# --- Endpoints ---

@router.get("/versions", response_model=list[RegulationVersionSchema])
async def list_versions(regulation: str | None = Query(None)) -> list[dict]:
    svc = RegulationDiffService()
    versions = await svc.list_versions(regulation=regulation)
    return [
        {"id": v.id, "regulation": v.regulation, "version": v.version,
         "title": v.title, "effective_date": v.effective_date.isoformat(),
         "total_articles": v.total_articles, "total_words": v.total_words,
         "source_url": v.source_url}
        for v in versions
    ]


@router.get("/diffs", response_model=list[RegulationDiffSummarySchema])
async def list_diffs(regulation: str | None = Query(None)) -> list[dict]:
    svc = RegulationDiffService()
    diffs = await svc.list_diffs(regulation=regulation)
    return [
        {"id": d.id, "regulation": d.regulation, "from_version": d.from_version,
         "to_version": d.to_version, "total_changes": d.total_changes,
         "critical_changes": d.critical_changes, "ai_summary": d.ai_summary}
        for d in diffs
    ]


@router.get("/diffs/{diff_id}", response_model=RegulationDiffSchema)
async def get_diff(diff_id: str) -> dict:
    svc = RegulationDiffService()
    d = await svc.get_diff(diff_id)
    if not d:
        raise HTTPException(status_code=404, detail="Diff not found")
    return {
        "id": d.id, "regulation": d.regulation, "from_version": d.from_version,
        "to_version": d.to_version, "total_changes": d.total_changes,
        "critical_changes": d.critical_changes, "articles_added": d.articles_added,
        "articles_removed": d.articles_removed, "articles_modified": d.articles_modified,
        "ai_summary": d.ai_summary, "impact_assessment": d.impact_assessment,
        "changes": [
            {"article": c.article, "section": c.section,
             "change_type": c.change_type.value, "severity": c.severity.value,
             "old_text": c.old_text, "new_text": c.new_text, "summary": c.summary,
             "impact_on_code": c.impact_on_code, "affected_controls": c.affected_controls}
            for c in d.changes
        ],
    }


@router.get("/compare", response_model=RegulationDiffSchema)
async def compare_versions(
    from_version: str = Query(..., description="Source version ID"),
    to_version: str = Query(..., description="Target version ID"),
) -> dict:
    svc = RegulationDiffService()
    d = await svc.compare_versions(from_version, to_version)
    if not d:
        raise HTTPException(status_code=404, detail="Version comparison not found")
    return {
        "id": d.id, "regulation": d.regulation, "from_version": d.from_version,
        "to_version": d.to_version, "total_changes": d.total_changes,
        "critical_changes": d.critical_changes, "articles_added": d.articles_added,
        "articles_removed": d.articles_removed, "articles_modified": d.articles_modified,
        "ai_summary": d.ai_summary, "impact_assessment": d.impact_assessment,
        "changes": [
            {"article": c.article, "section": c.section,
             "change_type": c.change_type.value, "severity": c.severity.value,
             "old_text": c.old_text, "new_text": c.new_text, "summary": c.summary,
             "impact_on_code": c.impact_on_code, "affected_controls": c.affected_controls}
            for c in d.changes
        ],
    }
