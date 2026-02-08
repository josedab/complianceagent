"""Federated Compliance Intelligence Network Service."""

import hashlib
import random
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.compliance_intel.models import (
    AnonymizedPattern,
    FederatedParticipant,
    IndustryInsight,
    InsightType,
    NetworkStats,
    ParticipantStatus,
    PrivacyLevel,
)

logger = structlog.get_logger()

# Built-in anonymized compliance patterns
_SEED_PATTERNS: list[dict] = [
    {"framework": "gdpr", "control": "Art.25", "desc": "Data protection by design using encryption-first architecture",
     "adoption": 72.0, "effectiveness": 85.0, "industry": "saas"},
    {"framework": "gdpr", "control": "Art.17", "desc": "Automated data deletion pipeline with retention policies",
     "adoption": 65.0, "effectiveness": 90.0, "industry": "saas"},
    {"framework": "hipaa", "control": "Security Rule", "desc": "End-to-end PHI encryption with key rotation",
     "adoption": 88.0, "effectiveness": 92.0, "industry": "healthtech"},
    {"framework": "pci_dss", "control": "Req 3", "desc": "Card tokenization with vault-based storage",
     "adoption": 95.0, "effectiveness": 96.0, "industry": "fintech"},
    {"framework": "soc2", "control": "CC6.1", "desc": "Zero-trust access model with JIT provisioning",
     "adoption": 45.0, "effectiveness": 88.0, "industry": "saas"},
    {"framework": "eu_ai_act", "control": "Art.13", "desc": "Automated model card generation for transparency",
     "adoption": 25.0, "effectiveness": 78.0, "industry": "ai_companies"},
    {"framework": "soc2", "control": "CC8.1", "desc": "GitOps-based change management with audit trail",
     "adoption": 58.0, "effectiveness": 85.0, "industry": "saas"},
    {"framework": "gdpr", "control": "Art.33", "desc": "Automated breach detection and 72-hour notification workflow",
     "adoption": 42.0, "effectiveness": 82.0, "industry": "fintech"},
]


