"""Codebase mapping endpoints."""

from datetime import UTC
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.models.codebase import CodebaseMapping, ComplianceStatus, Repository
from app.models.customer_profile import CustomerProfile
from app.schemas.codebase import CodebaseMappingRead


router = APIRouter()


@router.get("/", response_model=list[CodebaseMappingRead])
async def list_mappings(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    repository_id: UUID | None = None,
    requirement_id: UUID | None = None,
    compliance_status: ComplianceStatus | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[CodebaseMapping]:
    """List codebase mappings."""
    query = (
        select(CodebaseMapping)
        .join(Repository)
        .join(CustomerProfile)
        .where(CustomerProfile.organization_id == organization.id)
    )

    if repository_id:
        query = query.where(CodebaseMapping.repository_id == repository_id)
    if requirement_id:
        query = query.where(CodebaseMapping.requirement_id == requirement_id)
    if compliance_status:
        query = query.where(CodebaseMapping.compliance_status == compliance_status)

    query = query.order_by(CodebaseMapping.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{mapping_id}", response_model=CodebaseMappingRead)
async def get_mapping(
    mapping_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> CodebaseMapping:
    """Get mapping details."""
    result = await db.execute(
        select(CodebaseMapping)
        .options(
            selectinload(CodebaseMapping.repository).selectinload(Repository.customer_profile)
        )
        .where(CodebaseMapping.id == mapping_id)
    )
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found",
        )

    if mapping.repository.customer_profile.organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mapping not accessible",
        )

    return mapping


@router.post("/{mapping_id}/review", response_model=CodebaseMappingRead)
async def review_mapping(
    mapping_id: UUID,
    compliance_status: ComplianceStatus,
    notes: str | None = None,
    organization: CurrentOrganization = None,
    member: OrgMember = None,
    db: DB = None,
) -> CodebaseMapping:
    """Review and update mapping compliance status."""
    from datetime import datetime

    result = await db.execute(
        select(CodebaseMapping)
        .options(
            selectinload(CodebaseMapping.repository).selectinload(Repository.customer_profile)
        )
        .where(CodebaseMapping.id == mapping_id)
    )
    mapping = result.scalar_one_or_none()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapping not found",
        )

    if mapping.repository.customer_profile.organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mapping not accessible",
        )

    mapping.compliance_status = compliance_status
    mapping.compliance_notes = notes
    mapping.human_reviewed = True
    mapping.reviewed_at = datetime.now(UTC)
    # mapping.reviewed_by = str(member.user_id)

    await db.flush()
    await db.refresh(mapping)

    return mapping
