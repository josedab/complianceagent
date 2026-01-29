"""Enterprise SSO API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models import Organization, User
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Configure SAML for organization."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    org = current_user.organization

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
async def saml_login(org_slug: str, db: AsyncSession = Depends(get_db)) -> RedirectResponse:
    """Initiate SAML login flow."""
    from sqlalchemy import select

    result = await db.execute(
        select(Organization).where(Organization.slug == org_slug)
    )
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
async def saml_acs(request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """SAML Assertion Consumer Service - process SAML response."""
    form_data = await request.form()
    saml_response = form_data.get("SAMLResponse")
    relay_state = form_data.get("RelayState")  # org_slug

    if not saml_response or not relay_state:
        raise HTTPException(status_code=400, detail="Invalid SAML response")

    from sqlalchemy import select

    result = await db.execute(
        select(Organization).where(Organization.slug == relay_state)
    )
    org = result.scalar_one_or_none()

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

    # Find or create user
    result = await db.execute(
        select(User).where(
            User.email == assertion.email,
            User.organization_id == org.id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        # Auto-provision user via SAML
        user = User(
            email=assertion.email,
            full_name=assertion.attributes.get("displayName", assertion.email.split("@")[0]),
            organization_id=org.id,
            role="member",
            is_active=True,
            hashed_password="",  # SAML users don't have local passwords
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Generate tokens
    from app.core.security import create_access_token, create_refresh_token

    access_token = create_access_token(
        data={"sub": str(user.id), "org": str(org.id)}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.delete("/saml/configure")
async def disable_saml(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Disable SAML for organization."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    org = current_user.organization

    if org.settings and "saml" in org.settings:
        org.settings["saml"]["enabled"] = False
        await db.commit()

    return {"message": "SAML disabled successfully"}
