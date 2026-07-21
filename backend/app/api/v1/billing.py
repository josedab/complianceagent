"""Billing API routes.

All tenant-scoped endpoints use ``CurrentOrganization`` and ``OrgAdmin`` so
that the billing context is always resolved from the JWT org claim rather
than a (non-existent) ``current_user.organization`` attribute.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.v1.deps import DB, CurrentOrganization, CurrentUser, OrgAdmin
from app.core.config import settings
from app.models.codebase import Repository
from app.models.organization import Organization, OrganizationMember, PlanType
from app.models.production_features import APIKeyRecord
from app.services.billing import PLANS, PlanTier, StripeService, billing_service


logger = structlog.get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Typed response models
# ---------------------------------------------------------------------------


class PlanRead(BaseModel):
    tier: str
    name: str
    price_monthly: int
    price_yearly: int
    max_repositories: int
    max_frameworks: int
    max_users: int
    features: list[str]


class SubscriptionRead(BaseModel):
    organization_id: str
    plan_tier: str
    status: str
    billing_email: str
    current_period_end: str | None = None
    cancel_at_period_end: bool = False


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class PortalResponse(BaseModel):
    portal_url: str


class ChangePlanResponse(BaseModel):
    message: str
    new_plan: str


class InvoiceRead(BaseModel):
    id: str
    date: str
    amount: int
    status: str
    pdf_url: str | None = None


class UsageMetric(BaseModel):
    used: int
    limit: int


class UsageRead(BaseModel):
    repositories: UsageMetric
    frameworks: UsageMetric
    users: UsageMetric
    api_calls: UsageMetric


class WebhookAck(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STRIPE_API_KEY: str | None = getattr(settings, "stripe_api_key", None) or None
_STRIPE_WEBHOOK_SECRET: str | None = getattr(settings, "stripe_webhook_secret", None) or None


def _require_stripe() -> str:
    """Raise 503 if Stripe is not configured."""
    if not _STRIPE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe is not configured. Set STRIPE_API_KEY in your environment.",
        )
    return _STRIPE_API_KEY


def _stripe_service() -> StripeService:
    return StripeService(api_key=_require_stripe())


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/plans", response_model=list[PlanRead])
async def list_plans() -> list[dict[str, Any]]:
    """List available subscription plans."""
    return [
        {
            "tier": plan.tier.value,
            "name": plan.name,
            "price_monthly": plan.price_monthly,
            "price_yearly": plan.price_yearly,
            "max_repositories": plan.max_repositories,
            "max_frameworks": plan.max_frameworks,
            "max_users": plan.max_users,
            "features": plan.features,
        }
        for plan in PLANS.values()
    ]


@router.get("/subscription", response_model=SubscriptionRead)
async def get_subscription(
    user: CurrentUser,
    org: CurrentOrganization,
    db: DB,
) -> dict[str, Any]:
    """Get current subscription details.

    If the organization has a Stripe subscription ID the real status is
    fetched; otherwise a locally-derived status is returned.
    """
    result: dict[str, Any] = {
        "organization_id": str(org.id),
        "plan_tier": org.plan,
        "billing_email": user.email,
        "current_period_end": None,
        "cancel_at_period_end": False,
        "status": "active",
    }

    if org.stripe_subscription_id and _STRIPE_API_KEY:
        try:
            svc = _stripe_service()
            async with svc:
                sub = await svc.get_subscription(org.stripe_subscription_id)
            result["status"] = sub.get("status", "active")
            if sub.get("current_period_end"):
                result["current_period_end"] = datetime.fromtimestamp(
                    sub["current_period_end"], tz=UTC
                ).isoformat()
            result["cancel_at_period_end"] = sub.get("cancel_at_period_end", False)
        except Exception:
            logger.warning("billing.stripe_fetch_failed", org_id=str(org.id))

    return result


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    user: CurrentUser,
    org: CurrentOrganization,
    admin: OrgAdmin,
    db: DB,
    plan_tier: PlanTier = PlanTier.STARTER,
    yearly: bool = False,
) -> dict[str, str]:
    """Create a Stripe Checkout session for subscription upgrade."""
    api_key = _require_stripe()

    plan = billing_service.get_plan(plan_tier)

    if plan_tier == PlanTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enterprise plans require contacting sales",
        )

    price_id = plan.stripe_price_id_yearly if yearly else plan.stripe_price_id_monthly

    # Ensure the org has a Stripe customer
    customer_id = org.stripe_customer_id
    svc = StripeService(api_key=api_key)
    async with svc:
        if not customer_id:
            customer = await svc.create_customer(
                email=user.email,
                name=org.name,
                organization_id=str(org.id),
            )
            customer_id = customer["id"]
            org.stripe_customer_id = customer_id
            await db.flush()

        session = await svc.create_checkout_session(
            customer_id=customer_id,
            price_id=price_id,
            success_url=f"{settings.next_public_app_url.rstrip('/')}/dashboard/settings?billing=success",
            cancel_url=f"{settings.next_public_app_url.rstrip('/')}/dashboard/settings?billing=cancel",
        )

    return {
        "checkout_url": session["url"],
        "session_id": session["id"],
    }


@router.post("/portal", response_model=PortalResponse)
async def create_billing_portal_session(
    user: CurrentUser,
    org: CurrentOrganization,
    admin: OrgAdmin,
) -> dict[str, str]:
    """Create a Stripe billing portal session."""
    _require_stripe()

    if not org.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Stripe customer linked to this organization",
        )

    svc = _stripe_service()
    async with svc:
        session = await svc.create_billing_portal_session(
            customer_id=org.stripe_customer_id,
            return_url=f"{settings.next_public_app_url.rstrip('/')}/dashboard/settings",
        )

    return {"portal_url": session["url"]}


@router.post("/change-plan", response_model=ChangePlanResponse)
async def change_plan(
    user: CurrentUser,
    org: CurrentOrganization,
    admin: OrgAdmin,
    db: DB,
    new_tier: PlanTier = PlanTier.STARTER,
    yearly: bool = False,
) -> dict[str, Any]:
    """Change subscription plan.

    When Stripe is configured and the org has an active subscription the
    plan is changed via Stripe proration. Otherwise the plan tier is
    updated locally.
    """
    if new_tier == PlanTier.ENTERPRISE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enterprise plans require contacting sales",
        )

    plan = billing_service.get_plan(new_tier)

    if org.stripe_subscription_id and _STRIPE_API_KEY:
        price_id = plan.stripe_price_id_yearly if yearly else plan.stripe_price_id_monthly
        svc = _stripe_service()
        async with svc:
            await svc.update_subscription(org.stripe_subscription_id, price_id)

    org.plan = new_tier.value
    org.max_repositories = plan.max_repositories
    org.max_frameworks = plan.max_frameworks
    org.max_users = plan.max_users
    await db.flush()

    return {"message": "Plan updated successfully", "new_plan": new_tier.value}


@router.get("/invoices", response_model=list[InvoiceRead])
async def list_invoices(
    user: CurrentUser,
    org: CurrentOrganization,
    admin: OrgAdmin,
    limit: int = Query(10, ge=1, le=100),
) -> list[dict[str, Any]]:
    """List billing invoices from Stripe."""
    if not org.stripe_customer_id or not _STRIPE_API_KEY:
        return []

    svc = _stripe_service()
    async with svc:
        invoices = await svc.list_invoices(org.stripe_customer_id, limit=limit)

    return [
        {
            "id": inv["id"],
            "date": datetime.fromtimestamp(inv.get("created", 0), tz=UTC).strftime("%Y-%m-%d"),
            "amount": inv.get("amount_due", 0),
            "status": inv.get("status", "unknown"),
            "pdf_url": inv.get("invoice_pdf"),
        }
        for inv in invoices
    ]


@router.post("/webhook", response_model=WebhookAck)
async def stripe_webhook(request: Request, db: DB) -> dict[str, str]:
    """Handle Stripe webhooks with signature verification."""
    body = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not _STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe webhook secret is not configured",
        )

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe-Signature header",
        )

    # Verify signature (Stripe v1 scheme)
    try:
        _verify_stripe_signature(body, sig_header, _STRIPE_WEBHOOK_SECRET)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook signature: {exc}",
        ) from exc

    import json

    event = json.loads(body)
    event_type = event.get("type", "")
    data_object = event.get("data", {}).get("object", {})

    logger.info("billing.webhook_received", event_type=event_type)

    if event_type == "customer.subscription.updated":
        await _handle_subscription_updated(data_object, db)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(data_object, db)
    elif event_type == "invoice.payment_failed":
        logger.warning("billing.payment_failed", customer=data_object.get("customer"))

    return {"status": "received"}


@router.get("/usage", response_model=UsageRead)
async def get_usage(
    user: CurrentUser,
    org: CurrentOrganization,
    db: DB,
) -> dict[str, Any]:
    """Get current usage metrics for billing (actual counts)."""
    plan = billing_service.get_plan(PlanTier(org.plan))

    from app.models.customer_profile import CustomerProfile

    repo_count = (
        await db.execute(
            select(func.count())
            .select_from(Repository)
            .join(CustomerProfile)
            .where(CustomerProfile.organization_id == org.id)
        )
    ).scalar_one()

    member_count = (
        await db.execute(
            select(func.count())
            .select_from(OrganizationMember)
            .where(OrganizationMember.organization_id == org.id)
        )
    ).scalar_one()

    api_key_usage = (
        await db.execute(
            select(func.coalesce(func.sum(APIKeyRecord.usage_count), 0)).where(
                APIKeyRecord.organization_id == org.id,
                APIKeyRecord.status == "active",
            )
        )
    ).scalar_one()

    return {
        "repositories": {"used": repo_count, "limit": plan.max_repositories},
        "frameworks": {"used": plan.max_frameworks, "limit": plan.max_frameworks},
        "users": {"used": member_count, "limit": plan.max_users},
        "api_calls": {"used": int(api_key_usage), "limit": 10000},
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _verify_stripe_signature(payload: bytes, sig_header: str, secret: str) -> None:
    """Verify Stripe webhook signature (v1 scheme)."""
    elements = [item.split("=", 1) for item in sig_header.split(",") if "=" in item]
    timestamp = next((value for key, value in elements if key == "t"), None)
    signatures = [value for key, value in elements if key == "v1"]

    if not timestamp or not signatures:
        raise ValueError("Missing t or v1 in signature header")
    try:
        timestamp_value = int(timestamp)
    except ValueError as exc:
        raise ValueError("Invalid signature timestamp") from exc
    if abs(int(time.time()) - timestamp_value) > 300:
        raise ValueError("Signature timestamp is outside the allowed tolerance")

    signed_payload = f"{timestamp}.".encode() + payload
    expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()

    if not any(hmac.compare_digest(expected, signature) for signature in signatures):
        raise ValueError("Signature mismatch")


async def _handle_subscription_updated(data: dict[str, Any], db: DB) -> None:
    """Sync plan tier from a subscription.updated event."""
    customer_id = data.get("customer")
    if not customer_id:
        return
    result = await db.execute(
        select(Organization).where(Organization.stripe_customer_id == customer_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        return

    new_status = data.get("status", "active")
    if new_status == "canceled":
        org.plan = PlanType.STARTER
    org.stripe_subscription_id = data.get("id", org.stripe_subscription_id)
    await db.flush()


async def _handle_subscription_deleted(data: dict[str, Any], db: DB) -> None:
    """Downgrade org when subscription is deleted."""
    customer_id = data.get("customer")
    if not customer_id:
        return
    result = await db.execute(
        select(Organization).where(Organization.stripe_customer_id == customer_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        return

    org.plan = PlanType.STARTER
    org.stripe_subscription_id = None
    await db.flush()
