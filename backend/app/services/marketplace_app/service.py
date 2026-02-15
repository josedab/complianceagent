"""GitHub/GitLab Marketplace App Service."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.marketplace_app.models import (
    AppInstallation,
    AppPlatform,
    InstallationStatus,
    InstallationSyncResult,
    MarketplaceListingInfo,
    MarketplacePlan,
    PLAN_LIMITS,
    UsageRecord,
    UsageSummary,
    WebhookEvent,
)

logger = structlog.get_logger()


class MarketplaceAppService:
    """Service for managing GitHub/GitLab marketplace app installations."""

    def __init__(self, db: AsyncSession, github_client: object | None = None):
        self.db = db
        self.github = github_client
        self._installations: dict[UUID, AppInstallation] = {}
        self._webhook_log: list[WebhookEvent] = []

    async def handle_installation(
        self,
        platform: AppPlatform,
        external_id: int,
        account_login: str,
        account_type: str = "Organization",
        repositories: list[str] | None = None,
    ) -> AppInstallation:
        """Handle a new app installation event."""
        installation = AppInstallation(
            platform=platform,
            external_id=external_id,
            account_login=account_login,
            account_type=account_type,
            status=InstallationStatus.ACTIVE,
            repositories=repositories or [],
            installed_at=datetime.now(UTC),
            permissions={
                "checks": "write",
                "pull_requests": "write",
                "contents": "read",
                "metadata": "read",
            },
            events=["pull_request", "push", "check_run"],
        )

        self._installations[installation.id] = installation
        logger.info(
            "App installed",
            platform=platform.value,
            account=account_login,
            repos=len(installation.repositories),
        )
        return installation

    async def handle_uninstall(self, external_id: int) -> None:
        """Handle app uninstallation."""
        for inst in self._installations.values():
            if inst.external_id == external_id:
                inst.status = InstallationStatus.UNINSTALLED
                logger.info("App uninstalled", account=inst.account_login)
                return

    async def get_installation(self, installation_id: UUID) -> AppInstallation | None:
        """Get installation by ID."""
        return self._installations.get(installation_id)

    async def get_installation_by_external_id(self, external_id: int) -> AppInstallation | None:
        """Get installation by external platform ID."""
        for inst in self._installations.values():
            if inst.external_id == external_id:
                return inst
        return None

    async def list_installations(
        self,
        platform: AppPlatform | None = None,
        status: InstallationStatus | None = None,
    ) -> list[AppInstallation]:
        """List all installations with optional filters."""
        results = list(self._installations.values())
        if platform:
            results = [i for i in results if i.platform == platform]
        if status:
            results = [i for i in results if i.status == status]
        return results

    async def sync_repositories(self, installation_id: UUID) -> InstallationSyncResult:
        """Sync repositories for an installation."""
        installation = self._installations.get(installation_id)
        if not installation:
            return InstallationSyncResult()

        result = InstallationSyncResult(installation_id=installation_id)

        # In production, fetch from GitHub API
        logger.info(
            "Synced repositories",
            installation=str(installation_id),
            repos=len(installation.repositories),
        )
        result.scans_triggered = len(installation.repositories)
        return result

    async def process_webhook(self, event: WebhookEvent) -> dict:
        """Process an incoming webhook event."""
        self._webhook_log.append(event)
        event.received_at = datetime.now(UTC)

        handlers = {
            "installation": self._handle_installation_webhook,
            "pull_request": self._handle_pr_webhook,
            "push": self._handle_push_webhook,
        }

        handler = handlers.get(event.event_type)
        if handler:
            result = await handler(event)
            event.processed = True
            return result

        logger.debug("Unhandled webhook event", event_type=event.event_type)
        return {"status": "ignored", "event_type": event.event_type}

    async def update_plan(
        self, installation_id: UUID, plan: MarketplacePlan
    ) -> AppInstallation | None:
        """Update the plan for an installation."""
        installation = self._installations.get(installation_id)
        if installation:
            installation.plan = plan
            logger.info("Plan updated", installation=str(installation_id), plan=plan.value)
        return installation

    async def get_listing_info(self) -> MarketplaceListingInfo:
        """Get marketplace listing metadata."""
        return MarketplaceListingInfo(
            plans=[
                {"name": "Free", "price": 0, "repos": 3, "scans": 50},
                {"name": "Team", "price": 29, "repos": 25, "scans": 500},
                {"name": "Business", "price": 99, "repos": -1, "scans": 5000},
                {"name": "Enterprise", "price": -1, "repos": -1, "scans": -1},
            ],
            install_url="/api/v1/marketplace-app/install",
            webhook_url="/api/v1/marketplace-app/webhook",
        )

    async def _handle_installation_webhook(self, event: WebhookEvent) -> dict:
        """Handle installation webhook events."""
        action = event.action
        payload = event.payload

        if action == "created":
            installation = await self.handle_installation(
                platform=event.platform,
                external_id=event.installation_id,
                account_login=payload.get("account", {}).get("login", ""),
                repositories=payload.get("repositories", []),
            )
            return {"status": "installed", "id": str(installation.id)}

        if action == "deleted":
            await self.handle_uninstall(event.installation_id)
            return {"status": "uninstalled"}

        return {"status": "ignored", "action": action}

    async def _handle_pr_webhook(self, event: WebhookEvent) -> dict:
        """Handle pull request webhook events (triggers compliance scan)."""
        action = event.action
        if action not in ("opened", "synchronize", "reopened"):
            return {"status": "ignored", "action": action}

        pr_number = event.payload.get("number", 0)
        repo = event.payload.get("repository", {}).get("full_name", "")

        logger.info("PR compliance scan triggered", repo=repo, pr=pr_number)
        return {"status": "scan_triggered", "repo": repo, "pr": pr_number}

    async def _handle_push_webhook(self, event: WebhookEvent) -> dict:
        """Handle push webhook events."""
        ref = event.payload.get("ref", "")
        repo = event.payload.get("repository", {}).get("full_name", "")
        logger.info("Push event received", repo=repo, ref=ref)
        return {"status": "received", "repo": repo, "ref": ref}

    # ── Usage Metering ───────────────────────────────────────────────────

    def record_usage(
        self,
        installation_id: UUID,
        endpoint: str,
        method: str = "GET",
        response_time_ms: float = 0.0,
        status_code: int = 200,
        tokens_used: int = 0,
    ) -> UsageRecord:
        """Record an API usage event for metering."""
        if not hasattr(self, '_usage_records'):
            self._usage_records: list[UsageRecord] = []

        record = UsageRecord(
            installation_id=installation_id,
            endpoint=endpoint,
            method=method,
            response_time_ms=response_time_ms,
            status_code=status_code,
            tokens_used=tokens_used,
        )
        self._usage_records.append(record)
        return record

    def get_usage_summary(
        self,
        installation_id: str,
        period: str = "current_month",
    ) -> UsageSummary:
        """Get aggregated usage summary for an installation."""
        if not hasattr(self, '_usage_records'):
            self._usage_records: list[UsageRecord] = []

        inst_records = [
            r for r in self._usage_records
            if str(r.installation_id) == installation_id
        ]

        total_requests = len(inst_records)
        total_tokens = sum(r.tokens_used for r in inst_records)
        avg_rt = (
            sum(r.response_time_ms for r in inst_records) / total_requests
            if total_requests > 0 else 0.0
        )

        endpoints: dict[str, int] = {}
        for r in inst_records:
            endpoints[r.endpoint] = endpoints.get(r.endpoint, 0) + 1

        # Determine plan quota
        installation = self._get_installation_by_id(installation_id)
        plan = installation.plan.value if installation else "free"
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
        quota_limit = limits["monthly_requests"]
        quota_remaining = max(0, quota_limit - total_requests) if quota_limit > 0 else -1

        return UsageSummary(
            installation_id=installation_id,
            period=period,
            total_requests=total_requests,
            total_tokens=total_tokens,
            avg_response_time_ms=round(avg_rt, 2),
            endpoints_breakdown=endpoints,
            quota_limit=quota_limit,
            quota_used=total_requests,
            quota_remaining=quota_remaining,
            overage=quota_limit > 0 and total_requests > quota_limit,
        )

    def _get_installation_by_id(self, installation_id: str) -> Any:
        """Get installation by ID string."""
        for inst in self._installations.values():
            if str(inst.id) == installation_id:
                return inst
        return None

    def check_plan_enforcement(
        self,
        installation_id: str,
        action: str = "api_request",
    ) -> dict[str, Any]:
        """Check if an action is allowed under the current plan."""
        installation = self._get_installation_by_id(installation_id)
        if not installation:
            return {"allowed": False, "reason": "Installation not found"}

        plan = installation.plan.value
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

        # Enterprise has unlimited
        if limits["monthly_requests"] == -1:
            return {"allowed": True, "plan": plan, "reason": "Enterprise unlimited"}

        summary = self.get_usage_summary(installation_id)

        if action == "api_request" and summary.overage:
            return {
                "allowed": False,
                "plan": plan,
                "reason": f"Monthly request quota exceeded ({summary.quota_used}/{summary.quota_limit})",
                "upgrade_url": "/billing/upgrade",
            }

        repo_count = len(installation.repositories)
        if action == "add_repo" and limits["repos"] > 0 and repo_count >= limits["repos"]:
            return {
                "allowed": False,
                "plan": plan,
                "reason": f"Repository limit reached ({repo_count}/{limits['repos']})",
                "upgrade_url": "/billing/upgrade",
            }

        return {"allowed": True, "plan": plan, "reason": "Within plan limits"}
