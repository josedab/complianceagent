"""Requirement endpoints."""

from datetime import UTC
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.v1.deps import DB, OrgMember
from app.models.requirement import ObligationType, Requirement, RequirementCategory
from app.schemas.requirement import RequirementCreate, RequirementRead


router = APIRouter()


@router.get("/", response_model=list[RequirementRead])
async def list_requirements(
    db: DB,
    regulation_id: UUID | None = None,
    category: RequirementCategory | None = None,
    obligation_type: ObligationType | None = None,
    human_reviewed: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[Requirement]:
    """List requirements with optional filters."""
    query = select(Requirement)

    if regulation_id:
        query = query.where(Requirement.regulation_id == regulation_id)
    if category:
        query = query.where(Requirement.category == category)
    if obligation_type:
        query = query.where(Requirement.obligation_type == obligation_type)
    if human_reviewed is not None:
        query = query.where(Requirement.human_reviewed == human_reviewed)

    query = query.order_by(Requirement.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/", response_model=RequirementRead, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    req_in: RequirementCreate,
    member: OrgMember,
    db: DB,
) -> Requirement:
    """Create a new requirement."""
    requirement = Requirement(**req_in.model_dump())
    db.add(requirement)
    await db.flush()
    await db.refresh(requirement)
    return requirement


@router.get("/{requirement_id}", response_model=RequirementRead)
async def get_requirement(
    requirement_id: UUID,
    db: DB,
) -> Requirement:
    """Get requirement details."""
    result = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id)
    )
    requirement = result.scalar_one_or_none()

    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    return requirement


@router.post("/{requirement_id}/review", response_model=RequirementRead)
async def review_requirement(
    requirement_id: UUID,
    approved: bool,
    notes: str | None = None,
    member: OrgMember = None,
    db: DB = None,
) -> Requirement:
    """Mark requirement as human reviewed."""
    from datetime import datetime

    result = await db.execute(
        select(Requirement).where(Requirement.id == requirement_id)
    )
    requirement = result.scalar_one_or_none()

    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    requirement.human_reviewed = True
    requirement.reviewed_at = datetime.now(UTC)
    # requirement.reviewed_by = str(member.user_id)

    await db.flush()
    await db.refresh(requirement)

    return requirement
