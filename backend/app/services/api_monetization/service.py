"""Compliance API Monetization Layer service."""

from __future__ import annotations

from uuid import UUID, uuid4

import structlog

from app.services.api_monetization.models import (
    APIRevenueStats,
    APIStatus,
    APISubscription,
    ComplianceAPI,
    PricingTier,
    UsageRecord,
)

logger = structlog.get_logger()

_APIS: list[ComplianceAPI] = [
    ComplianceAPI(id="check-gdpr", name="Check GDPR Compliance", description="Analyze code for GDPR violations including consent, data minimization, and retention policies.",
        endpoint="/api/check/gdpr", regulation="GDPR", version="1.2.0", requests_per_month=45200,
        avg_latency_ms=120.0, pricing_per_request=0.02, documentation_url="/docs/api/gdpr",
        supported_languages=["Python", "TypeScript", "Java", "Go"], tags=["privacy", "gdpr", "pii"]),
    ComplianceAPI(id="validate-hipaa", name="Validate HIPAA PHI", description="Detect protected health information (PHI) in code and data flows with remediation suggestions.",
        endpoint="/api/check/hipaa", regulation="HIPAA", version="1.1.0", requests_per_month=28700,
        avg_latency_ms=145.0, pricing_per_request=0.03, documentation_url="/docs/api/hipaa",
        supported_languages=["Python", "TypeScript", "Java"], tags=["healthcare", "phi", "hipaa"]),
    ComplianceAPI(id="assess-pci", name="Assess PCI-DSS", description="Evaluate payment processing code for PCI-DSS compliance including cardholder data handling.",
        endpoint="/api/check/pci-dss", regulation="PCI-DSS", version="1.0.0", requests_per_month=19500,
        avg_latency_ms=160.0, pricing_per_request=0.025, documentation_url="/docs/api/pci",
        supported_languages=["Python", "TypeScript", "Java", "Go", "Ruby"], tags=["payment", "pci", "card"]),
    ComplianceAPI(id="detect-ai-bias", name="Detect AI Bias", description="Analyze ML models and datasets for bias, fairness issues, and EU AI Act compliance.",
        endpoint="/api/check/ai-bias", regulation="EU AI Act", version="0.9.0", status=APIStatus.PUBLISHED,
        requests_per_month=8900, avg_latency_ms=250.0, pricing_per_request=0.05, documentation_url="/docs/api/ai-bias",
        supported_languages=["Python"], tags=["ai", "bias", "fairness", "eu-ai-act"]),
    ComplianceAPI(id="scan-soc2", name="Scan SOC 2 Controls", description="Verify SOC 2 Type II control implementation across infrastructure and application code.",
        endpoint="/api/check/soc2", regulation="SOC 2", version="1.0.0", requests_per_month=15300,
        avg_latency_ms=180.0, pricing_per_request=0.03, documentation_url="/docs/api/soc2",
        supported_languages=["Python", "TypeScript", "Go"], tags=["audit", "soc2", "controls"]),
]


class APIMonetizationService:
    """Service for compliance API monetization layer."""

    async def list_apis(self, regulation: str | None = None) -> list[ComplianceAPI]:
        if regulation:
            return [a for a in _APIS if a.regulation.lower() == regulation.lower()]
        return list(_APIS)

    async def get_api(self, api_id: str) -> ComplianceAPI | None:
        return next((a for a in _APIS if a.id == api_id), None)

    async def create_subscription(
        self, developer_id: UUID, api_id: str, tier: PricingTier,
    ) -> APISubscription:
        if not any(a.id == api_id for a in _APIS):
            raise ValueError(f"API '{api_id}' not found")
        quotas = {PricingTier.FREE: 100, PricingTier.STARTER: 5000, PricingTier.PRO: 50000, PricingTier.ENTERPRISE: 500000}
        costs = {PricingTier.FREE: 0, PricingTier.STARTER: 99, PricingTier.PRO: 499, PricingTier.ENTERPRISE: 2499}
        sub = APISubscription(
            id=uuid4(), developer_id=developer_id, api_id=api_id, tier=tier,
            monthly_quota=quotas.get(tier, 100), monthly_cost=costs.get(tier, 0),
            api_key=f"ca_{uuid4().hex[:24]}",
        )
        logger.info("api.subscription_created", api_id=api_id, tier=tier.value)
        return sub

    async def get_usage(self, api_id: str) -> list[UsageRecord]:
        return [
            UsageRecord(api_id=api_id, developer_id=uuid4(), requests_count=1250, tokens_consumed=45000, compute_time_ms=150000, cost=25.0, period="2024-01"),
            UsageRecord(api_id=api_id, developer_id=uuid4(), requests_count=890, tokens_consumed=32000, compute_time_ms=112000, cost=17.8, period="2024-01"),
        ]

    async def get_revenue_stats(self) -> APIRevenueStats:
        return APIRevenueStats(
            total_apis=len(_APIS), total_developers=342, total_requests_month=117600,
            monthly_revenue=48500.0, top_api="check-gdpr", revenue_growth_pct=23.5, avg_revenue_per_api=9700.0,
        )
