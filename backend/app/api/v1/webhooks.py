"""Webhook handlers for external services."""

import hashlib
import hmac
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.core.config import settings


logger = structlog.get_logger()
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
    """Handle push events - trigger re-analysis on default branch pushes."""
    repo_name = data.get("repository", {}).get("full_name")
    ref = data.get("ref", "")

    # Only process pushes to default branch
    default_branch = data.get("repository", {}).get("default_branch")
    if ref != f"refs/heads/{default_branch}":
        return

    from sqlalchemy import select

    from app.models.codebase import Repository

    repo_result = await db.execute(
        select(Repository).where(Repository.full_name == repo_name)
    )
    repository = repo_result.scalar_one_or_none()

    if not repository:
        logger.debug("Push event for untracked repository", repo=repo_name)
        return

    # Update last push timestamp
    repository.last_push_at = datetime.now(UTC)
    await db.commit()

    logger.info(
        "Push event processed",
        repo=repo_name,
        ref=ref,
        commits=len(data.get("commits", [])),
    )


async def handle_pull_request_event(data: dict[str, Any], db: AsyncSession) -> None:
    """Handle PR events - run compliance check on PRs."""
    from app.workers.pr_bot_tasks import process_pr_webhook
    
    action = data.get("action")

    if action not in ["opened", "synchronize", "reopened"]:
        return

    pr = data.get("pull_request", {})
    repo = data.get("repository", {})
    
    # Get organization for this repository
    from sqlalchemy import select
    from app.models.codebase import Repository
    
    repo_result = await db.execute(
        select(Repository).where(Repository.full_name == repo.get("full_name"))
    )
    repository = repo_result.scalar_one_or_none()
    
    if repository and repository.organization_id:
        # Queue PR analysis task
        # In production, access_token would come from GitHub App installation
        process_pr_webhook.delay(
            event_type="pull_request",
            event_data=data,
            organization_id=str(repository.organization_id),
            access_token="",  # Will be fetched from installation in task
        )


async def handle_installation_event(data: dict[str, Any], db: AsyncSession) -> None:
    """Handle GitHub App installation events."""
    action = data.get("action")
    installation = data.get("installation", {})
    account = installation.get("account", {})

    if action == "created":
        logger.info(
            "GitHub App installed",
            installation_id=installation.get("id"),
            account=account.get("login"),
            account_type=account.get("type"),
        )
    elif action == "deleted":
        logger.info(
            "GitHub App uninstalled",
            installation_id=installation.get("id"),
            account=account.get("login"),
        )


async def handle_installation_repos_event(data: dict[str, Any], db: AsyncSession) -> None:
    """Handle repository added/removed from installation."""
    action = data.get("action")
    repos_added = data.get("repositories_added", [])
    repos_removed = data.get("repositories_removed", [])

    if repos_added:
        logger.info(
            "Repositories added to installation",
            count=len(repos_added),
            repos=[r.get("full_name") for r in repos_added],
        )

    if repos_removed:
        logger.info(
            "Repositories removed from installation",
            count=len(repos_removed),
            repos=[r.get("full_name") for r in repos_removed],
        )


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
        # Pattern marketplace events
        "checkout.session.completed": handle_checkout_session_completed,
        "account.updated": handle_connect_account_updated,
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


# ============================================================================
# Pattern Marketplace Webhook Handlers
# ============================================================================


async def handle_checkout_session_completed(
    data: dict[str, Any],
    db: AsyncSession,
) -> None:
    """Handle completed checkout session for pattern purchases.

    This creates the PatternPurchase record when a user completes
    payment for a marketplace pattern.
    """
    from sqlalchemy import select

    from app.models.pattern_marketplace import PatternPurchase

    metadata = data.get("metadata", {})

    # Only process pattern purchases
    if metadata.get("type") != "pattern_purchase":
        return

    pattern_id = metadata.get("pattern_id")
    organization_id = metadata.get("organization_id")
    user_id = metadata.get("user_id")

    if not pattern_id or not organization_id:
        logger.warning(
            "Checkout session missing required metadata",
            session_id=data.get("id"),
            metadata=metadata,
        )
        return

    # Check if purchase already exists (idempotency)
    checkout_session_id = data.get("id")
    existing = await db.execute(
        select(PatternPurchase).where(
            PatternPurchase.stripe_checkout_session_id == checkout_session_id
        )
    )
    if existing.scalar_one_or_none():
        logger.info(
            "Pattern purchase already recorded",
            checkout_session_id=checkout_session_id,
        )
        return

    # Get payment details
    amount_total = data.get("amount_total", 0)  # In cents
    payment_intent_id = data.get("payment_intent")

    # Determine license type from pattern
    from app.models.pattern_marketplace import CompliancePattern, LicenseType

    pattern_result = await db.execute(
        select(CompliancePattern).where(CompliancePattern.id == UUID(pattern_id))
    )
    pattern = pattern_result.scalar_one_or_none()

    license_type = LicenseType.COMMERCIAL
    if pattern:
        license_type = pattern.license_type

    # Create purchase record
    purchase = PatternPurchase(
        pattern_id=UUID(pattern_id),
        organization_id=UUID(organization_id),
        user_id=UUID(user_id) if user_id else None,
        price_paid=amount_total / 100,  # Convert cents to dollars
        license_type=license_type,
        stripe_payment_id=payment_intent_id,
        stripe_checkout_session_id=checkout_session_id,
    )

    db.add(purchase)
    await db.commit()

    logger.info(
        "Pattern purchase recorded",
        pattern_id=pattern_id,
        organization_id=organization_id,
        amount=amount_total / 100,
        checkout_session_id=checkout_session_id,
    )

    # Update pattern download count
    if pattern:
        pattern.downloads += 1
        await db.commit()


async def handle_connect_account_updated(
    data: dict[str, Any],
    db: AsyncSession,
) -> None:
    """Handle Stripe Connect account updates.

    Updates the publisher profile when their Connect account
    status changes (e.g., onboarding completes).
    """
    from sqlalchemy import select

    from app.models.pattern_marketplace import PublisherProfile

    account_id = data.get("id")
    organization_id = data.get("metadata", {}).get("organization_id")

    if not organization_id:
        return

    charges_enabled = data.get("charges_enabled", False)
    payouts_enabled = data.get("payouts_enabled", False)
    details_submitted = data.get("details_submitted", False)

    # Find publisher profile
    result = await db.execute(
        select(PublisherProfile).where(
            PublisherProfile.organization_id == UUID(organization_id)
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        logger.warning(
            "Publisher profile not found for Connect account",
            account_id=account_id,
            organization_id=organization_id,
        )
        return

    # Update profile with Connect account status
    profile.stripe_connect_account_id = account_id

    # Mark as verified when fully onboarded
    if charges_enabled and payouts_enabled and details_submitted:
        if not profile.verified:
            profile.verified = True
            profile.verified_at = datetime.now(UTC)
            logger.info(
                "Publisher verified via Stripe Connect",
                organization_id=organization_id,
                account_id=account_id,
            )

    await db.commit()

    logger.info(
        "Publisher Connect account updated",
        organization_id=organization_id,
        account_id=account_id,
        charges_enabled=charges_enabled,
        payouts_enabled=payouts_enabled,
    )
