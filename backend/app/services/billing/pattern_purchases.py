"""Stripe integration for Pattern Marketplace purchases."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import httpx
import structlog

from app.core.config import settings


logger = structlog.get_logger()


@dataclass
class CheckoutSession:
    """Checkout session for a pattern purchase."""

    id: str
    url: str
    pattern_id: str
    organization_id: str
    price: float
    status: str


@dataclass
class ConnectAccount:
    """Stripe Connect account for a publisher."""

    id: str
    organization_id: str
    charges_enabled: bool
    payouts_enabled: bool
    details_submitted: bool
    onboarding_url: str | None = None


class PatternPurchaseStripeService:
    """Stripe service for pattern marketplace purchases.

    Handles:
    - One-time pattern purchases via Checkout Sessions
    - Stripe Connect for publisher payouts
    - Transfer management for revenue sharing
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or getattr(settings, "stripe_api_key", "")
        self.base_url = "https://api.stripe.com/v1"
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            auth=httpx.BasicAuth(self.api_key, ""),
            timeout=30.0,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    # ========================================================================
    # Pattern Purchase Checkout
    # ========================================================================

    async def create_pattern_checkout_session(
        self,
        pattern_id: UUID,
        pattern_name: str,
        pattern_description: str,
        price_cents: int,
        organization_id: UUID,
        user_id: UUID | None,
        publisher_connect_account_id: str | None,
        success_url: str,
        cancel_url: str,
    ) -> CheckoutSession:
        """Create a Stripe Checkout session for a one-time pattern purchase.

        Args:
            pattern_id: The pattern being purchased
            pattern_name: Display name for the line item
            pattern_description: Description for the line item
            price_cents: Price in cents
            organization_id: Purchasing organization
            user_id: User making the purchase
            publisher_connect_account_id: Stripe Connect account for the publisher
            success_url: URL to redirect on success (with {CHECKOUT_SESSION_ID} placeholder)
            cancel_url: URL to redirect on cancel

        Returns:
            CheckoutSession with URL to redirect user
        """
        # Build metadata for webhook processing
        metadata = {
            "type": "pattern_purchase",
            "pattern_id": str(pattern_id),
            "organization_id": str(organization_id),
        }
        if user_id:
            metadata["user_id"] = str(user_id)

        # Create line item data
        data = {
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "line_items[0][price_data][currency]": "usd",
            "line_items[0][price_data][unit_amount]": str(price_cents),
            "line_items[0][price_data][product_data][name]": pattern_name,
            "line_items[0][price_data][product_data][description]": pattern_description[:500],
            "line_items[0][quantity]": "1",
            "payment_intent_data[metadata][pattern_id]": str(pattern_id),
            "payment_intent_data[metadata][organization_id]": str(organization_id),
        }

        # Add metadata
        for key, value in metadata.items():
            data[f"metadata[{key}]"] = value

        # If publisher has Connect account, set up application fee for platform
        if publisher_connect_account_id:
            # Platform takes 30% fee (publisher gets 70%)
            platform_fee = int(price_cents * 0.30)
            data["payment_intent_data[application_fee_amount]"] = str(platform_fee)
            data["payment_intent_data[transfer_data][destination]"] = publisher_connect_account_id

        response = await self._client.post("/checkout/sessions", data=data)
        response.raise_for_status()
        session_data = response.json()

        logger.info(
            "Pattern checkout session created",
            session_id=session_data["id"],
            pattern_id=str(pattern_id),
            organization_id=str(organization_id),
            price_cents=price_cents,
        )

        return CheckoutSession(
            id=session_data["id"],
            url=session_data["url"],
            pattern_id=str(pattern_id),
            organization_id=str(organization_id),
            price=price_cents / 100,
            status=session_data["status"],
        )

    async def get_checkout_session(self, session_id: str) -> dict[str, Any]:
        """Get checkout session details."""
        response = await self._client.get(f"/checkout/sessions/{session_id}")
        response.raise_for_status()
        return response.json()

    async def get_payment_intent(self, payment_intent_id: str) -> dict[str, Any]:
        """Get payment intent details."""
        response = await self._client.get(f"/payment_intents/{payment_intent_id}")
        response.raise_for_status()
        return response.json()

    # ========================================================================
    # Stripe Connect for Publishers
    # ========================================================================

    async def create_connect_account(
        self,
        organization_id: UUID,
        organization_name: str,
        email: str,
    ) -> ConnectAccount:
        """Create a Stripe Connect Express account for a publisher.

        Args:
            organization_id: Publisher's organization ID
            organization_name: Business name
            email: Contact email

        Returns:
            ConnectAccount with onboarding URL
        """
        data = {
            "type": "express",
            "email": email,
            "metadata[organization_id]": str(organization_id),
            "capabilities[card_payments][requested]": "true",
            "capabilities[transfers][requested]": "true",
            "business_profile[name]": organization_name,
            "business_profile[product_description]": "Compliance patterns for software development",
        }

        response = await self._client.post("/accounts", data=data)
        response.raise_for_status()
        account_data = response.json()

        logger.info(
            "Stripe Connect account created",
            account_id=account_data["id"],
            organization_id=str(organization_id),
        )

        return ConnectAccount(
            id=account_data["id"],
            organization_id=str(organization_id),
            charges_enabled=account_data.get("charges_enabled", False),
            payouts_enabled=account_data.get("payouts_enabled", False),
            details_submitted=account_data.get("details_submitted", False),
        )

    async def create_account_onboarding_link(
        self,
        account_id: str,
        refresh_url: str,
        return_url: str,
    ) -> str:
        """Create an onboarding link for a Connect account.

        Args:
            account_id: Stripe Connect account ID
            refresh_url: URL if link expires
            return_url: URL after onboarding completes

        Returns:
            Onboarding URL
        """
        data = {
            "account": account_id,
            "refresh_url": refresh_url,
            "return_url": return_url,
            "type": "account_onboarding",
        }

        response = await self._client.post("/account_links", data=data)
        response.raise_for_status()
        link_data = response.json()

        return link_data["url"]

    async def get_connect_account(self, account_id: str) -> ConnectAccount:
        """Get Connect account details."""
        response = await self._client.get(f"/accounts/{account_id}")
        response.raise_for_status()
        account_data = response.json()

        return ConnectAccount(
            id=account_data["id"],
            organization_id=account_data.get("metadata", {}).get("organization_id", ""),
            charges_enabled=account_data.get("charges_enabled", False),
            payouts_enabled=account_data.get("payouts_enabled", False),
            details_submitted=account_data.get("details_submitted", False),
        )

    async def create_login_link(self, account_id: str) -> str:
        """Create a login link for publisher to access their Stripe dashboard."""
        response = await self._client.post(f"/accounts/{account_id}/login_links")
        response.raise_for_status()
        link_data = response.json()
        return link_data["url"]

    # ========================================================================
    # Transfers & Payouts
    # ========================================================================

    async def create_transfer(
        self,
        amount_cents: int,
        destination_account_id: str,
        pattern_id: UUID,
        purchase_id: UUID,
        description: str = "",
    ) -> dict[str, Any]:
        """Create a transfer to a publisher's Connect account.

        Used for manual transfers when not using automatic transfer on checkout.
        """
        data = {
            "amount": str(amount_cents),
            "currency": "usd",
            "destination": destination_account_id,
            "metadata[pattern_id]": str(pattern_id),
            "metadata[purchase_id]": str(purchase_id),
        }
        if description:
            data["description"] = description

        response = await self._client.post("/transfers", data=data)
        response.raise_for_status()
        return response.json()

    async def get_account_balance(self, account_id: str) -> dict[str, Any]:
        """Get balance for a Connect account."""
        response = await self._client.get(
            "/balance",
            headers={"Stripe-Account": account_id},
        )
        response.raise_for_status()
        return response.json()

    async def list_transfers(
        self,
        destination_account_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """List transfers to a Connect account."""
        response = await self._client.get(
            "/transfers",
            params={"destination": destination_account_id, "limit": limit},
        )
        response.raise_for_status()
        return response.json().get("data", [])

    # ========================================================================
    # Refunds
    # ========================================================================

    async def refund_payment(
        self,
        payment_intent_id: str,
        reason: str = "requested_by_customer",
        reverse_transfer: bool = True,
    ) -> dict[str, Any]:
        """Refund a pattern purchase.

        Args:
            payment_intent_id: The payment intent to refund
            reason: Reason for refund
            reverse_transfer: Whether to also reverse the transfer to publisher

        Returns:
            Refund details
        """
        data = {
            "payment_intent": payment_intent_id,
            "reason": reason,
        }
        if reverse_transfer:
            data["reverse_transfer"] = "true"

        response = await self._client.post("/refunds", data=data)
        response.raise_for_status()
        return response.json()


class PatternPurchaseService:
    """High-level service for pattern marketplace purchases."""

    def __init__(self):
        self.stripe = PatternPurchaseStripeService()

    async def create_purchase_checkout(
        self,
        pattern_id: UUID,
        pattern_name: str,
        pattern_description: str,
        price: float,
        organization_id: UUID,
        user_id: UUID | None,
        publisher_connect_account_id: str | None = None,
        base_url: str = "",
    ) -> CheckoutSession:
        """Create a checkout session for purchasing a pattern.

        Args:
            pattern_id: Pattern to purchase
            pattern_name: Name for display
            pattern_description: Description for display
            price: Price in dollars
            organization_id: Purchasing organization
            user_id: User making purchase
            publisher_connect_account_id: Publisher's Stripe Connect account
            base_url: Base URL for redirects

        Returns:
            CheckoutSession with URL to redirect user
        """
        if not base_url:
            base_url = getattr(settings, "frontend_url", "http://localhost:3000")

        success_url = f"{base_url}/marketplace/purchase/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{base_url}/marketplace/patterns/{pattern_id}"

        price_cents = int(price * 100)

        async with self.stripe:
            return await self.stripe.create_pattern_checkout_session(
                pattern_id=pattern_id,
                pattern_name=pattern_name,
                pattern_description=pattern_description,
                price_cents=price_cents,
                organization_id=organization_id,
                user_id=user_id,
                publisher_connect_account_id=publisher_connect_account_id,
                success_url=success_url,
                cancel_url=cancel_url,
            )

    async def setup_publisher_payouts(
        self,
        organization_id: UUID,
        organization_name: str,
        email: str,
        base_url: str = "",
    ) -> ConnectAccount:
        """Set up a publisher for receiving payouts via Stripe Connect.

        Args:
            organization_id: Publisher's organization
            organization_name: Business name
            email: Contact email
            base_url: Base URL for redirects

        Returns:
            ConnectAccount with onboarding URL
        """
        if not base_url:
            base_url = getattr(settings, "frontend_url", "http://localhost:3000")

        async with self.stripe:
            # Create Connect account
            account = await self.stripe.create_connect_account(
                organization_id=organization_id,
                organization_name=organization_name,
                email=email,
            )

            # Generate onboarding link
            onboarding_url = await self.stripe.create_account_onboarding_link(
                account_id=account.id,
                refresh_url=f"{base_url}/publisher/onboarding/refresh",
                return_url=f"{base_url}/publisher/onboarding/complete",
            )
            account.onboarding_url = onboarding_url

            return account

    async def get_publisher_dashboard_url(self, account_id: str) -> str:
        """Get URL for publisher to access their Stripe dashboard."""
        async with self.stripe:
            return await self.stripe.create_login_link(account_id)

    async def process_refund(
        self,
        payment_intent_id: str,
        reason: str = "requested_by_customer",
    ) -> dict[str, Any]:
        """Process a refund for a pattern purchase."""
        async with self.stripe:
            return await self.stripe.refund_payment(
                payment_intent_id=payment_intent_id,
                reason=reason,
                reverse_transfer=True,
            )


# Singleton instance
pattern_purchase_service = PatternPurchaseService()
