"""Unified global search endpoint.

Searches across regulations, requirements, compliance actions, and
repositories — all scoped to the current user's organization.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import or_, select

from app.api.v1.deps import DB, CurrentOrganization, CurrentUser
from app.models.audit import ComplianceAction
from app.models.codebase import Repository
from app.models.regulation import Regulation
from app.models.requirement import Requirement


logger = structlog.get_logger(__name__)

router = APIRouter()


class SearchResultItem(BaseModel):
    id: str
    type: str  # regulation | requirement | action | repository
    title: str
    description: str | None = None
    url: str


class SearchResponse(BaseModel):
    query: str
    items: list[SearchResultItem]
    total: int
    limit: int
    offset: int


@router.get("", response_model=SearchResponse)
async def global_search(
    user: CurrentUser,
    org: CurrentOrganization,
    db: DB,
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """Search across all core entities, scoped to the current organization."""
    pattern = f"%{q}%"
    results: list[SearchResultItem] = []

    # Regulations (global — not org-scoped)
    reg_stmt = (
        select(Regulation)
        .where(
            or_(
                Regulation.name.ilike(pattern),
                Regulation.content_summary.ilike(pattern),
            )
        )
        .limit(limit)
    )
    regs = (await db.execute(reg_stmt)).scalars().all()
    for reg in regs:
        results.append(
            SearchResultItem(
                id=str(reg.id),
                type="regulation",
                title=reg.name,
                description=(reg.content_summary or "")[:200],
                url=f"/dashboard/regulations/{reg.id}",
            )
        )

    # Requirements
    req_stmt = (
        select(Requirement)
        .where(
            or_(
                Requirement.title.ilike(pattern),
                Requirement.description.ilike(pattern),
            )
        )
        .limit(limit)
    )
    reqs = (await db.execute(req_stmt)).scalars().all()
    for req in reqs:
        results.append(
            SearchResultItem(
                id=str(req.id),
                type="requirement",
                title=req.title,
                description=(req.description or "")[:200],
                url=f"/dashboard/regulations/{req.regulation_id}",
            )
        )

    # Compliance actions (org-scoped)
    action_stmt = (
        select(ComplianceAction)
        .where(
            ComplianceAction.organization_id == org.id,
            or_(
                ComplianceAction.title.ilike(pattern),
                ComplianceAction.description.ilike(pattern),
            ),
        )
        .limit(limit)
    )
    actions = (await db.execute(action_stmt)).scalars().all()
    for a in actions:
        results.append(
            SearchResultItem(
                id=str(a.id),
                type="action",
                title=a.title,
                description=(a.description or "")[:200],
                url=f"/dashboard/actions/{a.id}",
            )
        )

    # Repositories (linked via customer_profile)
    repo_stmt = (
        select(Repository)
        .where(
            or_(
                Repository.name.ilike(pattern),
                Repository.full_name.ilike(pattern),
            ),
        )
        .limit(limit)
    )
    repos = (await db.execute(repo_stmt)).scalars().all()
    for repo in repos:
        results.append(
            SearchResultItem(
                id=str(repo.id),
                type="repository",
                title=repo.name,
                description=repo.full_name,
                url=f"/dashboard/repositories/{repo.id}",
            )
        )

    # Sort by relevance (title match first) and paginate
    total = len(results)
    paginated = results[offset : offset + limit]

    return {
        "query": q,
        "items": paginated,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
