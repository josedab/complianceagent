"""Regulation endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.v1.deps import DB, OrgMember
from app.models.regulation import (
    Jurisdiction,
    Regulation,
    RegulatoryFramework,
    RegulatorySource,
)
from app.models.requirement import Requirement
from app.schemas.regulation import (
    RegulationCreate,
    RegulationRead,
    RegulationSummary,
    RegulatorySourceCreate,
    RegulatorySourceRead,
)


router = APIRouter()


# Regulatory Sources
@router.get("/sources", response_model=list[RegulatorySourceRead])
async def list_regulatory_sources(
    db: DB,
    jurisdiction: Jurisdiction | None = None,
    framework: RegulatoryFramework | None = None,
    is_active: bool | None = True,
) -> list[RegulatorySource]:
    """List regulatory sources."""
    query = select(RegulatorySource)

    if jurisdiction:
        query = query.where(RegulatorySource.jurisdiction == jurisdiction)
    if framework:
        query = query.where(RegulatorySource.framework == framework)
    if is_active is not None:
        query = query.where(RegulatorySource.is_active == is_active)

    result = await db.execute(query.order_by(RegulatorySource.name))
    return list(result.scalars().all())


@router.post("/sources", response_model=RegulatorySourceRead, status_code=status.HTTP_201_CREATED)
async def create_regulatory_source(
    source_in: RegulatorySourceCreate,
    member: OrgMember,
    db: DB,
) -> RegulatorySource:
    """Create a new regulatory source."""
    source = RegulatorySource(**source_in.model_dump())
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return source


@router.get("/sources/{source_id}", response_model=RegulatorySourceRead)
async def get_regulatory_source(
    source_id: UUID,
    db: DB,
) -> RegulatorySource:
    """Get regulatory source details."""
    result = await db.execute(
        select(RegulatorySource).where(RegulatorySource.id == source_id)
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regulatory source not found",
        )

    return source


# Regulations
@router.get("/", response_model=list[RegulationSummary])
async def list_regulations(
    db: DB,
    jurisdiction: Jurisdiction | None = None,
    framework: RegulatoryFramework | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[dict]:
    """List regulations with optional filters."""
    query = select(Regulation)

    if jurisdiction:
        query = query.where(Regulation.jurisdiction == jurisdiction)
    if framework:
        query = query.where(Regulation.framework == framework)

    query = query.order_by(Regulation.effective_date.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    regulations = result.scalars().all()

    # Get requirement counts
    summaries = []
    for reg in regulations:
        count_result = await db.execute(
            select(func.count()).where(Requirement.regulation_id == reg.id)
        )
        req_count = count_result.scalar() or 0
        summaries.append({
            **RegulationSummary.model_validate(reg).model_dump(),
            "requirements_count": req_count,
        })

    return summaries


@router.post("/", response_model=RegulationRead, status_code=status.HTTP_201_CREATED)
async def create_regulation(
    reg_in: RegulationCreate,
    member: OrgMember,
    db: DB,
) -> Regulation:
    """Create a new regulation."""
    regulation = Regulation(**reg_in.model_dump())
    db.add(regulation)
    await db.flush()
    await db.refresh(regulation)
    return regulation


@router.get("/{regulation_id}", response_model=RegulationRead)
async def get_regulation(
    regulation_id: UUID,
    db: DB,
) -> dict:
    """Get regulation details."""
    result = await db.execute(
        select(Regulation)
        .options(selectinload(Regulation.requirements))
        .where(Regulation.id == regulation_id)
    )
    regulation = result.scalar_one_or_none()

    if not regulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regulation not found",
        )

    return {
        **RegulationRead.model_validate(regulation).model_dump(),
        "requirements_count": len(regulation.requirements),
    }


@router.get("/{regulation_id}/requirements", response_model=list)
async def get_regulation_requirements(
    regulation_id: UUID,
    db: DB,
) -> list[Requirement]:
    """Get requirements for a regulation."""
    result = await db.execute(
        select(Requirement)
        .where(Requirement.regulation_id == regulation_id)
        .order_by(Requirement.reference_id)
    )
    return list(result.scalars().all())
