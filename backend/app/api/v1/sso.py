"""Enterprise SSO API routes."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.api.v1.deps import DB, OrgAdmin
from app.core.security import create_access_token, create_refresh_token
from app.models.organization import MemberRole, Organization, OrganizationMember
from app.models.user import User
from app.services.enterprise import SAMLConfig, saml_service


router = APIRouter()


class SAMLConfigCreate(BaseModel):
    """SAML configuration create request."""

    entity_id: str
    sso_url: str
    slo_url: str | None = None
    certificate: str
    attribute_mapping: dict[str, str] = {}


@router.get("/saml/metadata")
async def get_saml_metadata() -> Response:
    """Get SAML Service Provider metadata."""
    metadata = saml_service.generate_metadata()
    return Response(
        content=metadata,
        media_type="application/xml",
    )


@router.post("/saml/configure")
async def configure_saml(
    config: SAMLConfigCreate,
    admin: OrgAdmin,
    db: DB,
) -> dict[str, str]:
    """Configure SAML for organization."""
    result = await db.execute(select(Organization).where(Organization.id == admin.organization_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Store SAML config in org settings
    org.settings = org.settings or {}
    org.settings["saml"] = {
        "entity_id": config.entity_id,
        "sso_url": config.sso_url,
        "slo_url": config.slo_url,
        "certificate": config.certificate,
        "attribute_mapping": config.attribute_mapping,
        "enabled": True,
    }

    await db.commit()

    return {"message": "SAML configuration saved successfully"}


@router.get("/saml/login/{org_slug}")
async def saml_login(org_slug: str, db: DB) -> RedirectResponse:
    """Initiate SAML login flow."""
    result = await db.execute(select(Organization).where(Organization.slug == org_slug))
    org = result.scalar_one_or_none()

    if not org or not org.settings.get("saml", {}).get("enabled"):
        raise HTTPException(status_code=404, detail="SAML not configured for this organization")

    saml_settings = org.settings["saml"]
    config = SAMLConfig(
        entity_id=saml_settings["entity_id"],
        sso_url=saml_settings["sso_url"],
        slo_url=saml_settings.get("slo_url"),
        certificate=saml_settings["certificate"],
        attribute_mapping=saml_settings.get("attribute_mapping", {}),
    )

    auth_request = saml_service.generate_auth_request(
        config=config,
        relay_state=org_slug,
    )

    # Redirect to IdP with SAML request
    redirect_url = f"{auth_request['sso_url']}?SAMLRequest={auth_request['saml_request']}&RelayState={auth_request['relay_state']}"
    return RedirectResponse(url=redirect_url)


@router.post("/saml/acs")
async def saml_acs(request: Request, db: DB) -> dict[str, Any]:
    """SAML Assertion Consumer Service - process SAML response."""
    form_data = await request.form()
    saml_response = form_data.get("SAMLResponse")
    relay_state = form_data.get("RelayState")  # org_slug

    if not saml_response or not relay_state:
        raise HTTPException(status_code=400, detail="Invalid SAML response")

    org_result = await db.execute(select(Organization).where(Organization.slug == relay_state))
    org = org_result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    saml_settings = org.settings.get("saml", {})
    config = SAMLConfig(
        entity_id=saml_settings["entity_id"],
        sso_url=saml_settings["sso_url"],
        slo_url=saml_settings.get("slo_url"),
        certificate=saml_settings["certificate"],
        attribute_mapping=saml_settings.get("attribute_mapping", {}),
    )

    try:
        assertion = saml_service.parse_response(str(saml_response), config)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e

    # Find or create the user by email (User has no direct org/role columns;
    # organization membership is tracked via OrganizationMember).
    user_result = await db.execute(select(User).where(User.email == assertion.email))
    user = user_result.scalar_one_or_none()

    if not user:
        # Auto-provision user via SAML
        user = User(
            email=assertion.email,
            full_name=assertion.attributes.get("displayName", assertion.email.split("@")[0]),
            is_active=True,
            is_verified=True,
            hashed_password="",  # SAML users don't have local passwords
        )
        db.add(user)
        await db.flush()

    # Ensure the user has a membership in this organization
    member_result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.user_id == user.id,
            OrganizationMember.organization_id == org.id,
        )
    )
    member = member_result.scalar_one_or_none()
    if not member:
        member = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role=MemberRole.MEMBER,
        )
        db.add(member)

    await db.commit()

    # Generate tokens
    access_token = create_access_token(subject=str(user.id), org_id=str(org.id))
    refresh_token = create_refresh_token(subject=str(user.id), org_id=str(org.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.delete("/saml/configure")
async def disable_saml(
    admin: OrgAdmin,
    db: DB,
) -> dict[str, str]:
    """Disable SAML for organization."""
    result = await db.execute(select(Organization).where(Organization.id == admin.organization_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if org.settings and "saml" in org.settings:
        org.settings["saml"]["enabled"] = False
        await db.commit()

    return {"message": "SAML disabled successfully"}
