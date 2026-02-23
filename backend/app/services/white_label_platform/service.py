"""White Label Platform Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.white_label_platform.models import (
    InstanceStatus,
    PartnerAnalytics,
    PartnerConfig,
    PartnerTier,
    WhiteLabelInstance,
    WhiteLabelStats,
)


logger = structlog.get_logger()


class WhiteLabelPlatformService:
    """Multi-tenant white-label compliance platform management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._partners: dict[UUID, PartnerConfig] = {}
        self._instances: dict[UUID, WhiteLabelInstance] = {}
        self._seed_data()

    def _seed_data(self) -> None:
        """Seed sample partner configurations."""
        partners = [
            PartnerConfig(
                partner_name="SecureComply Solutions",
                tier=PartnerTier.PLATINUM,
                domain="compliance.securecomply.io",
                branding={
                    "logo": "https://cdn.securecomply.io/logo.svg",
                    "color_primary": "#1a3a5c",
                    "color_secondary": "#4a90d9",
                    "favicon": "https://cdn.securecomply.io/favicon.ico",
                    "company_name": "SecureComply Solutions",
                    "domain": "compliance.securecomply.io",
                },
                features_enabled=[
                    "audit_trail",
                    "policy_engine",
                    "risk_assessment",
                    "evidence_vault",
                    "regulatory_feed",
                    "ai_copilot",
                ],
                max_tenants=50,
                status=InstanceStatus.ACTIVE,
                onboarded_at=datetime(2024, 6, 15, 10, 0, tzinfo=UTC),
            ),
            PartnerConfig(
                partner_name="DataGuard Pro",
                tier=PartnerTier.GOLD,
                domain="platform.dataguardpro.com",
                branding={
                    "logo": "https://assets.dataguardpro.com/logo.png",
                    "color_primary": "#2d5016",
                    "color_secondary": "#6abf40",
                    "favicon": "https://assets.dataguardpro.com/favicon.ico",
                    "company_name": "DataGuard Pro",
                    "domain": "platform.dataguardpro.com",
                },
                features_enabled=[
                    "audit_trail",
                    "policy_engine",
                    "risk_assessment",
                    "evidence_vault",
                ],
                max_tenants=25,
                status=InstanceStatus.ACTIVE,
                onboarded_at=datetime(2024, 9, 1, 14, 0, tzinfo=UTC),
            ),
            PartnerConfig(
                partner_name="ReguTech Ventures",
                tier=PartnerTier.SILVER,
                domain="app.regutechventures.com",
                branding={
                    "logo": "https://cdn.regutech.com/logo.svg",
                    "color_primary": "#4a1942",
                    "color_secondary": "#9b59b6",
                    "favicon": "https://cdn.regutech.com/favicon.ico",
                    "company_name": "ReguTech Ventures",
                    "domain": "app.regutechventures.com",
                },
                features_enabled=[
                    "audit_trail",
                    "policy_engine",
                ],
                max_tenants=10,
                status=InstanceStatus.ACTIVE,
                onboarded_at=datetime(2025, 1, 10, 9, 0, tzinfo=UTC),
            ),
        ]

        for partner in partners:
            self._partners[partner.id] = partner

        # Seed instances for partners
        instance_data = [
            (partners[0].id, "Acme Healthcare", "acme-healthcare", 45, 12),
            (partners[0].id, "Global Finance Corp", "global-finance", 120, 35),
            (partners[0].id, "Nordic Insurance AS", "nordic-insurance", 30, 8),
            (partners[1].id, "TechStartup GmbH", "techstartup", 15, 5),
            (partners[1].id, "E-Commerce Holdings", "ecommerce-holdings", 60, 18),
            (partners[2].id, "LocalBank Ltd", "localbank", 20, 4),
        ]

        for partner_id, name, slug, users, repos in instance_data:
            instance = WhiteLabelInstance(
                partner_id=partner_id,
                tenant_name=name,
                tenant_slug=slug,
                status=InstanceStatus.ACTIVE,
                users=users,
                repos=repos,
                created_at=datetime(2025, 1, 15, 10, 0, tzinfo=UTC),
            )
            self._instances[instance.id] = instance

        logger.info(
            "White-label platform seeded",
            partner_count=len(self._partners),
            instance_count=len(self._instances),
        )

    async def onboard_partner(
        self,
        partner_name: str,
        tier: str,
        domain: str,
        branding: dict,
    ) -> PartnerConfig:
        """Onboard a new white-label partner."""
        partner = PartnerConfig(
            partner_name=partner_name,
            tier=PartnerTier(tier),
            domain=domain,
            branding=branding,
            features_enabled=["audit_trail", "policy_engine"],
            status=InstanceStatus.ACTIVE,
            onboarded_at=datetime.now(UTC),
        )

        if partner.tier == PartnerTier.PLATINUM:
            partner.max_tenants = 50
            partner.features_enabled.extend(["risk_assessment", "evidence_vault", "regulatory_feed", "ai_copilot"])
        elif partner.tier == PartnerTier.GOLD:
            partner.max_tenants = 25
            partner.features_enabled.extend(["risk_assessment", "evidence_vault"])

        self._partners[partner.id] = partner

        logger.info("Partner onboarded", partner_id=str(partner.id), name=partner_name, tier=tier)
        return partner

    async def create_instance(
        self,
        partner_id: UUID,
        tenant_name: str,
    ) -> WhiteLabelInstance:
        """Create a new tenant instance for a partner."""
        partner = self._partners.get(partner_id)
        if not partner:
            msg = f"Partner {partner_id} not found"
            raise ValueError(msg)

        current_count = sum(
            1 for i in self._instances.values()
            if i.partner_id == partner_id and i.status != InstanceStatus.DECOMMISSIONED
        )
        if current_count >= partner.max_tenants:
            msg = f"Partner {partner.partner_name} has reached maximum tenant limit ({partner.max_tenants})"
            raise ValueError(msg)

        slug = tenant_name.lower().replace(" ", "-")

        instance = WhiteLabelInstance(
            partner_id=partner_id,
            tenant_name=tenant_name,
            tenant_slug=slug,
            status=InstanceStatus.ACTIVE,
            created_at=datetime.now(UTC),
        )
        self._instances[instance.id] = instance

        logger.info(
            "Instance created",
            instance_id=str(instance.id),
            partner_id=str(partner_id),
            tenant=tenant_name,
        )
        return instance

    async def get_partner_analytics(self, partner_id: UUID) -> PartnerAnalytics:
        """Get analytics for a specific partner."""
        partner = self._partners.get(partner_id)
        if not partner:
            msg = f"Partner {partner_id} not found"
            raise ValueError(msg)

        instances = [i for i in self._instances.values() if i.partner_id == partner_id]
        total_users = sum(i.users for i in instances)
        total_repos = sum(i.repos for i in instances)

        mrr_rates = {
            PartnerTier.SILVER: 2500.0,
            PartnerTier.GOLD: 7500.0,
            PartnerTier.PLATINUM: 15000.0,
        }
        base_mrr = mrr_rates.get(partner.tier, 2500.0)
        mrr = base_mrr + (len(instances) * 500.0)

        usage_hours = total_users * 12.5

        return PartnerAnalytics(
            partner_id=partner_id,
            total_tenants=len(instances),
            total_users=total_users,
            total_repos=total_repos,
            mrr=mrr,
            usage_hours=usage_hours,
        )

    async def suspend_instance(self, instance_id: UUID) -> WhiteLabelInstance:
        """Suspend a tenant instance."""
        instance = self._instances.get(instance_id)
        if not instance:
            msg = f"Instance {instance_id} not found"
            raise ValueError(msg)

        instance.status = InstanceStatus.SUSPENDED

        logger.info("Instance suspended", instance_id=str(instance_id))
        return instance

    async def list_partners(
        self,
        tier: PartnerTier | None = None,
    ) -> list[PartnerConfig]:
        """List partners with optional tier filter."""
        partners = list(self._partners.values())

        if tier is not None:
            partners = [p for p in partners if p.tier == tier]

        return partners

    async def list_instances(
        self,
        partner_id: UUID | None = None,
    ) -> list[WhiteLabelInstance]:
        """List instances with optional partner filter."""
        instances = list(self._instances.values())

        if partner_id is not None:
            instances = [i for i in instances if i.partner_id == partner_id]

        return instances

    async def get_stats(self) -> WhiteLabelStats:
        """Get overall platform statistics."""
        partners = list(self._partners.values())
        instances = list(self._instances.values())

        by_tier: dict[str, int] = {}
        for p in partners:
            by_tier[p.tier.value] = by_tier.get(p.tier.value, 0) + 1

        by_status: dict[str, int] = {}
        for i in instances:
            by_status[i.status.value] = by_status.get(i.status.value, 0) + 1

        total_mrr = 0.0
        for partner in partners:
            analytics = await self.get_partner_analytics(partner.id)
            total_mrr += analytics.mrr

        return WhiteLabelStats(
            total_partners=len(partners),
            total_instances=len(instances),
            by_tier=by_tier,
            total_mrr=total_mrr,
            by_status=by_status,
        )
