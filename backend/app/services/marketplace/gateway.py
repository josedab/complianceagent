"""API Gateway - Routes and rate limits marketplace requests."""

import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import structlog

from app.services.marketplace.models import (
    APIKey,
    APIProduct,
    PlanTier,
    PLAN_CONFIGS,
    Subscription,
    UsageRecord,
    UsageType,
)


logger = structlog.get_logger()


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self._requests: dict[str, list[float]] = {}  # key -> timestamps
    
    def is_allowed(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()
        cutoff = now - window_seconds
        
        if key not in self._requests:
            self._requests[key] = []
        
        # Clean old requests
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]
        
        if len(self._requests[key]) >= limit:
            return False
        
        self._requests[key].append(now)
        return True
    
    def get_remaining(self, key: str, limit: int, window_seconds: int = 60) -> int:
        """Get remaining requests in window."""
        now = time.time()
        cutoff = now - window_seconds
        
        if key not in self._requests:
            return limit
        
        recent = [t for t in self._requests[key] if t > cutoff]
        return max(0, limit - len(recent))


class APIGateway:
    """Gateway for managing API access and routing."""

    def __init__(self):
        self._api_keys: dict[UUID, APIKey] = {}
        self._key_lookup: dict[str, UUID] = {}  # key_prefix -> key_id
        self._products: dict[UUID, APIProduct] = {}
        self._subscriptions: dict[UUID, Subscription] = {}  # org_id -> subscription
        self._usage_records: list[UsageRecord] = []
        self._rate_limiter = RateLimiter()
        
        # Initialize default products
        self._init_default_products()

    def _init_default_products(self) -> None:
        """Initialize default API products."""
        default_products = [
            APIProduct(
                slug="compliance-analysis",
                name="Compliance Analysis API",
                description="Analyze code repositories for regulatory compliance",
                category="analysis",
                base_path="/api/v1/analysis",
                free_tier_limit=50,
                features=["code_scanning", "violation_detection", "remediation_suggestions"],
                supported_frameworks=["GDPR", "HIPAA", "PCI-DSS", "SOC2"],
            ),
            APIProduct(
                slug="regulatory-intelligence",
                name="Regulatory Intelligence API",
                description="Real-time regulatory updates and alerts",
                category="intelligence",
                base_path="/api/v1/intelligence",
                free_tier_limit=100,
                features=["real_time_updates", "relevance_scoring", "digest_generation"],
                supported_frameworks=["All"],
            ),
            APIProduct(
                slug="evidence-collection",
                name="Evidence Collection API",
                description="Automated compliance evidence gathering",
                category="evidence",
                base_path="/api/v1/evidence",
                free_tier_limit=25,
                features=["auto_collection", "cross_framework_mapping", "audit_reports"],
                supported_frameworks=["SOC2", "ISO27001", "HIPAA", "GDPR", "PCI-DSS"],
            ),
            APIProduct(
                slug="digital-twin",
                name="Compliance Digital Twin API",
                description="What-if simulation for compliance changes",
                category="analysis",
                base_path="/api/v1/digital-twin",
                free_tier_limit=20,
                features=["snapshot_creation", "scenario_simulation", "impact_analysis"],
                supported_frameworks=["All"],
            ),
            APIProduct(
                slug="pr-review",
                name="PR Review Co-Pilot API",
                description="AI-powered compliance review for pull requests",
                category="analysis",
                base_path="/api/v1/pr-review",
                free_tier_limit=30,
                features=["diff_analysis", "violation_detection", "auto_fix_suggestions"],
                supported_frameworks=["GDPR", "HIPAA", "PCI-DSS", "SOX", "EU AI Act"],
            ),
        ]
        
        for product in default_products:
            self._products[product.id] = product

    def generate_api_key(
        self,
        organization_id: UUID,
        name: str,
        plan_tier: PlanTier = PlanTier.FREE,
        allowed_products: list[UUID] | None = None,
        expires_in_days: int | None = None,
    ) -> tuple[str, APIKey]:
        """Generate a new API key.
        
        Returns:
            Tuple of (raw_key, APIKey object)
        """
        # Generate secure random key
        raw_key = f"ca_{secrets.token_urlsafe(32)}"
        key_prefix = raw_key[:12]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Get plan config
        plan_config = PLAN_CONFIGS.get(plan_tier, PLAN_CONFIGS[PlanTier.FREE])
        
        api_key = APIKey(
            organization_id=organization_id,
            key_prefix=key_prefix,
            key_hash=key_hash,
            name=name,
            plan_tier=plan_tier,
            allowed_products=allowed_products or [],
            rate_limit=plan_config["rate_limit_per_minute"],
            monthly_limit=plan_config["monthly_requests"],
        )
        
        if expires_in_days:
            api_key.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Store
        self._api_keys[api_key.id] = api_key
        self._key_lookup[key_prefix] = api_key.id
        
        logger.info(
            "Generated API key",
            key_id=str(api_key.id),
            organization_id=str(organization_id),
            plan=plan_tier.value,
        )
        
        return raw_key, api_key

    def validate_key(self, raw_key: str) -> APIKey | None:
        """Validate an API key."""
        if not raw_key or len(raw_key) < 12:
            return None
        
        key_prefix = raw_key[:12]
        key_id = self._key_lookup.get(key_prefix)
        
        if not key_id:
            return None
        
        api_key = self._api_keys.get(key_id)
        if not api_key:
            return None
        
        # Verify hash
        expected_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        if api_key.key_hash != expected_hash:
            return None
        
        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None
        
        # Check if active
        if not api_key.is_active:
            return None
        
        return api_key

    def check_rate_limit(self, api_key: APIKey) -> tuple[bool, int]:
        """Check if request is within rate limits.
        
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        limit_key = str(api_key.id)
        is_allowed = self._rate_limiter.is_allowed(
            limit_key,
            api_key.rate_limit,
            window_seconds=60,
        )
        remaining = self._rate_limiter.get_remaining(
            limit_key,
            api_key.rate_limit,
            window_seconds=60,
        )
        return is_allowed, remaining

    def check_quota(self, api_key: APIKey) -> tuple[bool, int]:
        """Check if request is within monthly quota.
        
        Returns:
            Tuple of (has_quota, remaining_quota)
        """
        if api_key.monthly_limit < 0:  # Unlimited
            return True, -1
        
        # Count this month's usage
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_usage = sum(
            1 for r in self._usage_records
            if r.api_key_id == api_key.id and r.timestamp >= month_start
        )
        
        remaining = api_key.monthly_limit - month_usage
        return remaining > 0, remaining

    def record_usage(
        self,
        api_key: APIKey,
        endpoint: str,
        method: str = "GET",
        usage_type: UsageType = UsageType.REQUEST,
        status_code: int = 200,
        response_time_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> UsageRecord:
        """Record API usage."""
        record = UsageRecord(
            api_key_id=api_key.id,
            organization_id=api_key.organization_id,
            endpoint=endpoint,
            method=method,
            usage_type=usage_type,
            status_code=status_code,
            response_time_ms=response_time_ms,
            metadata=metadata or {},
        )
        
        self._usage_records.append(record)
        
        # Update last used
        api_key.last_used_at = datetime.utcnow()
        
        return record

    async def process_request(
        self,
        raw_key: str,
        endpoint: str,
        method: str = "GET",
    ) -> dict[str, Any]:
        """Process an API request through the gateway.
        
        Returns authorization result with headers to include.
        """
        start_time = time.perf_counter()
        
        # Validate key
        api_key = self.validate_key(raw_key)
        if not api_key:
            return {
                "authorized": False,
                "error": "Invalid or expired API key",
                "status_code": 401,
            }
        
        # Check rate limit
        rate_allowed, rate_remaining = self.check_rate_limit(api_key)
        if not rate_allowed:
            return {
                "authorized": False,
                "error": "Rate limit exceeded",
                "status_code": 429,
                "headers": {
                    "X-RateLimit-Limit": str(api_key.rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60",
                },
            }
        
        # Check quota
        quota_ok, quota_remaining = self.check_quota(api_key)
        if not quota_ok:
            return {
                "authorized": False,
                "error": "Monthly quota exceeded",
                "status_code": 429,
                "headers": {
                    "X-Quota-Limit": str(api_key.monthly_limit),
                    "X-Quota-Remaining": "0",
                },
            }
        
        # Record usage
        response_time = (time.perf_counter() - start_time) * 1000
        self.record_usage(
            api_key=api_key,
            endpoint=endpoint,
            method=method,
            response_time_ms=response_time,
        )
        
        return {
            "authorized": True,
            "api_key": api_key,
            "headers": {
                "X-RateLimit-Limit": str(api_key.rate_limit),
                "X-RateLimit-Remaining": str(rate_remaining),
                "X-Quota-Limit": str(api_key.monthly_limit) if api_key.monthly_limit > 0 else "unlimited",
                "X-Quota-Remaining": str(quota_remaining) if quota_remaining >= 0 else "unlimited",
            },
        }

    def get_products(self, category: str | None = None) -> list[APIProduct]:
        """Get available API products."""
        products = list(self._products.values())
        if category:
            products = [p for p in products if p.category == category]
        return [p for p in products if p.is_active]

    def get_product(self, product_id: UUID | None = None, slug: str | None = None) -> APIProduct | None:
        """Get a specific product."""
        if product_id:
            return self._products.get(product_id)
        if slug:
            for p in self._products.values():
                if p.slug == slug:
                    return p
        return None

    def get_api_key(self, key_id: UUID) -> APIKey | None:
        """Get API key by ID."""
        return self._api_keys.get(key_id)

    def list_api_keys(self, organization_id: UUID) -> list[APIKey]:
        """List API keys for an organization."""
        return [
            k for k in self._api_keys.values()
            if k.organization_id == organization_id
        ]

    def revoke_api_key(self, key_id: UUID) -> bool:
        """Revoke an API key."""
        api_key = self._api_keys.get(key_id)
        if api_key:
            api_key.is_active = False
            logger.info("Revoked API key", key_id=str(key_id))
            return True
        return False


# Global instance
_gateway: APIGateway | None = None


def get_api_gateway() -> APIGateway:
    """Get or create API gateway."""
    global _gateway
    if _gateway is None:
        _gateway = APIGateway()
    return _gateway
