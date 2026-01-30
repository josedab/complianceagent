"""Webhook handlers for external services."""

import hashlib
import hmac
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.core.config import settings


router = APIRouter()


@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Handle GitHub App webhooks."""
    payload = await request.body()

    # Verify signature
    if settings.github_webhook_secret:
        expected_sig = "sha256=" + hmac.new(
            settings.github_webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, x_hub_signature_256 or ""):
            raise HTTPException(status_code=401, detail="Invalid signature")

    data = await request.json()

    # Handle different event types
    handlers = {
        "push": handle_push_event,
        "pull_request": handle_pull_request_event,
        "installation": handle_installation_event,
        "installation_repositories": handle_installation_repos_event,
    }

    handler = handlers.get(x_github_event)
    if handler:
        await handler(data, db)

    return {"status": "processed", "event": x_github_event}


async def handle_push_event(data: dict[str, Any], db: AsyncSession) -> None:
    """Handle push events - trigger re-analysis if needed."""
    data.get("repository", {}).get("full_name")
    ref = data.get("ref", "")

    # Only process pushes to default branch
    default_branch = data.get("repository", {}).get("default_branch")
    if ref != f"refs/heads/{default_branch}":
        return

    # Queue re-analysis task

    # Find repository in our system and trigger analysis
    # analyze_repository.delay(repo_id)


async def handle_pull_request_event(data: dict[str, Any], db: AsyncSession) -> None:
    """Handle PR events - run compliance check on PRs."""
    action = data.get("action")

    if action not in ["opened", "synchronize", "reopened"]:
        return

    data.get("pull_request", {})
    data.get("repository", {})

    # Queue compliance check

    # check_pr_compliance.delay(repo["full_name"], pr["number"])


async def handle_installation_event(data: dict[str, Any], db: AsyncSession) -> None:
    """Handle GitHub App installation events."""
    action = data.get("action")
    data.get("installation", {})

    if action == "created":
        # New installation - could notify or set up
        pass
    elif action == "deleted":
        # Installation removed - clean up
        pass


async def handle_installation_repos_event(data: dict[str, Any], db: AsyncSession) -> None:
    """Handle repository added/removed from installation."""
    data.get("action")
    data.get("repositories_added", [])
    data.get("repositories_removed", [])

    # Update our repository tracking


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Handle Stripe webhooks."""
    await request.body()

    # Verify signature
    # In production, use stripe.Webhook.construct_event()

    data = await request.json()
    event_type = data.get("type")
    event_data = data.get("data", {}).get("object", {})

    handlers = {
        "customer.subscription.created": handle_subscription_created,
        "customer.subscription.updated": handle_subscription_updated,
        "customer.subscription.deleted": handle_subscription_deleted,
        "invoice.paid": handle_invoice_paid,
        "invoice.payment_failed": handle_payment_failed,
    }

    handler = handlers.get(event_type)
    if handler:
        await handler(event_data, db)

    return {"status": "processed", "event": event_type}


async def handle_subscription_created(data: dict[str, Any], db: AsyncSession) -> None:
    """Handle new subscription."""
    data.get("customer")
    data.get("id")
    data.get("status")

    # Update organization with subscription details
    # Send welcome email


async def handle_subscription_updated(data: dict[str, Any], db: AsyncSession) -> None:
    """Handle subscription changes (plan change, etc.)."""
    data.get("customer")
    data.get("status")

    # Update organization plan


async def handle_subscription_deleted(data: dict[str, Any], db: AsyncSession) -> None:
    """Handle subscription cancellation."""
    data.get("customer")

    # Downgrade to free tier or disable access


async def handle_invoice_paid(data: dict[str, Any], db: AsyncSession) -> None:
    """Handle successful payment."""
    data.get("customer")
    data.get("amount_paid")

    # Record payment, extend access


async def handle_payment_failed(data: dict[str, Any], db: AsyncSession) -> None:
    """Handle failed payment."""
    data.get("customer")

    # Send notification, potentially restrict access
