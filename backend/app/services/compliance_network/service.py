"""Open Compliance Data Network Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.compliance_network.models import (
    BenchmarkCategory,
    IndustryBenchmark,
    NetworkMembership,
    NetworkStats,
    ThreatAlert,
)


logger = structlog.get_logger()

_INDUSTRIES = [
    "financial_services",
    "healthcare",
    "technology",
    "retail",
    "manufacturing",
    "energy",
    "government",
    "education",
]

_SEED_BENCHMARKS: dict[str, dict[str, tuple[float, float, float]]] = {
    "financial_services": {
        "posture_score": (72.0, 81.0, 90.0),
        "time_to_remediate": (24.0, 48.0, 96.0),
        "audit_readiness": (65.0, 78.0, 88.0),
        "violation_density": (2.1, 4.5, 8.2),
        "framework_coverage": (70.0, 82.0, 93.0),
    },
    "healthcare": {
        "posture_score": (68.0, 77.0, 86.0),
        "time_to_remediate": (36.0, 72.0, 120.0),
        "audit_readiness": (60.0, 73.0, 85.0),
        "violation_density": (3.0, 6.0, 10.5),
        "framework_coverage": (65.0, 78.0, 90.0),
    },
    "technology": {
        "posture_score": (76.0, 85.0, 93.0),
        "time_to_remediate": (12.0, 24.0, 48.0),
        "audit_readiness": (70.0, 82.0, 92.0),
        "violation_density": (1.5, 3.2, 6.0),
        "framework_coverage": (75.0, 87.0, 95.0),
    },
    "retail": {
        "posture_score": (65.0, 75.0, 84.0),
        "time_to_remediate": (30.0, 60.0, 108.0),
        "audit_readiness": (58.0, 70.0, 82.0),
        "violation_density": (2.8, 5.5, 9.0),
        "framework_coverage": (60.0, 74.0, 86.0),
    },
    "manufacturing": {
        "posture_score": (60.0, 72.0, 82.0),
        "time_to_remediate": (48.0, 96.0, 168.0),
        "audit_readiness": (55.0, 68.0, 80.0),
        "violation_density": (3.5, 7.0, 12.0),
        "framework_coverage": (55.0, 70.0, 83.0),
    },
    "energy": {
        "posture_score": (62.0, 74.0, 84.0),
        "time_to_remediate": (40.0, 80.0, 144.0),
        "audit_readiness": (58.0, 71.0, 83.0),
        "violation_density": (3.0, 6.5, 11.0),
        "framework_coverage": (58.0, 72.0, 85.0),
    },
    "government": {
        "posture_score": (70.0, 80.0, 89.0),
        "time_to_remediate": (36.0, 72.0, 120.0),
        "audit_readiness": (68.0, 79.0, 90.0),
        "violation_density": (2.0, 4.0, 7.5),
        "framework_coverage": (72.0, 84.0, 94.0),
    },
    "education": {
        "posture_score": (58.0, 70.0, 80.0),
        "time_to_remediate": (48.0, 96.0, 192.0),
        "audit_readiness": (50.0, 65.0, 78.0),
        "violation_density": (4.0, 8.0, 14.0),
        "framework_coverage": (50.0, 66.0, 80.0),
    },
}

_SEED_THREATS = [
    ThreatAlert(
        title="Log4Shell Variant in Logging Libraries",
        description="New variant of Log4Shell affecting Java logging frameworks with compliance implications for SOC2 and HIPAA",
        affected_frameworks=["SOC2", "HIPAA"],
        severity="critical",
        reported_by_count=847,
        confidence=0.95,
    ),
    ThreatAlert(
        title="GDPR Consent Bypass via Third-Party SDKs",
        description="Multiple third-party SDKs found bypassing GDPR consent mechanisms through side-channel data collection",
        affected_frameworks=["GDPR"],
        severity="high",
        reported_by_count=432,
        confidence=0.88,
    ),
    ThreatAlert(
        title="PCI-DSS Key Rotation Gap",
        description="Common misconfiguration in cloud KMS services leading to non-compliant key rotation periods",
        affected_frameworks=["PCI-DSS", "SOC2"],
        severity="medium",
        reported_by_count=265,
        confidence=0.82,
    ),
]


class ComplianceNetworkService:
    """Service for the open compliance data network."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._members: dict[str, NetworkMembership] = {}
        self._threats: list[ThreatAlert] = list(_SEED_THREATS)
        self._patterns: list[dict] = []
        self._stats = NetworkStats(
            total_members=1247,
            active_contributors=389,
            patterns_shared=2156,
            threats_detected=47,
            industries_represented=len(_INDUSTRIES),
        )

    async def join_network(
        self, organization_id: str, membership: NetworkMembership = NetworkMembership.FREE
    ) -> dict:
        """Join the compliance data network."""
        self._members[organization_id] = membership
        self._stats.total_members += 1
        if membership != NetworkMembership.FREE:
            self._stats.active_contributors += 1

        logger.info(
            "Network member joined", organization_id=organization_id, membership=membership.value
        )
        return {
            "organization_id": organization_id,
            "membership": membership.value,
            "joined_at": datetime.now(UTC).isoformat(),
            "benefits": self._get_benefits(membership),
        }

    def _get_benefits(self, membership: NetworkMembership) -> list[str]:
        """Get benefits for a membership tier."""
        benefits = ["Industry benchmarks", "Threat alerts"]
        if membership in (NetworkMembership.CONTRIBUTOR, NetworkMembership.PREMIUM):
            benefits.extend(["Detailed percentile rankings", "Pattern sharing"])
        if membership == NetworkMembership.PREMIUM:
            benefits.extend(["Custom benchmark cohorts", "Early threat warnings", "API access"])
        return benefits

    async def get_benchmarks(
        self, industry: str, your_values: dict[str, float] | None = None
    ) -> list[IndustryBenchmark]:
        """Get industry benchmarks with optional comparison to your values."""
        seed_data = _SEED_BENCHMARKS.get(industry)
        if not seed_data:
            return []

        values = your_values or {}
        benchmarks: list[IndustryBenchmark] = []

        for cat_name, (p25, med, p75) in seed_data.items():
            category = BenchmarkCategory(cat_name)
            your_val = values.get(cat_name, med)

            # Deterministic percentile calculation
            if your_val <= p25:
                percentile = round(25.0 * (your_val / p25), 1) if p25 > 0 else 0.0
            elif your_val <= med:
                percentile = (
                    round(25.0 + 25.0 * ((your_val - p25) / (med - p25)), 1)
                    if (med - p25) > 0
                    else 50.0
                )
            elif your_val <= p75:
                percentile = (
                    round(50.0 + 25.0 * ((your_val - med) / (p75 - med)), 1)
                    if (p75 - med) > 0
                    else 75.0
                )
            else:
                percentile = (
                    round(min(99.0, 75.0 + 25.0 * ((your_val - p75) / p75)), 1) if p75 > 0 else 99.0
                )

            benchmarks.append(
                IndustryBenchmark(
                    category=category,
                    industry=industry,
                    percentile_25=p25,
                    median=med,
                    percentile_75=p75,
                    your_value=your_val,
                    your_percentile=percentile,
                )
            )

        return benchmarks

    async def report_threat(
        self, title: str, description: str, affected_frameworks: list[str], severity: str = "medium"
    ) -> ThreatAlert:
        """Report a new compliance threat to the network."""
        threat = ThreatAlert(
            title=title,
            description=description,
            affected_frameworks=affected_frameworks,
            severity=severity,
            reported_by_count=1,
            confidence=0.5,
        )
        self._threats.append(threat)
        self._stats.threats_detected += 1

        logger.info("Threat reported", title=title, severity=severity)
        return threat

    async def list_threats(
        self, severity: str | None = None, framework: str | None = None
    ) -> list[ThreatAlert]:
        """List threats with optional filters."""
        results = list(self._threats)
        if severity:
            results = [t for t in results if t.severity == severity]
        if framework:
            results = [t for t in results if framework in t.affected_frameworks]
        return results

    async def get_network_stats(self) -> NetworkStats:
        """Get overall network statistics."""
        return self._stats

    async def get_industry_comparison(self, industry: str, your_score: float) -> dict:
        """Get a comparison of your score against industry peers."""
        seed_data = _SEED_BENCHMARKS.get(industry)
        if not seed_data:
            return {"industry": industry, "available": False}

        p25, med, p75 = seed_data["posture_score"]
        if your_score >= p75:
            position = "top_quartile"
        elif your_score >= med:
            position = "above_median"
        elif your_score >= p25:
            position = "below_median"
        else:
            position = "bottom_quartile"

        return {
            "industry": industry,
            "your_score": your_score,
            "industry_median": med,
            "industry_p25": p25,
            "industry_p75": p75,
            "position": position,
            "peers_count": self._stats.total_members,
        }

    async def contribute_pattern(self, organization_id: str, pattern: dict) -> dict:
        """Contribute a compliance pattern to the network."""
        membership = self._members.get(organization_id, NetworkMembership.FREE)
        if membership == NetworkMembership.FREE:
            return {"accepted": False, "reason": "Contributor or premium membership required"}

        entry = {
            "organization_id": organization_id,
            "pattern": pattern,
            "contributed_at": datetime.now(UTC).isoformat(),
        }
        self._patterns.append(entry)
        self._stats.patterns_shared += 1

        logger.info("Pattern contributed", organization_id=organization_id)
        return {"accepted": True, "pattern_id": len(self._patterns)}
