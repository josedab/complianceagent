"""API dependencies."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

import structlog
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.organization import Organization, OrganizationMember
from app.models.production_features import APIKeyRecord
from app.models.user import User


if TYPE_CHECKING:
    from app.agents.copilot import CopilotClient
    from app.agents.orchestrator import ComplianceOrchestrator
    from app.services.audit.service import AuditService


logger = structlog.get_logger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
    x_api_key: str | None = Header(None),
) -> User:
    """Get the current authenticated user via JWT or API key.

    Supports two authentication methods:
    1. Bearer JWT token in the Authorization header
    2. API key in the X-API-Key header

    JWT is checked first; if absent, falls back to API key lookup.
    API key requests are validated against the key's scopes.
    """
    # --- Path 1: JWT Bearer token ---
    if credentials and credentials.credentials:
        token_payload = decode_token(credentials.credentials)
        if not token_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        result = await db.execute(select(User).where(User.id == UUID(token_payload.sub)))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive",
            )

        return user

    # --- Path 2: API key ---
    if x_api_key:
        key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
        result = await db.execute(
            select(APIKeyRecord).where(
                APIKeyRecord.key_hash == key_hash,
                APIKeyRecord.status == "active",
            )
        )
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )

        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired",
            )

        # Enforce scopes: "read" allows GET/HEAD/OPTIONS; "write" allows all methods
        key_scopes = set(api_key.scopes or [])
        method = request.method.upper()
        is_read = method in ("GET", "HEAD", "OPTIONS")
        if key_scopes and "write" not in key_scopes and not is_read:
            if not any(s.startswith("write") for s in key_scopes):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="API key does not have write scope",
                )
        if key_scopes and "read" not in key_scopes and is_read:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key does not have read scope",
            )

        # Update usage stats
        api_key.last_used_at = datetime.now(UTC)
        api_key.usage_count = (api_key.usage_count or 0) + 1

        # Resolve a user from the API key's organization
        if api_key.organization_id:
            member_result = await db.execute(
                select(OrganizationMember)
                .where(OrganizationMember.organization_id == api_key.organization_id)
                .order_by(OrganizationMember.created_at.asc())
                .limit(1)
            )
            member = member_result.scalar_one_or_none()
            if member:
                user_result = await db.execute(
                    select(User).where(User.id == member.user_id, User.is_active.is_(True))
                )
                user = user_result.scalar_one_or_none()
                if user:
                    logger.debug("auth.api_key", key_prefix=api_key.key_prefix, user=user.email)
                    return user

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has no associated user",
        )

    # --- No credentials ---
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_organization(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Organization:
    """Get the current organization from token."""
    token_payload = decode_token(credentials.credentials)
    if not token_payload or not token_payload.org_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No organization context",
        )

    result = await db.execute(
        select(Organization).where(Organization.id == UUID(token_payload.org_id))
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return organization


async def require_org_member(
    user: Annotated[User, Depends(get_current_user)],
    organization: Annotated[Organization, Depends(get_current_organization)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrganizationMember:
    """Require the user to be a member of the organization."""
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.user_id == user.id,
            OrganizationMember.organization_id == organization.id,
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )

    return member


async def require_org_admin(
    member: Annotated[OrganizationMember, Depends(require_org_member)],
) -> OrganizationMember:
    """Require the user to be an admin of the organization."""
    if member.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return member


# Service factory functions for proper dependency injection
def get_copilot_client():
    """Factory for CopilotClient - lazy import to avoid circular deps."""
    from app.agents.copilot import CopilotClient

    return CopilotClient()


def get_audit_service(db: Annotated[AsyncSession, Depends(get_db)]):
    """Factory for AuditService."""
    from app.services.audit.service import AuditService

    return AuditService(db)


def get_relevance_filter():
    """Factory for RelevanceFilter."""
    from app.agents.relevance_filter import RelevanceFilter

    return RelevanceFilter()


def get_compliance_orchestrator(
    db: Annotated[AsyncSession, Depends(get_db)],
    organization: Annotated[Organization, Depends(get_current_organization)],
):
    """Factory for ComplianceOrchestrator with dependencies injected."""
    from app.agents.orchestrator import ComplianceOrchestrator

    return ComplianceOrchestrator(
        db=db,
        organization_id=organization.id,
        copilot=get_copilot_client(),
        relevance_filter=get_relevance_filter(),
    )


def get_code_generation_service():
    """Factory for CodeGenerationService."""
    from app.services.generation.generator import CodeGenerationService

    return CodeGenerationService(copilot=get_copilot_client())


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentOrganization = Annotated[Organization, Depends(get_current_organization)]
OrgMember = Annotated[OrganizationMember, Depends(require_org_member)]
OrgAdmin = Annotated[OrganizationMember, Depends(require_org_admin)]
DB = Annotated[AsyncSession, Depends(get_db)]

# Service type aliases (use string literals for forward references)
CopilotDep = Annotated["CopilotClient", Depends(get_copilot_client)]
AuditServiceDep = Annotated["AuditService", Depends(get_audit_service)]
OrchestratorDep = Annotated["ComplianceOrchestrator", Depends(get_compliance_orchestrator)]
