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
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import decode_token
from app.models.organization import Organization, OrganizationMember
from app.models.production_features import APIKeyRecord
from app.models.user import User


if TYPE_CHECKING:
    from app.agents.copilot import CopilotClient
    from app.agents.orchestrator import ComplianceOrchestrator
    from app.agents.relevance_filter import RelevanceFilter
    from app.services.audit.service import AuditService
    from app.services.generation.generator import CodeGenerationService


logger = structlog.get_logger(__name__)

security = HTTPBearer(auto_error=False)


def _get_access_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    """Read an access token from a bearer header or HttpOnly cookie."""
    if credentials and credentials.credentials:
        return credentials.credentials
    return request.cookies.get("access_token")


async def _get_api_key_record(db: AsyncSession, raw_key: str) -> APIKeyRecord:
    """Resolve and validate an API key without changing usage counters."""
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
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
    if api_key.expires_at and api_key.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )
    if api_key.organization_id and api_key.created_by:
        membership = await db.execute(
            select(OrganizationMember.id).where(
                OrganizationMember.organization_id == api_key.organization_id,
                OrganizationMember.user_id == api_key.created_by,
            )
        )
        if membership.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key owner is no longer a member of the organization",
            )
    return api_key


def _enforce_api_key_scope(api_key: APIKeyRecord, request: Request) -> None:
    """Require a read or write scope appropriate for the HTTP method."""
    key_scopes = set(api_key.scopes or [])
    is_read = request.method.upper() in ("GET", "HEAD", "OPTIONS")
    action = "read" if is_read else "write"
    path = request.url.path
    namespace = None
    namespace_prefixes = {
        "regulations": ("/api/v1/regulations", "/api/v1/requirements"),
        "repositories": ("/api/v1/repositories",),
        "audit": ("/api/v1/audit", "/api/v1/audit-reports"),
        "billing": ("/api/v1/billing",),
        "compliance": (
            "/api/v1/compliance",
            "/api/v1/ide",
            "/api/v1/actions",
            "/api/v1/notifications",
        ),
    }
    for candidate, prefixes in namespace_prefixes.items():
        if path.startswith(prefixes):
            namespace = candidate
            break

    has_scope = action in key_scopes or (
        namespace is not None and f"{action}:{namespace}" in key_scopes
    )
    if key_scopes and not has_scope:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"API key does not have {action} access"
                + (f" for {namespace}" if namespace else " for this endpoint")
            ),
        )


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
    access_token = _get_access_token(request, credentials)
    if access_token:
        token_payload = decode_token(access_token)
        if not token_payload or token_payload.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        result = await db.execute(
            select(User)
            .options(selectinload(User.memberships))
            .where(User.id == UUID(token_payload.sub))
        )
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
        api_key = await _get_api_key_record(db, x_api_key)
        _enforce_api_key_scope(api_key, request)

        # Update usage stats
        api_key.last_used_at = datetime.now(UTC)
        api_key.usage_count = (api_key.usage_count or 0) + 1

        # Resolve the creator when available; fall back to an active org member
        # for keys created before ownership tracking was introduced.
        if api_key.created_by:
            user_result = await db.execute(
                select(User)
                .options(selectinload(User.memberships))
                .where(
                    User.id == api_key.created_by,
                    User.is_active.is_(True),
                )
            )
            user = user_result.scalar_one_or_none()
            if user:
                logger.debug("auth.api_key", key_prefix=api_key.key_prefix, user=user.email)
                return user
        elif api_key.organization_id:
            member_result = await db.execute(
                select(OrganizationMember)
                .where(OrganizationMember.organization_id == api_key.organization_id)
                .order_by(OrganizationMember.created_at.asc())
                .limit(1)
            )
            member = member_result.scalar_one_or_none()
            if member:
                user_result = await db.execute(
                    select(User)
                    .options(selectinload(User.memberships))
                    .where(User.id == member.user_id, User.is_active.is_(True))
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
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
    x_api_key: str | None = Header(None),
) -> Organization:
    """Get the current organization from an access token or API key."""
    access_token = _get_access_token(request, credentials)
    token_payload = decode_token(access_token) if access_token else None

    organization_id: UUID | None = None
    token_user_id: UUID | None = None
    if token_payload and token_payload.type == "access" and token_payload.org_id:
        organization_id = UUID(token_payload.org_id)
        token_user_id = UUID(token_payload.sub)
    elif x_api_key:
        api_key = await _get_api_key_record(db, x_api_key)
        _enforce_api_key_scope(api_key, request)
        organization_id = api_key.organization_id

    if organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No organization context",
        )

    if token_user_id is not None:
        membership = await db.execute(
            select(OrganizationMember.id).where(
                OrganizationMember.user_id == token_user_id,
                OrganizationMember.organization_id == organization_id,
            )
        )
        if membership.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Organization membership is no longer active",
            )

    result = await db.execute(select(Organization).where(Organization.id == organization_id))
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
def get_copilot_client() -> CopilotClient:
    """Factory for CopilotClient - lazy import to avoid circular deps."""
    from app.agents.copilot import CopilotClient

    return CopilotClient()


def get_audit_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuditService:
    """Factory for AuditService."""
    from app.services.audit.service import AuditService

    return AuditService(db)


def get_relevance_filter() -> RelevanceFilter:
    """Factory for RelevanceFilter."""
    from app.agents.relevance_filter import RelevanceFilter

    return RelevanceFilter()


def get_compliance_orchestrator(
    db: Annotated[AsyncSession, Depends(get_db)],
    organization: Annotated[Organization, Depends(get_current_organization)],
) -> ComplianceOrchestrator:
    """Factory for ComplianceOrchestrator with dependencies injected."""
    from app.agents.orchestrator import ComplianceOrchestrator

    return ComplianceOrchestrator(
        db=db,
        organization_id=organization.id,
        copilot=get_copilot_client(),
        relevance_filter=get_relevance_filter(),
    )


def get_code_generation_service() -> CodeGenerationService:
    """Factory for CodeGenerationService."""
    from app.services.generation.generator import CodeGenerationService

    return CodeGenerationService(copilot_client=get_copilot_client())


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
