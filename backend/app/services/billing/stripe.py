"""Stripe billing integration."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx
import structlog


logger = structlog.get_logger()


class PlanTier(str, Enum):
    """Subscription plan tiers."""

    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class PlanConfig:
    """Configuration for a subscription plan."""

    tier: PlanTier
    name: str
    price_monthly: int  # in cents
    price_yearly: int  # in cents
    max_repositories: int
    max_frameworks: int
    max_users: int
    features: list[str]
    stripe_price_id_monthly: str
    stripe_price_id_yearly: str


# Plan definitions
PLANS = {
    PlanTier.STARTER: PlanConfig(
        tier=PlanTier.STARTER,
        name="Starter",
        price_monthly=50000,  # $500
        price_yearly=480000,  # $4800 (2 months free)
        max_repositories=1,
        max_frameworks=3,
        max_users=5,
        features=[
            "1 Repository",
            "3 Regulatory Frameworks",
            "5 Team Members",
            "Email Support",
            "Basic Audit Trail",
        ],
        stripe_price_id_monthly="price_starter_monthly",
        stripe_price_id_yearly="price_starter_yearly",
    ),
    PlanTier.PROFESSIONAL: PlanConfig(
        tier=PlanTier.PROFESSIONAL,
        name="Professional",
        price_monthly=150000,  # $1500
        price_yearly=1440000,  # $14400 (2 months free)
        max_repositories=5,
        max_frameworks=10,
        max_users=20,
        features=[
            "5 Repositories",
            "10 Regulatory Frameworks",
            "20 Team Members",
            "Priority Support",
            "Full Audit Trail",
            "CI/CD Integration",
            "API Access",
        ],
        stripe_price_id_monthly="price_professional_monthly",
        stripe_price_id_yearly="price_professional_yearly",
    ),
    PlanTier.ENTERPRISE: PlanConfig(
        tier=PlanTier.ENTERPRISE,
        name="Enterprise",
        price_monthly=0,  # Custom pricing
        price_yearly=0,
        max_repositories=999,
        max_frameworks=999,
        max_users=999,
        features=[
            "Unlimited Repositories",
            "All Regulatory Frameworks",
            "Unlimited Team Members",
            "Dedicated Support",
            "Full Audit Trail",
            "CI/CD Integration",
            "API Access",
            "SSO/SAML",
            "Custom Integrations",
            "SLA",
        ],
        stripe_price_id_monthly="",
        stripe_price_id_yearly="",
    ),
}


class StripeService:
    """Service for Stripe billing integration."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or ""
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

    async def create_customer(
        self,
        email: str,
        name: str,
        organization_id: str,
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create a Stripe customer."""
        data = {
            "email": email,
            "name": name,
            "metadata[organization_id]": organization_id,
        }
        if metadata:
            for key, value in metadata.items():
                data[f"metadata[{key}]"] = value

        response = await self._client.post("/customers", data=data)
        response.raise_for_status()
        return response.json()

    async def get_customer(self, customer_id: str) -> dict[str, Any]:
        """Get a Stripe customer."""
        response = await self._client.get(f"/customers/{customer_id}")
        response.raise_for_status()
        return response.json()

    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: int = 14,
    ) -> dict[str, Any]:
        """Create a subscription."""
        data = {
            "customer": customer_id,
            "items[0][price]": price_id,
            "trial_period_days": str(trial_days),
            "payment_behavior": "default_incomplete",
            "expand[]": "latest_invoice.payment_intent",
        }

        response = await self._client.post("/subscriptions", data=data)
        response.raise_for_status()
        return response.json()

    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True,
    ) -> dict[str, Any]:
        """Cancel a subscription."""
        data = {"cancel_at_period_end": "true" if at_period_end else "false"}
        response = await self._client.post(
            f"/subscriptions/{subscription_id}",
            data=data,
        )
        response.raise_for_status()
        return response.json()

    async def update_subscription(
        self,
        subscription_id: str,
        new_price_id: str,
    ) -> dict[str, Any]:
        """Update subscription to a new plan."""
        # Get current subscription
        sub_response = await self._client.get(f"/subscriptions/{subscription_id}")
        sub_response.raise_for_status()
        subscription = sub_response.json()

        # Update the subscription item
        item_id = subscription["items"]["data"][0]["id"]
        data = {
            "items[0][id]": item_id,
            "items[0][price]": new_price_id,
            "proration_behavior": "create_prorations",
        }

        response = await self._client.post(
            f"/subscriptions/{subscription_id}",
            data=data,
        )
        response.raise_for_status()
        return response.json()

    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        trial_days: int = 14,
    ) -> dict[str, Any]:
        """Create a Stripe Checkout session."""
        data = {
            "customer": customer_id,
            "line_items[0][price]": price_id,
            "line_items[0][quantity]": "1",
            "mode": "subscription",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "subscription_data[trial_period_days]": str(trial_days),
        }

        response = await self._client.post("/checkout/sessions", data=data)
        response.raise_for_status()
        return response.json()

    async def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str,
    ) -> dict[str, Any]:
        """Create a billing portal session."""
        data = {
            "customer": customer_id,
            "return_url": return_url,
        }

        response = await self._client.post(
            "/billing_portal/sessions",
            data=data,
        )
        response.raise_for_status()
        return response.json()

    async def get_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Get subscription details."""
        response = await self._client.get(f"/subscriptions/{subscription_id}")
        response.raise_for_status()
        return response.json()

    async def list_invoices(
        self,
        customer_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """List invoices for a customer."""
        response = await self._client.get(
            "/invoices",
            params={"customer": customer_id, "limit": limit},
        )
        response.raise_for_status()
        return response.json().get("data", [])


class BillingService:
    """High-level billing service."""

    def __init__(self):
        self.stripe = StripeService()

    def get_plan(self, tier: PlanTier) -> PlanConfig:
        """Get plan configuration."""
        return PLANS.get(tier, PLANS[PlanTier.STARTER])

    def get_all_plans(self) -> list[PlanConfig]:
        """Get all available plans."""
        return list(PLANS.values())

    async def setup_organization_billing(
        self,
        organization_id: str,
        organization_name: str,
        admin_email: str,
        plan_tier: PlanTier = PlanTier.STARTER,
        yearly: bool = False,
    ) -> dict[str, Any]:
        """Set up billing for a new organization."""
        plan = self.get_plan(plan_tier)
        price_id = plan.stripe_price_id_yearly if yearly else plan.stripe_price_id_monthly

        async with self.stripe:
            # Create customer
            customer = await self.stripe.create_customer(
                email=admin_email,
                name=organization_name,
                organization_id=organization_id,
            )

            # Create subscription with trial
            subscription = await self.stripe.create_subscription(
                customer_id=customer["id"],
                price_id=price_id,
                trial_days=14,
            )

            return {
                "customer_id": customer["id"],
                "subscription_id": subscription["id"],
                "status": subscription["status"],
                "trial_end": subscription.get("trial_end"),
                "plan_tier": plan_tier.value,
            }

    async def change_plan(
        self,
        subscription_id: str,
        new_tier: PlanTier,
        yearly: bool = False,
    ) -> dict[str, Any]:
        """Change subscription plan."""
        plan = self.get_plan(new_tier)
        price_id = plan.stripe_price_id_yearly if yearly else plan.stripe_price_id_monthly

        async with self.stripe:
            subscription = await self.stripe.update_subscription(
                subscription_id=subscription_id,
                new_price_id=price_id,
            )

            return {
                "subscription_id": subscription["id"],
                "status": subscription["status"],
                "new_plan_tier": new_tier.value,
            }

    async def get_billing_portal_url(
        self,
        customer_id: str,
        return_url: str,
    ) -> str:
        """Get URL for customer billing portal."""
        async with self.stripe:
            session = await self.stripe.create_billing_portal_session(
                customer_id=customer_id,
                return_url=return_url,
            )
            return session["url"]


billing_service = BillingService()