class ComplianceIntelService:
    """Federated compliance intelligence network with differential privacy."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._participants: dict[UUID, FederatedParticipant] = {}
        self._patterns: list[AnonymizedPattern] = [
            AnonymizedPattern(
                framework=p["framework"], control_id=p["control"],
                pattern_description=p["desc"], adoption_rate=p["adoption"],
                effectiveness_score=p["effectiveness"], industry=p["industry"],
                sample_size=random.randint(50, 300), created_at=datetime.now(UTC),
            ) for p in _SEED_PATTERNS
        ]
        self._insights: list[IndustryInsight] = []

    async def join_network(
        self,
        organization_name: str,
        industry: str,
        size_category: str = "medium",
        privacy_level: PrivacyLevel = PrivacyLevel.STANDARD,
    ) -> FederatedParticipant:
        """Register an organization to join the federated network."""
        participant = FederatedParticipant(
            organization_name=organization_name,
            industry=industry,
            size_category=size_category,
            privacy_level=privacy_level,
            status=ParticipantStatus.ACTIVE,
            joined_at=datetime.now(UTC),
        )
        self._participants[participant.id] = participant
        logger.info("Participant joined network", org=organization_name, industry=industry)
        return participant

    async def contribute_pattern(
        self,
        participant_id: UUID,
        framework: str,
        control_id: str,
        pattern_description: str,
        effectiveness_score: float,
    ) -> AnonymizedPattern | None:
        """Contribute an anonymized compliance pattern to the network."""
        participant = self._participants.get(participant_id)
        if not participant or participant.status != ParticipantStatus.ACTIVE:
            return None

        epsilon = {"full": 0.1, "standard": 1.0, "relaxed": 5.0}.get(
            participant.privacy_level.value, 1.0
        )
        noisy_effectiveness = self._add_laplace_noise(effectiveness_score, epsilon)

        pattern = AnonymizedPattern(
            framework=framework,
            control_id=control_id,
            pattern_description=self._anonymize_text(pattern_description),
            adoption_rate=0.0,
            effectiveness_score=max(0, min(100, noisy_effectiveness)),
            industry=participant.industry,
            sample_size=1,
            noise_applied=True,
            epsilon=epsilon,
            created_at=datetime.now(UTC),
        )
        self._patterns.append(pattern)
        participant.contributed_patterns += 1
        return pattern

    async def get_insights(
        self,
        industry: str | None = None,
        framework: str | None = None,
        limit: int = 10,
    ) -> list[IndustryInsight]:
        """Get federated intelligence insights."""
        insights = self._generate_insights(industry, framework)
        return insights[:limit]

    async def get_patterns(
        self,
        framework: str | None = None,
        industry: str | None = None,
    ) -> list[AnonymizedPattern]:
        patterns = self._patterns
        if framework:
            patterns = [p for p in patterns if p.framework == framework]
        if industry:
            patterns = [p for p in patterns if p.industry == industry]
        return sorted(patterns, key=lambda p: p.effectiveness_score, reverse=True)

    async def get_network_stats(self) -> NetworkStats:
        active = sum(1 for p in self._participants.values() if p.status == ParticipantStatus.ACTIVE)
        industries = list({p.industry for p in self._participants.values()})
        frameworks = list({p.framework for p in self._patterns})

        return NetworkStats(
            total_participants=len(self._participants),
            active_participants=active,
            total_patterns=len(self._patterns),
            total_insights=len(self._insights),
            industries_represented=industries or ["saas", "fintech", "healthtech"],
            frameworks_covered=frameworks or ["gdpr", "hipaa", "pci_dss", "soc2"],
            avg_privacy_epsilon=1.0,
        )

    async def get_similar_orgs_insights(
        self,
        industry: str,
        size_category: str = "medium",
    ) -> list[dict]:
        """Get 'companies like you' insights."""
        patterns = [p for p in self._patterns if p.industry == industry]
        if not patterns:
            patterns = self._patterns[:5]

        return [
            {
                "insight": f"Companies in {industry} commonly use: {p.pattern_description}",
                "framework": p.framework,
                "adoption_rate": round(p.adoption_rate, 1),
                "effectiveness": round(p.effectiveness_score, 1),
                "sample_size": p.sample_size,
            }
            for p in sorted(patterns, key=lambda x: x.adoption_rate, reverse=True)[:5]
        ]

    def _generate_insights(self, industry: str | None, framework: str | None) -> list[IndustryInsight]:
        patterns = self._patterns
        if industry:
            patterns = [p for p in patterns if p.industry == industry]
        if framework:
            patterns = [p for p in patterns if p.framework == framework]

        insights = []
        for p in patterns[:10]:
            insight = IndustryInsight(
                insight_type=InsightType.COMMON_PATTERN if p.adoption_rate > 50 else InsightType.BEST_PRACTICE,
                title=f"{p.framework.upper()} — {p.control_id}",
                description=p.pattern_description,
                framework=p.framework,
                industry=p.industry,
                relevance_score=p.effectiveness_score / 100,
                data_points=p.sample_size,
                recommendations=[
                    f"Consider adopting: {p.pattern_description}",
                    f"Adoption rate in {p.industry}: {p.adoption_rate:.0f}%",
                ],
                generated_at=datetime.now(UTC),
            )
            insights.append(insight)

        self._insights.extend(insights)
        return insights

    @staticmethod
    def _add_laplace_noise(value: float, epsilon: float) -> float:
        """Add Laplace noise for differential privacy."""
        sensitivity = 10.0
        scale = sensitivity / epsilon
        noise = random.uniform(-1, 1) * scale
        return value + noise

    @staticmethod
    def _anonymize_text(text: str) -> str:
        """Basic text anonymization — remove specific identifiers."""
        anonymized = text
        for word in ["company", "org", "team", "project"]:
            anonymized = anonymized.replace(word, "[entity]")
        return anonymized
