"""Zero-Config Compliance SaaS Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.saas_onboarding.models import (
    OnboardingProgress,
    OnboardingStep,
    SaaSMetrics,
    SaaSPlan,
    SaaSTenant,
    TenantStatus,
    UsageLimits,
)


logger = structlog.get_logger()

PLAN_LIMITS: dict[SaaSPlan, dict] = {
    SaaSPlan.FREE: {"max_repos": 3, "max_scans": 10, "max_api": 60, "ai": False, "sso": False, "policies": False, "support": "community"},
    SaaSPlan.TEAM: {"max_repos": 25, "max_scans": 100, "max_api": 300, "ai": True, "sso": False, "policies": False, "support": "email"},
    SaaSPlan.BUSINESS: {"max_repos": 100, "max_scans": 500, "max_api": 1000, "ai": True, "sso": True, "policies": True, "support": "priority"},
    SaaSPlan.ENTERPRISE: {"max_repos": -1, "max_scans": -1, "max_api": 5000, "ai": True, "sso": True, "policies": True, "support": "dedicated"},
}


class SaaSOnboardingService:
    """Zero-config SaaS onboarding and tenant management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._tenants: dict[str, SaaSTenant] = {}
        self._progress: dict[str, OnboardingProgress] = {}

    async def create_tenant(
        self,
        name: str,
        owner_email: str,
        plan: str = "free",
        region: str = "us-east-1",
    ) -> SaaSTenant:
        now = datetime.now(UTC)
        slug = name.lower().replace(" ", "-").replace(".", "-")[:50]
        limits = PLAN_LIMITS[SaaSPlan(plan)]
        tenant = SaaSTenant(
            name=name,
            slug=slug,
            owner_email=owner_email,
            plan=SaaSPlan(plan),
            status=TenantStatus.PROVISIONING,
            repo_limit=limits["max_repos"],
            onboarding_step=OnboardingStep.SIGNUP,
            region=region,
            created_at=now,
        )
        self._tenants[slug] = tenant

        progress = OnboardingProgress(
            tenant_id=tenant.id,
            current_step=OnboardingStep.SIGNUP,
            steps_completed=["signup"],
            started_at=now,
        )
        self._progress[slug] = progress

        tenant.status = TenantStatus.ACTIVE
        tenant.activated_at = now
        logger.info("Tenant created", slug=slug, plan=plan, region=region)
        return tenant

    async def advance_onboarding(self, slug: str, step: str, data: dict | None = None) -> OnboardingProgress | None:
        tenant = self._tenants.get(slug)
        progress = self._progress.get(slug)
        if not tenant or not progress:
            return None

        onboarding_step = OnboardingStep(step)
        progress.current_step = onboarding_step
        if step not in progress.steps_completed:
            progress.steps_completed.append(step)
        tenant.onboarding_step = onboarding_step

        if step == "connect_scm" and data:
            tenant.scm_provider = data.get("provider", "")
            tenant.scm_org = data.get("organization", "")
        elif step == "select_repos" and data:
            tenant.repos_connected = data.get("repo_count", 0)
        elif step == "first_scan" and data:
            tenant.first_scan_score = data.get("score")
            progress.time_to_first_scan_seconds = (datetime.now(UTC) - (progress.started_at or datetime.now(UTC))).total_seconds()
        elif step == "completed":
            tenant.onboarding_completed = True
            progress.completed_at = datetime.now(UTC)

        logger.info("Onboarding advanced", slug=slug, step=step)
        return progress

    def get_tenant(self, slug: str) -> SaaSTenant | None:
        return self._tenants.get(slug)

    def get_onboarding_progress(self, slug: str) -> OnboardingProgress | None:
        return self._progress.get(slug)

    def get_usage_limits(self, plan: str) -> UsageLimits:
        saas_plan = SaaSPlan(plan)
        limits = PLAN_LIMITS[saas_plan]
        return UsageLimits(
            plan=saas_plan,
            max_repos=limits["max_repos"],
            max_scans_per_day=limits["max_scans"],
            max_api_calls_per_minute=limits["max_api"],
            ai_features_enabled=limits["ai"],
            sso_enabled=limits["sso"],
            custom_policies_enabled=limits["policies"],
            support_tier=limits["support"],
        )

    async def upgrade_plan(self, slug: str, new_plan: str) -> SaaSTenant | None:
        tenant = self._tenants.get(slug)
        if not tenant:
            return None
        saas_plan = SaaSPlan(new_plan)
        tenant.plan = saas_plan
        tenant.repo_limit = PLAN_LIMITS[saas_plan]["max_repos"]
        logger.info("Plan upgraded", slug=slug, plan=new_plan)
        return tenant

    def list_tenants(self, plan: SaaSPlan | None = None, limit: int = 50) -> list[SaaSTenant]:
        results = list(self._tenants.values())
        if plan:
            results = [t for t in results if t.plan == plan]
        return sorted(results, key=lambda t: t.created_at or datetime.min.replace(tzinfo=UTC), reverse=True)[:limit]

    def get_metrics(self) -> SaaSMetrics:
        tenants = list(self._tenants.values())
        active = [t for t in tenants if t.status == TenantStatus.ACTIVE]
        by_plan: dict[str, int] = {}
        for t in tenants:
            by_plan[t.plan.value] = by_plan.get(t.plan.value, 0) + 1
        completed = [p for p in self._progress.values() if p.completed_at]
        avg_time = 0.0
        if completed:
            times = [p.time_to_first_scan_seconds for p in completed if p.time_to_first_scan_seconds]
            avg_time = round(sum(times) / len(times) / 60, 1) if times else 0.0
        return SaaSMetrics(
            total_tenants=len(tenants),
            active_tenants=len(active),
            by_plan=by_plan,
            avg_time_to_first_scan_min=avg_time,
            onboarding_completion_rate=round(len(completed) / len(tenants), 2) if tenants else 0.0,
            total_repos_connected=sum(t.repos_connected for t in tenants),
        )
