"""SaaS Platform Service."""

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.saas_tenant import SaasTenant, TenantPlan, TenantStatus, TenantUsageRecord
from app.services.saas_platform.models import (
    OnboardingStep,
    ResourceLimits,
    TenantConfig,
    TenantProvisionResult,
    UsageSummary,
)

logger = structlog.get_logger()


class SaaSPlatformService:
    """Service for SaaS tenant management and provisioning."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def provision_tenant(self, config: TenantConfig) -> TenantProvisionResult:
        """Provision a new SaaS tenant."""
        logger.info("Provisioning tenant", slug=config.slug, plan=config.plan)

        # Get default resource limits for the plan
        plan = TenantPlan(config.plan) if config.plan else TenantPlan.FREE
        limits = self._get_default_limits(plan)

        # Create tenant record
        tenant = SaasTenant(
            name=config.name,
            slug=config.slug,
            plan=plan,
            status=TenantStatus.TRIAL,
            owner_user_id=UUID("00000000-0000-0000-0000-000000000000"),  # Set by caller
            settings={
                "industry": config.industry,
                "jurisdictions": config.jurisdictions,
                "github_org": config.github_org,
            },
            resource_limits=limits.to_dict(),
            trial_ends_at=datetime.now(UTC) + timedelta(days=14),
        )
        self.db.add(tenant)
        await self.db.flush()
        await self.db.refresh(tenant)

        # Generate API key
        api_key = f"ca_{secrets.token_urlsafe(32)}"

        # Define onboarding steps
        onboarding_steps = [
            OnboardingStep(
                id="connect-github",
                name="Connect GitHub",
                description="Connect your GitHub organization to enable repository scanning.",
            ),
            OnboardingStep(
                id="select-regulations",
                name="Select Regulations",
                description="Choose the regulations applicable to your organization.",
            ),
            OnboardingStep(
                id="invite-team",
                name="Invite Team Members",
                description="Invite your team to collaborate on compliance.",
            ),
            OnboardingStep(
                id="first-scan",
                name="Run First Scan",
                description="Run your first compliance scan on a repository.",
            ),
            OnboardingStep(
                id="review-dashboard",
                name="Review Dashboard",
                description="Review your compliance dashboard and risk overview.",
            ),
        ]

        # Store onboarding steps in tenant settings
        tenant_settings = dict(tenant.settings)
        tenant_settings["onboarding_steps"] = [s.to_dict() for s in onboarding_steps]
        tenant.settings = tenant_settings
        await self.db.flush()

        logger.info("Tenant provisioned", tenant_id=str(tenant.id), slug=config.slug)

        return TenantProvisionResult(
            tenant_id=tenant.id,
            status="provisioned",
            api_key=api_key,
            onboarding_steps=onboarding_steps,
            dashboard_url=f"/dashboard/{tenant.slug}",
        )

    async def get_tenant(self, tenant_id: UUID) -> SaasTenant | None:
        """Get a tenant by ID."""
        result = await self.db.execute(
            select(SaasTenant).where(SaasTenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def update_tenant_plan(self, tenant_id: UUID, plan: TenantPlan) -> SaasTenant:
        """Update a tenant's subscription plan."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        old_plan = tenant.plan
        tenant.plan = plan
        tenant.resource_limits = self._get_default_limits(plan).to_dict()

        # Activate if currently in trial
        if tenant.status == TenantStatus.TRIAL:
            tenant.status = TenantStatus.ACTIVE

        await self.db.flush()
        await self.db.refresh(tenant)

        logger.info(
            "Tenant plan updated",
            tenant_id=str(tenant_id),
            old_plan=old_plan.value,
            new_plan=plan.value,
        )

        return tenant

    async def suspend_tenant(self, tenant_id: UUID, reason: str) -> None:
        """Suspend a tenant."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        tenant.status = TenantStatus.SUSPENDED
        tenant_settings = dict(tenant.settings)
        tenant_settings["suspension_reason"] = reason
        tenant_settings["suspended_at"] = datetime.now(UTC).isoformat()
        tenant.settings = tenant_settings
        await self.db.flush()

        logger.info("Tenant suspended", tenant_id=str(tenant_id), reason=reason)

    async def get_onboarding_status(self, tenant_id: UUID) -> list[OnboardingStep]:
        """Get onboarding status for a tenant."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        steps_data = tenant.settings.get("onboarding_steps", [])
        steps = []
        for s in steps_data:
            steps.append(
                OnboardingStep(
                    id=s["id"],
                    name=s["name"],
                    description=s["description"],
                    status=s.get("status", "pending"),
                    completed_at=(
                        datetime.fromisoformat(s["completed_at"])
                        if s.get("completed_at")
                        else None
                    ),
                )
            )
        return steps

    async def complete_onboarding_step(
        self, tenant_id: UUID, step_id: str
    ) -> OnboardingStep:
        """Mark an onboarding step as completed."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        steps_data = tenant.settings.get("onboarding_steps", [])
        completed_step = None

        for s in steps_data:
            if s["id"] == step_id:
                s["status"] = "completed"
                s["completed_at"] = datetime.now(UTC).isoformat()
                completed_step = OnboardingStep(
                    id=s["id"],
                    name=s["name"],
                    description=s["description"],
                    status="completed",
                    completed_at=datetime.now(UTC),
                )
                break

        if not completed_step:
            raise ValueError(f"Onboarding step {step_id} not found")

        # Update settings
        tenant_settings = dict(tenant.settings)
        tenant_settings["onboarding_steps"] = steps_data
        tenant.settings = tenant_settings

        # Check if all steps are completed
        all_completed = all(
            s.get("status") in ("completed", "skipped") for s in steps_data
        )
        if all_completed:
            tenant.onboarding_completed_at = datetime.now(UTC)

        await self.db.flush()

        logger.info(
            "Onboarding step completed",
            tenant_id=str(tenant_id),
            step_id=step_id,
        )

        return completed_step

    async def record_usage(
        self, tenant_id: UUID, metric: str, value: float
    ) -> None:
        """Record a usage metric for a tenant."""
        now = datetime.now(UTC)
        record = TenantUsageRecord(
            tenant_id=tenant_id,
            metric=metric,
            value=value,
            period_start=now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            period_end=(now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=32)).replace(day=1) - timedelta(seconds=1),
            record_metadata={},
        )
        self.db.add(record)
        await self.db.flush()

        logger.info(
            "Usage recorded",
            tenant_id=str(tenant_id),
            metric=metric,
            value=value,
        )

    async def get_usage_summary(self, tenant_id: UUID) -> UsageSummary:
        """Get usage summary for a tenant."""
        now = datetime.now(UTC)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        result = await self.db.execute(
            select(TenantUsageRecord).where(
                TenantUsageRecord.tenant_id == tenant_id,
                TenantUsageRecord.period_start >= period_start,
            )
        )
        records = result.scalars().all()

        summary = UsageSummary(tenant_id=tenant_id, period="current")
        for record in records:
            if record.metric == "api_calls":
                summary.api_calls += int(record.value)
            elif record.metric == "scans_run":
                summary.scans_run += int(record.value)
            elif record.metric == "regulations_tracked":
                summary.regulations_tracked += int(record.value)
            elif record.metric == "storage_mb":
                summary.storage_mb += record.value
            elif record.metric == "seats_used":
                summary.seats_used = max(summary.seats_used, int(record.value))

        return summary

    async def check_resource_limits(
        self, tenant_id: UUID, resource: str
    ) -> bool:
        """Check if a tenant is within resource limits. Returns True if within limits."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        limits = tenant.resource_limits
        summary = await self.get_usage_summary(tenant_id)

        limit_checks = {
            "repos": ("max_repos", 0),
            "scans": ("max_scans_per_month", summary.scans_run),
            "api_calls": ("max_api_calls_per_day", summary.api_calls),
            "seats": ("max_seats", summary.seats_used),
            "storage": ("max_storage_mb", summary.storage_mb),
        }

        check = limit_checks.get(resource)
        if not check:
            return True

        limit_key, current_value = check
        max_value = limits.get(limit_key, 0)
        return current_value < max_value

    @staticmethod
    def _get_default_limits(plan: TenantPlan) -> ResourceLimits:
        """Get default resource limits for a plan."""
        plan_limits = {
            TenantPlan.FREE: ResourceLimits(
                max_repos=3,
                max_scans_per_month=50,
                max_api_calls_per_day=500,
                max_seats=2,
                max_storage_mb=100,
            ),
            TenantPlan.STARTER: ResourceLimits(
                max_repos=10,
                max_scans_per_month=500,
                max_api_calls_per_day=5000,
                max_seats=10,
                max_storage_mb=1000,
            ),
            TenantPlan.PROFESSIONAL: ResourceLimits(
                max_repos=50,
                max_scans_per_month=5000,
                max_api_calls_per_day=50000,
                max_seats=50,
                max_storage_mb=10000,
            ),
            TenantPlan.ENTERPRISE: ResourceLimits(
                max_repos=999999,
                max_scans_per_month=999999,
                max_api_calls_per_day=999999,
                max_seats=999999,
                max_storage_mb=999999,
            ),
        }
        return plan_limits.get(plan, ResourceLimits())


def get_saas_platform_service(db: AsyncSession) -> SaaSPlatformService:
    """Factory function to create SaaS Platform service."""
    return SaaSPlatformService(db=db)
