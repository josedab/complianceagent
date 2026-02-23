"""Multi-SCM Support Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.multi_scm.models import (
    PRStatus,
    SCMConnection,
    SCMConnectionStatus,
    SCMProvider,
    SCMSyncStatus,
    UnifiedPullRequest,
    UnifiedRepository,
    UnifiedWebhook,
)


logger = structlog.get_logger()


class MultiSCMService:
    """Unified SCM abstraction over GitHub, GitLab, Bitbucket, Azure DevOps."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._connections: dict[str, SCMConnection] = {}
        self._repositories: list[UnifiedRepository] = []
        self._pull_requests: list[UnifiedPullRequest] = []
        self._webhooks: list[UnifiedWebhook] = []

    async def connect_provider(
        self,
        provider: str,
        organization: str,
        base_url: str = "",
        config: dict | None = None,
    ) -> SCMConnection:
        """Connect to an SCM provider."""
        scm_provider = SCMProvider(provider)
        default_urls = {
            SCMProvider.GITHUB: "https://api.github.com",
            SCMProvider.GITLAB: "https://gitlab.com/api/v4",
            SCMProvider.BITBUCKET: "https://api.bitbucket.org/2.0",
            SCMProvider.AZURE_DEVOPS: "https://dev.azure.com",
        }

        conn = SCMConnection(
            provider=scm_provider,
            organization=organization,
            base_url=base_url or default_urls.get(scm_provider, ""),
            status=SCMConnectionStatus.CONNECTED,
            connected_at=datetime.now(UTC),
            config=config or {},
        )
        key = f"{provider}:{organization}"
        self._connections[key] = conn
        logger.info("SCM provider connected", provider=provider, org=organization)
        return conn

    async def disconnect_provider(self, provider: str, organization: str) -> bool:
        key = f"{provider}:{organization}"
        conn = self._connections.get(key)
        if not conn:
            return False
        conn.status = SCMConnectionStatus.DISCONNECTED
        return True

    def list_connections(self, provider: SCMProvider | None = None) -> list[SCMConnection]:
        conns = list(self._connections.values())
        if provider:
            conns = [c for c in conns if c.provider == provider]
        return conns

    async def sync_repositories(self, provider: str, organization: str) -> list[UnifiedRepository]:
        """Sync repositories from a connected provider."""
        key = f"{provider}:{organization}"
        conn = self._connections.get(key)
        if not conn or conn.status != SCMConnectionStatus.CONNECTED:
            return []

        # Simulated repo discovery
        repos = [
            UnifiedRepository(
                provider=SCMProvider(provider),
                provider_id=f"{organization}/repo-{i}",
                full_name=f"{organization}/repo-{i}",
                default_branch="main",
                url=f"{conn.base_url}/{organization}/repo-{i}",
                language="Python" if i % 2 == 0 else "TypeScript",
            )
            for i in range(1, 4)
        ]
        self._repositories.extend(repos)
        conn.repositories_synced = len(repos)
        conn.last_sync_at = datetime.now(UTC)
        logger.info("Repositories synced", provider=provider, count=len(repos))
        return repos

    def list_repositories(
        self,
        provider: SCMProvider | None = None,
        limit: int = 50,
    ) -> list[UnifiedRepository]:
        repos = list(self._repositories)
        if provider:
            repos = [r for r in repos if r.provider == provider]
        return repos[:limit]

    async def create_compliance_pr(
        self,
        provider: str,
        repo_full_name: str,
        title: str,
        source_branch: str,
        target_branch: str = "main",
        fixes: list[dict] | None = None,
    ) -> UnifiedPullRequest:
        """Create a compliance fix PR across any SCM provider."""
        pr = UnifiedPullRequest(
            provider=SCMProvider(provider),
            provider_id=f"pr-{len(self._pull_requests) + 1}",
            repo_full_name=repo_full_name,
            number=len(self._pull_requests) + 1,
            title=title,
            status=PRStatus.OPEN,
            source_branch=source_branch,
            target_branch=target_branch,
            compliance_check_status="running",
            url=f"https://{provider}.com/{repo_full_name}/pull/{len(self._pull_requests) + 1}",
            created_at=datetime.now(UTC),
        )
        self._pull_requests.append(pr)
        logger.info("Compliance PR created", provider=provider, repo=repo_full_name, pr=pr.number)
        return pr

    def list_pull_requests(
        self,
        provider: SCMProvider | None = None,
        repo: str | None = None,
        status: PRStatus | None = None,
        limit: int = 50,
    ) -> list[UnifiedPullRequest]:
        results = list(self._pull_requests)
        if provider:
            results = [p for p in results if p.provider == provider]
        if repo:
            results = [p for p in results if p.repo_full_name == repo]
        if status:
            results = [p for p in results if p.status == status]
        return results[:limit]

    async def process_webhook(
        self,
        provider: str,
        event_type: str,
        payload: dict,
    ) -> UnifiedWebhook:
        """Process webhook from any SCM provider."""
        repo = ""
        if provider == "github":
            repo = payload.get("repository", {}).get("full_name", "")
        elif provider == "gitlab":
            repo = payload.get("project", {}).get("path_with_namespace", "")
        elif provider == "bitbucket":
            repo = payload.get("repository", {}).get("full_name", "")

        webhook = UnifiedWebhook(
            provider=SCMProvider(provider),
            event_type=event_type,
            repo_full_name=repo,
            payload=payload,
            processed=True,
            received_at=datetime.now(UTC),
        )
        self._webhooks.append(webhook)
        logger.info("SCM webhook processed", provider=provider, event_type=event_type, repo=repo)
        return webhook

    def get_sync_status(self, provider: str | None = None) -> list[SCMSyncStatus]:
        statuses = []
        for conn in self._connections.values():
            if provider and conn.provider.value != provider:
                continue
            repos = [r for r in self._repositories if r.provider == conn.provider]
            prs = [p for p in self._pull_requests if p.provider == conn.provider]
            whs = [w for w in self._webhooks if w.provider == conn.provider]
            statuses.append(SCMSyncStatus(
                provider=conn.provider,
                total_repos=conn.repositories_synced,
                repos_scanned=len(repos),
                prs_analyzed=len(prs),
                webhooks_processed=len(whs),
                last_sync_at=conn.last_sync_at,
            ))
        return statuses
