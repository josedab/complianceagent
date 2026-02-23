"""Compliance API Gateway Service."""

import secrets
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.api_gateway.models import (
    APITier,
    APIUsageRecord,
    DeveloperPortalInfo,
    GatewayStats,
    OAuthClient,
    RateLimitStatus,
    TokenStatus,
)


logger = structlog.get_logger()

_TIER_LIMITS: dict[APITier, dict] = {
    APITier.FREE: {"rpm": 60, "monthly": 10000, "scopes": ["read"]},
    APITier.STARTER: {"rpm": 300, "monthly": 100000, "scopes": ["read", "write"]},
    APITier.PROFESSIONAL: {"rpm": 1000, "monthly": 1000000, "scopes": ["read", "write", "admin"]},
    APITier.ENTERPRISE: {"rpm": 5000, "monthly": -1, "scopes": ["read", "write", "admin", "audit"]},
}


class APIGatewayService:
    """Compliance API Gateway with OAuth2 and rate limiting."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._clients: dict[str, OAuthClient] = {}
        self._usage: list[APIUsageRecord] = []

    async def create_client(
        self,
        client_name: str,
        tier: str = "free",
        redirect_uris: list[str] | None = None,
        scopes: list[str] | None = None,
    ) -> tuple[OAuthClient, str]:
        api_tier = APITier(tier)
        limits = _TIER_LIMITS[api_tier]
        client_id = f"ca_{secrets.token_urlsafe(16)}"
        client_secret = secrets.token_urlsafe(32)

        client = OAuthClient(
            client_id=client_id,
            client_name=client_name,
            tier=api_tier,
            redirect_uris=redirect_uris or [],
            scopes=scopes or limits["scopes"],
            rate_limit_per_minute=limits["rpm"],
            monthly_quota=limits["monthly"],
            created_at=datetime.now(UTC),
        )
        self._clients[client_id] = client
        logger.info("OAuth client created", name=client_name, tier=tier)
        return client, client_secret

    async def authenticate(self, client_id: str) -> OAuthClient | None:
        client = self._clients.get(client_id)
        if not client or client.status != TokenStatus.ACTIVE:
            return None
        if client.monthly_quota > 0 and client.monthly_usage >= client.monthly_quota:
            client.status = TokenStatus.RATE_LIMITED
            return None
        return client

    async def record_request(
        self,
        client_id: str,
        endpoint: str,
        method: str = "GET",
        status_code: int = 200,
        response_time_ms: float = 0.0,
    ) -> APIUsageRecord:
        record = APIUsageRecord(
            client_id=client_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            timestamp=datetime.now(UTC),
        )
        self._usage.append(record)
        client = self._clients.get(client_id)
        if client:
            client.monthly_usage += 1
        return record

    async def revoke_client(self, client_id: str) -> bool:
        client = self._clients.get(client_id)
        if not client:
            return False
        client.status = TokenStatus.REVOKED
        return True

    def get_rate_limit(self, client_id: str) -> RateLimitStatus | None:
        client = self._clients.get(client_id)
        if not client:
            return None
        recent = sum(1 for r in self._usage if r.client_id == client_id)
        return RateLimitStatus(
            client_id=client_id,
            tier=client.tier.value,
            limit_per_minute=client.rate_limit_per_minute,
            remaining=max(0, client.rate_limit_per_minute - (recent % client.rate_limit_per_minute)),
            monthly_quota=client.monthly_quota,
            monthly_used=client.monthly_usage,
        )

    def get_developer_portal(self) -> DeveloperPortalInfo:
        return DeveloperPortalInfo(
            sdks=[
                {"language": "Python", "package": "complianceagent", "install": "pip install complianceagent"},
                {"language": "TypeScript", "package": "@complianceagent/sdk", "install": "npm install @complianceagent/sdk"},
                {"language": "Go", "package": "complianceagent-go", "install": "go get github.com/josedab/complianceagent-go"},
            ],
        )

    def list_clients(self, tier: APITier | None = None) -> list[OAuthClient]:
        results = list(self._clients.values())
        if tier:
            results = [c for c in results if c.tier == tier]
        return results

    def get_stats(self) -> GatewayStats:
        by_tier: dict[str, int] = {}
        by_endpoint: dict[str, int] = {}
        times: list[float] = []
        errors = 0

        for c in self._clients.values():
            by_tier[c.tier.value] = by_tier.get(c.tier.value, 0) + 1

        for r in self._usage:
            by_endpoint[r.endpoint] = by_endpoint.get(r.endpoint, 0) + 1
            times.append(r.response_time_ms)
            if r.status_code >= 400:
                errors += 1

        return GatewayStats(
            total_clients=len(self._clients),
            active_clients=sum(1 for c in self._clients.values() if c.status == TokenStatus.ACTIVE),
            total_requests=len(self._usage),
            by_tier=by_tier,
            by_endpoint=by_endpoint,
            avg_response_time_ms=round(sum(times) / len(times), 2) if times else 0.0,
            error_rate_pct=round(errors / len(self._usage) * 100, 1) if self._usage else 0.0,
        )
