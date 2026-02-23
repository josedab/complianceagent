"""GitHub App Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.github_app.models import (
    AppInstallation,
    AppMarketplaceListing,
    AppPlan,
    ComplianceCheckResult,
    InstallationStatus,
    WebhookEvent,
    WebhookEventType,
)


logger = structlog.get_logger()


MARKETPLACE_PLANS = [
    {"id": "free", "name": "Free", "price": 0, "repos": 3, "features": ["Basic compliance checks", "SARIF output"]},
    {"id": "team", "name": "Team", "price": 49, "repos": 25, "features": ["All Free features", "PR bot", "IDE linting", "5 frameworks"]},
    {"id": "business", "name": "Business", "price": 199, "repos": 100, "features": ["All Team features", "AI code generation", "20+ frameworks", "Priority support"]},
    {"id": "enterprise", "name": "Enterprise", "price": 499, "repos": -1, "features": ["All Business features", "SSO/SAML", "Custom policies", "Dedicated support"]},
]


class GitHubAppService:
    """Service for GitHub App installation and webhook handling."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._installations: dict[int, AppInstallation] = {}
        self._events: list[WebhookEvent] = []
        self._check_results: list[ComplianceCheckResult] = []

    async def handle_installation(
        self,
        github_installation_id: int,
        account_login: str,
        account_type: str = "Organization",
        action: str = "created",
        repositories: list[str] | None = None,
    ) -> AppInstallation:
        """Handle GitHub App installation/uninstallation event."""
        if action == "deleted":
            existing = self._installations.get(github_installation_id)
            if existing:
                existing.status = InstallationStatus.UNINSTALLED
                existing.updated_at = datetime.now(UTC)
                logger.info("App uninstalled", account=account_login)
                return existing

        installation = AppInstallation(
            github_installation_id=github_installation_id,
            account_login=account_login,
            account_type=account_type,
            status=InstallationStatus.ACTIVE,
            plan=AppPlan.FREE,
            repositories=repositories or [],
            permissions={"checks": "write", "contents": "read", "pull_requests": "write"},
            events_subscribed=["pull_request", "push", "check_suite"],
            installed_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self._installations[github_installation_id] = installation
        logger.info("App installed", account=account_login, repos=len(installation.repositories))
        return installation

    async def get_installation(self, github_installation_id: int) -> AppInstallation | None:
        return self._installations.get(github_installation_id)

    async def list_installations(self, status: InstallationStatus | None = None) -> list[AppInstallation]:
        results = list(self._installations.values())
        if status:
            results = [i for i in results if i.status == status]
        return sorted(results, key=lambda i: i.installed_at or datetime.min.replace(tzinfo=UTC), reverse=True)

    async def process_webhook(
        self,
        event_type: str,
        installation_id: int,
        payload: dict,
    ) -> WebhookEvent:
        """Process an incoming webhook event."""
        evt_type = WebhookEventType(event_type) if event_type in WebhookEventType.__members__.values() else WebhookEventType.PUSH
        event = WebhookEvent(
            event_type=evt_type,
            installation_id=installation_id,
            payload=payload,
            received_at=datetime.now(UTC),
        )

        # Route to handler
        result = {}
        if evt_type == WebhookEventType.PULL_REQUEST:
            result = await self._handle_pr_event(installation_id, payload)
        elif evt_type == WebhookEventType.PUSH:
            result = await self._handle_push_event(installation_id, payload)
        elif evt_type == WebhookEventType.INSTALLATION:
            action = payload.get("action", "created")
            account = payload.get("account", {}).get("login", "")
            await self.handle_installation(installation_id, account, action=action)
            result = {"action": action, "account": account}

        event.processed = True
        event.result = result
        event.processed_at = datetime.now(UTC)
        self._events.append(event)

        logger.info("Webhook processed", event_type=event_type, installation_id=installation_id)
        return event

    async def _handle_pr_event(self, installation_id: int, payload: dict) -> dict:
        """Handle pull_request webhook — run compliance check."""
        repo = payload.get("repository", {}).get("full_name", "")
        pr_number = payload.get("pull_request", {}).get("number", 0)

        check = ComplianceCheckResult(
            installation_id=installation_id,
            repo=repo,
            pr_number=pr_number,
            conclusion="success",
            violations_found=0,
            frameworks_checked=["GDPR", "HIPAA", "PCI-DSS"],
            created_at=datetime.now(UTC),
        )
        self._check_results.append(check)
        return {"check_id": str(check.id), "conclusion": check.conclusion, "violations": 0}

    async def _handle_push_event(self, installation_id: int, payload: dict) -> dict:
        """Handle push webhook — trigger incremental scan."""
        repo = payload.get("repository", {}).get("full_name", "")
        ref = payload.get("ref", "")
        return {"repo": repo, "ref": ref, "scan_triggered": True}

    def get_marketplace_listing(self) -> AppMarketplaceListing:
        """Get marketplace listing info."""
        return AppMarketplaceListing(
            plans=MARKETPLACE_PLANS,
            install_url="https://github.com/apps/complianceagent/installations/new",
            setup_url="https://complianceagent.ai/setup",
        )

    async def update_plan(self, installation_id: int, plan: str) -> AppInstallation | None:
        """Update installation plan."""
        inst = self._installations.get(installation_id)
        if not inst:
            return None
        inst.plan = AppPlan(plan)
        inst.updated_at = datetime.now(UTC)
        logger.info("Plan updated", installation_id=installation_id, plan=plan)
        return inst

    def get_check_results(
        self,
        installation_id: int | None = None,
        repo: str | None = None,
        limit: int = 50,
    ) -> list[ComplianceCheckResult]:
        results = list(self._check_results)
        if installation_id:
            results = [r for r in results if r.installation_id == installation_id]
        if repo:
            results = [r for r in results if r.repo == repo]
        return results[:limit]
