"""Billing API routes."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models import User
from app.services.billing import PLANS, PlanTier, billing_service


router = APIRouter()


@router.get("/plans")
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


@router.get("/subscription")
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get current subscription details."""
    org = current_user.organization

    return {
        "organization_id": str(org.id),
        "plan_tier": org.plan,
        "status": "active",  # Would come from Stripe in production
        "billing_email": current_user.email,
        "current_period_end": None,  # From Stripe
        "cancel_at_period_end": False,
    }


@router.post("/checkout")
async def create_checkout_session(
    plan_tier: PlanTier,
    yearly: bool = False,
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Create a Stripe Checkout session for subscription."""
    billing_service.get_plan(plan_tier)

    if plan_tier == PlanTier.ENTERPRISE:
        raise HTTPException(
            status_code=400,
            detail="Enterprise plans require contacting sales",
        )

    # In production, this would create actual Stripe session
    return {
        "checkout_url": f"https://checkout.stripe.com/placeholder?plan={plan_tier.value}",
        "session_id": "cs_placeholder",
    }


@router.post("/portal")
async def create_billing_portal_session(
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Create a Stripe billing portal session."""

    # In production, would get customer_id from org and create real portal session
    return {
        "portal_url": "https://billing.stripe.com/placeholder",
    }


@router.post("/change-plan")
async def change_plan(
    new_tier: PlanTier,
    yearly: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Change subscription plan."""
    org = current_user.organization

    if new_tier == PlanTier.ENTERPRISE:
        raise HTTPException(
            status_code=400,
            detail="Enterprise plans require contacting sales",
        )

    # Update org plan
    org.plan = new_tier.value
    await db.commit()

    return {
        "message": "Plan updated successfully",
        "new_plan": new_tier.value,
    }


@router.get("/invoices")
async def list_invoices(
    current_user: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List billing invoices."""
    # In production, fetch from Stripe
    return [
        {
            "id": "inv_123",
            "date": "2026-01-01",
            "amount": 150000,
            "status": "paid",
            "pdf_url": "https://stripe.com/invoice/123.pdf",
        },
        {
            "id": "inv_122",
            "date": "2025-12-01",
            "amount": 150000,
            "status": "paid",
            "pdf_url": "https://stripe.com/invoice/122.pdf",
        },
    ]


@router.post("/webhook")
async def stripe_webhook(request: Request) -> dict[str, str]:
    """Handle Stripe webhooks."""
    await request.body()
    request.headers.get("stripe-signature")

    # In production:
    # 1. Verify webhook signature
    # 2. Handle events like:
    #    - customer.subscription.created
    #    - customer.subscription.updated
    #    - customer.subscription.deleted
    #    - invoice.paid
    #    - invoice.payment_failed

    return {"status": "received"}


@router.get("/usage")
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get current usage metrics for billing."""
    org = current_user.organization
    plan = billing_service.get_plan(PlanTier(org.plan))

    # In production, query actual usage
    return {
        "repositories": {
            "used": 3,
            "limit": plan.max_repositories,
        },
        "frameworks": {
            "used": 2,
            "limit": plan.max_frameworks,
        },
        "users": {
            "used": 5,
            "limit": plan.max_users,
        },
        "api_calls": {
            "used": 1500,
            "limit": 10000,
        },
    }
