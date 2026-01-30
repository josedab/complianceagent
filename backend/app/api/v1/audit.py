"""Audit trail endpoints."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.v1.deps import DB, CurrentOrganization, OrgMember
from app.models.audit import AuditEventType, AuditTrail, ComplianceAction, ComplianceActionStatus
from app.schemas.audit import (
    AuditTrailRead,
    ComplianceActionCreate,
    ComplianceActionRead,
    ComplianceActionUpdate,
)


router = APIRouter()


@router.get("/trail", response_model=list[AuditTrailRead])
async def list_audit_trail(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    regulation_id: UUID | None = None,
    requirement_id: UUID | None = None,
    event_type: AuditEventType | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[AuditTrail]:
    """List audit trail entries."""
    query = select(AuditTrail).where(AuditTrail.organization_id == organization.id)

    if regulation_id:
        query = query.where(AuditTrail.regulation_id == regulation_id)
    if requirement_id:
        query = query.where(AuditTrail.requirement_id == requirement_id)
    if event_type:
        query = query.where(AuditTrail.event_type == event_type)
    if start_date:
        query = query.where(AuditTrail.created_at >= start_date)
    if end_date:
        query = query.where(AuditTrail.created_at <= end_date)

    query = query.order_by(AuditTrail.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/trail/{entry_id}", response_model=AuditTrailRead)
async def get_audit_entry(
    entry_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> AuditTrail:
    """Get audit trail entry details."""
    result = await db.execute(
        select(AuditTrail).where(
            AuditTrail.id == entry_id,
            AuditTrail.organization_id == organization.id,
        )
    )
    entry = result.scalar_one_or_none()

    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit entry not found",
        )

    return entry


# Compliance Actions
@router.get("/actions", response_model=list[ComplianceActionRead])
async def list_compliance_actions(
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
    status_filter: ComplianceActionStatus | None = None,
    repository_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[ComplianceAction]:
    """List compliance actions."""
    query = select(ComplianceAction).where(ComplianceAction.organization_id == organization.id)

    if status_filter:
        query = query.where(ComplianceAction.status == status_filter)
    if repository_id:
        query = query.where(ComplianceAction.repository_id == repository_id)

    query = query.order_by(ComplianceAction.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/actions", response_model=ComplianceActionRead, status_code=status.HTTP_201_CREATED)
async def create_compliance_action(
    action_in: ComplianceActionCreate,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ComplianceAction:
    """Create a compliance action."""
    action = ComplianceAction(
        organization_id=organization.id,
        **action_in.model_dump(),
    )
    db.add(action)
    await db.flush()
    await db.refresh(action)
    return action


@router.get("/actions/{action_id}", response_model=ComplianceActionRead)
async def get_compliance_action(
    action_id: UUID,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ComplianceAction:
    """Get compliance action details."""
    result = await db.execute(
        select(ComplianceAction).where(
            ComplianceAction.id == action_id,
            ComplianceAction.organization_id == organization.id,
        )
    )
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance action not found",
        )

    return action


@router.patch("/actions/{action_id}", response_model=ComplianceActionRead)
async def update_compliance_action(
    action_id: UUID,
    action_in: ComplianceActionUpdate,
    organization: CurrentOrganization,
    member: OrgMember,
    db: DB,
) -> ComplianceAction:
    """Update compliance action."""
    result = await db.execute(
        select(ComplianceAction).where(
            ComplianceAction.id == action_id,
            ComplianceAction.organization_id == organization.id,
        )
    )
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance action not found",
        )

    update_data = action_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(action, field, value)

    await db.flush()
    await db.refresh(action)

    return action
