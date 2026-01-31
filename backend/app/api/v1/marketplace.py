"""API endpoints for Regulatory API Marketplace."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.services.marketplace import (
    APIGateway,
    PlanTier,
    UsageTracker,
    WhiteLabelService,
    get_api_gateway,
    get_usage_tracker,
    get_white_label_service,
)


router = APIRouter(prefix="/marketplace", tags=["marketplace"])


# Request/Response Models
class GenerateKeyRequest(BaseModel):
    """Request to generate an API key."""
    
    organization_id: UUID
    name: str
    plan: str = "free"
    expires_in_days: int | None = None


class KeyResponse(BaseModel):
    """API key response (shown only once)."""
    
    key_id: UUID
    raw_key: str
    key_prefix: str
    name: str
    plan: str
    rate_limit: int
    monthly_limit: int
    expires_at: str | None


class CreateSubscriptionRequest(BaseModel):
    """Request to create subscription."""
    
    organization_id: UUID
    plan: str
    products: list[UUID] | None = None


class WhiteLabelConfigRequest(BaseModel):
    """Request to create white-label config."""
    
    organization_id: UUID
    brand_name: str
    custom_domain: str | None = None
    logo_url: str | None = None
    theme: str = "default"
    custom_colors: dict[str, str] | None = None


class UpdateWhiteLabelRequest(BaseModel):
    """Request to update white-label config."""
    
    brand_name: str | None = None
    custom_domain: str | None = None
    logo_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None


def _parse_plan(plan: str) -> PlanTier:
    """Parse plan string to enum."""
    try:
        return PlanTier(plan.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid plan: {plan}. Valid: {[p.value for p in PlanTier]}",
        )


# Products Endpoints
@router.get("/products")
async def list_products(category: str | None = None):
    """List available API products.
    
    Returns all compliance APIs available in the marketplace.
    """
    gateway = get_api_gateway()
    products = gateway.get_products(category)
    
    return {
        "products": [
            {
                "id": str(p.id),
                "slug": p.slug,
                "name": p.name,
                "description": p.description,
                "category": p.category,
                "version": p.version,
                "free_tier_limit": p.free_tier_limit,
                "features": p.features,
                "supported_frameworks": p.supported_frameworks,
                "is_beta": p.is_beta,
            }
            for p in products
        ],
        "total": len(products),
    }


@router.get("/products/{slug}")
async def get_product(slug: str):
    """Get product details by slug."""
    gateway = get_api_gateway()
    product = gateway.get_product(slug=slug)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "id": str(product.id),
        "slug": product.slug,
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "version": product.version,
        "base_path": product.base_path,
        "free_tier_limit": product.free_tier_limit,
        "price_per_request": product.price_per_request,
        "features": product.features,
        "supported_frameworks": product.supported_frameworks,
        "documentation_url": product.documentation_url or f"/docs/api/{product.slug}",
    }


# API Key Endpoints
@router.post("/keys", response_model=KeyResponse)
async def generate_api_key(request: GenerateKeyRequest):
    """Generate a new API key.
    
    IMPORTANT: The full API key is only shown once in this response.
    Store it securely - it cannot be retrieved again.
    """
    gateway = get_api_gateway()
    plan_tier = _parse_plan(request.plan)
    
    raw_key, api_key = gateway.generate_api_key(
        organization_id=request.organization_id,
        name=request.name,
        plan_tier=plan_tier,
        expires_in_days=request.expires_in_days,
    )
    
    return KeyResponse(
        key_id=api_key.id,
        raw_key=raw_key,
        key_prefix=api_key.key_prefix,
        name=api_key.name,
        plan=api_key.plan_tier.value,
        rate_limit=api_key.rate_limit,
        monthly_limit=api_key.monthly_limit,
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
    )


@router.get("/keys/{organization_id}")
async def list_api_keys(organization_id: UUID):
    """List API keys for an organization."""
    gateway = get_api_gateway()
    keys = gateway.list_api_keys(organization_id)
    
    return {
        "organization_id": str(organization_id),
        "keys": [
            {
                "id": str(k.id),
                "key_prefix": k.key_prefix,
                "name": k.name,
                "plan": k.plan_tier.value,
                "rate_limit": k.rate_limit,
                "monthly_limit": k.monthly_limit,
                "is_active": k.is_active,
                "created_at": k.created_at.isoformat(),
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            }
            for k in keys
        ],
    }


@router.delete("/keys/{key_id}")
async def revoke_api_key(key_id: UUID):
    """Revoke an API key."""
    gateway = get_api_gateway()
    revoked = gateway.revoke_api_key(key_id)
    
    if not revoked:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"revoked": True, "key_id": str(key_id)}


@router.post("/keys/validate")
async def validate_api_key(x_api_key: str = Header(...)):
    """Validate an API key and return its details."""
    gateway = get_api_gateway()
    api_key = gateway.validate_key(x_api_key)
    
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid or expired API key")
    
    rate_allowed, rate_remaining = gateway.check_rate_limit(api_key)
    quota_ok, quota_remaining = gateway.check_quota(api_key)
    
    return {
        "valid": True,
        "key_prefix": api_key.key_prefix,
        "plan": api_key.plan_tier.value,
        "rate_limit": {
            "limit": api_key.rate_limit,
            "remaining": rate_remaining,
        },
        "quota": {
            "limit": api_key.monthly_limit if api_key.monthly_limit > 0 else "unlimited",
            "remaining": quota_remaining if quota_remaining >= 0 else "unlimited",
        },
    }


# Subscription Endpoints
@router.post("/subscriptions")
async def create_subscription(request: CreateSubscriptionRequest):
    """Create a new subscription."""
    tracker = get_usage_tracker()
    plan_tier = _parse_plan(request.plan)
    
    subscription = tracker.create_subscription(
        organization_id=request.organization_id,
        plan_tier=plan_tier,
        products=request.products,
    )
    
    return {
        "id": str(subscription.id),
        "organization_id": str(subscription.organization_id),
        "plan": subscription.plan_tier.value,
        "monthly_price": subscription.monthly_price,
        "current_period_start": subscription.current_period_start.isoformat(),
        "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        "is_active": subscription.is_active,
    }


@router.get("/subscriptions/{organization_id}")
async def get_subscription(organization_id: UUID):
    """Get subscription for an organization."""
    tracker = get_usage_tracker()
    subscription = tracker.get_subscription(organization_id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return {
        "id": str(subscription.id),
        "organization_id": str(subscription.organization_id),
        "plan": subscription.plan_tier.value,
        "monthly_price": subscription.monthly_price,
        "usage_this_period": subscription.usage_this_period,
        "current_period_start": subscription.current_period_start.isoformat(),
        "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        "is_active": subscription.is_active,
    }


# Usage Endpoints
@router.get("/usage/{organization_id}")
async def get_usage_summary(organization_id: UUID):
    """Get usage summary for the current billing period."""
    tracker = get_usage_tracker()
    summary = tracker.get_usage_summary(organization_id)
    
    return {
        "organization_id": str(summary.organization_id),
        "period_start": summary.period_start.isoformat(),
        "period_end": summary.period_end.isoformat(),
        "total_requests": summary.total_requests,
        "included_requests": summary.included_requests,
        "overage_requests": summary.overage_requests,
        "estimated_cost": summary.estimated_cost,
        "by_product": summary.by_product,
    }


@router.get("/usage/{organization_id}/analytics")
async def get_usage_analytics(organization_id: UUID, days: int = 30):
    """Get usage analytics and trends."""
    tracker = get_usage_tracker()
    analytics = tracker.get_usage_analytics(organization_id, days)
    return analytics


@router.get("/usage/{organization_id}/invoice")
async def get_invoice(
    organization_id: UUID,
    month: int | None = None,
    year: int | None = None,
):
    """Get billing invoice for a month."""
    tracker = get_usage_tracker()
    invoice = tracker.get_billing_invoice(organization_id, month, year)
    return invoice


# White-Label Endpoints
@router.post("/white-label")
async def create_white_label_config(request: WhiteLabelConfigRequest):
    """Create white-label configuration for a partner."""
    service = get_white_label_service()
    
    config = service.create_config(
        organization_id=request.organization_id,
        brand_name=request.brand_name,
        custom_domain=request.custom_domain,
        logo_url=request.logo_url,
        theme=request.theme,
        custom_colors=request.custom_colors,
    )
    
    return {
        "id": str(config.id),
        "organization_id": str(config.organization_id),
        "brand_name": config.brand_name,
        "custom_domain": config.custom_domain,
        "logo_url": config.logo_url,
        "primary_color": config.primary_color,
        "secondary_color": config.secondary_color,
        "is_active": config.is_active,
    }


@router.get("/white-label/{organization_id}")
async def get_white_label_config(organization_id: UUID):
    """Get white-label configuration."""
    service = get_white_label_service()
    config = service.get_config(organization_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="White-label config not found")
    
    return {
        "id": str(config.id),
        "organization_id": str(config.organization_id),
        "brand_name": config.brand_name,
        "custom_domain": config.custom_domain,
        "logo_url": config.logo_url,
        "primary_color": config.primary_color,
        "secondary_color": config.secondary_color,
        "ssl_enabled": config.ssl_enabled,
        "is_active": config.is_active,
    }


@router.patch("/white-label/{organization_id}")
async def update_white_label_config(
    organization_id: UUID,
    request: UpdateWhiteLabelRequest,
):
    """Update white-label configuration."""
    service = get_white_label_service()
    
    updates = {k: v for k, v in request.dict().items() if v is not None}
    config = service.update_config(organization_id, updates)
    
    if not config:
        raise HTTPException(status_code=404, detail="White-label config not found")
    
    return {
        "id": str(config.id),
        "updated": True,
        "brand_name": config.brand_name,
        "custom_domain": config.custom_domain,
    }


@router.get("/white-label/{organization_id}/embed")
async def get_embed_config(organization_id: UUID, component: str = "full"):
    """Get embeddable configuration for white-label partners."""
    service = get_white_label_service()
    return service.generate_embed_config(organization_id, component)


@router.get("/white-label/{organization_id}/domain-verification")
async def get_domain_verification(organization_id: UUID, domain: str):
    """Get DNS records for domain verification."""
    service = get_white_label_service()
    return service.verify_domain(organization_id, domain)


# Plans/Pricing Info
@router.get("/plans")
async def list_plans():
    """List available subscription plans."""
    from app.services.marketplace.models import PLAN_CONFIGS
    
    plans = []
    for tier, config in PLAN_CONFIGS.items():
        plans.append({
            "tier": tier.value,
            "monthly_requests": config["monthly_requests"] if config["monthly_requests"] > 0 else "unlimited",
            "rate_limit_per_minute": config["rate_limit_per_minute"],
            "features": config["features"],
            "price": config["price"] if config["price"] >= 0 else "Contact Sales",
        })
    
    return {"plans": plans}
