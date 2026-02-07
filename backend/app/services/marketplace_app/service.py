"""GitHub/GitLab Marketplace App Service."""

from datetime import UTC, datetime
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
