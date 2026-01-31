"""GitLab integration client for repository analysis."""

from dataclasses import dataclass
from typing import Any

import httpx
import structlog


logger = structlog.get_logger()


@dataclass
class GitLabFile:
    """Represents a file in a GitLab repository."""
    path: str
    name: str
    size: int
    type: str  # "blob" or "tree"
    mode: str


@dataclass
class GitLabRepository:
    """Represents a GitLab repository."""
    id: int
    name: str
    path: str
    full_path: str
    default_branch: str
    visibility: str
    description: str | None
    web_url: str
    ssh_url: str
    http_url: str
    languages: dict[str, float] | None = None


class GitLabClient:
    """Client for interacting with GitLab API."""

    def __init__(
        self,
        token: str | None = None,
        base_url: str = "https://gitlab.com",
    ):
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/v4"
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "GitLabClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            headers=self._get_headers(),
            timeout=httpx.Timeout(30.0),
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["PRIVATE-TOKEN"] = self.token
        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any] | list[Any]:
        """Make an API request."""
        if not self._client:
            msg = "Client not initialized. Use async with context manager."
            raise RuntimeError(msg)

        url = f"{self.api_url}{endpoint}"
        response = await self._client.request(method, url, **kwargs)

        if response.status_code == 404:
            msg = f"Resource not found: {endpoint}"
            raise ValueError(msg)
        if response.status_code == 401:
            msg = "Authentication failed. Check your GitLab token."
            raise ValueError(msg)
        if response.status_code >= 400:
            msg = f"API error {response.status_code}: {response.text}"
            raise ValueError(msg)

        return response.json()

    # Project endpoints
    async def get_project(self, project_id: str | int) -> GitLabRepository:
        """Get project details."""
        # URL-encode the project path if it's a string
        if isinstance(project_id, str):
            project_id = project_id.replace("/", "%2F")

        data = await self._request("GET", f"/projects/{project_id}")
        return GitLabRepository(
            id=data["id"],
            name=data["name"],
            path=data["path"],
            full_path=data["path_with_namespace"],
            default_branch=data.get("default_branch", "main"),
            visibility=data["visibility"],
            description=data.get("description"),
            web_url=data["web_url"],
            ssh_url=data["ssh_url_to_repo"],
            http_url=data["http_url_to_repo"],
        )

    async def get_project_languages(self, project_id: str | int) -> dict[str, float]:
        """Get programming languages used in project."""
        if isinstance(project_id, str):
            project_id = project_id.replace("/", "%2F")

        return await self._request("GET", f"/projects/{project_id}/languages")

    async def list_user_projects(
        self,
        page: int = 1,
        per_page: int = 20,
        membership: bool = True,
    ) -> list[GitLabRepository]:
        """List projects accessible to authenticated user."""
        params = {
            "page": page,
            "per_page": per_page,
            "membership": str(membership).lower(),
        }
        data = await self._request("GET", "/projects", params=params)

        return [
            GitLabRepository(
                id=p["id"],
                name=p["name"],
                path=p["path"],
                full_path=p["path_with_namespace"],
                default_branch=p.get("default_branch", "main"),
                visibility=p["visibility"],
                description=p.get("description"),
                web_url=p["web_url"],
                ssh_url=p["ssh_url_to_repo"],
                http_url=p["http_url_to_repo"],
            )
            for p in data
        ]

    # Repository files endpoints
    async def get_repository_tree(
        self,
        project_id: str | int,
        path: str = "",
        ref: str | None = None,
        recursive: bool = False,
        per_page: int = 100,
    ) -> list[GitLabFile]:
        """Get repository file tree."""
        if isinstance(project_id, str):
            project_id = project_id.replace("/", "%2F")

        params: dict[str, Any] = {
            "per_page": per_page,
            "recursive": str(recursive).lower(),
        }
        if path:
            params["path"] = path
        if ref:
            params["ref"] = ref

        data = await self._request(
            "GET",
            f"/projects/{project_id}/repository/tree",
            params=params,
        )

        return [
            GitLabFile(
                path=f["path"],
                name=f["name"],
                size=0,  # GitLab tree doesn't include size
                type=f["type"],
                mode=f["mode"],
            )
            for f in data
        ]

    async def get_file_content(
        self,
        project_id: str | int,
        file_path: str,
        ref: str | None = None,
    ) -> str:
        """Get file content."""
        if isinstance(project_id, str):
            project_id = project_id.replace("/", "%2F")

        encoded_path = file_path.replace("/", "%2F")
        params = {}
        if ref:
            params["ref"] = ref

        data = await self._request(
            "GET",
            f"/projects/{project_id}/repository/files/{encoded_path}",
            params=params,
        )

        import base64
        return base64.b64decode(data["content"]).decode("utf-8")

    async def get_file_blame(
        self,
        project_id: str | int,
        file_path: str,
        ref: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get file blame information."""
        if isinstance(project_id, str):
            project_id = project_id.replace("/", "%2F")

        encoded_path = file_path.replace("/", "%2F")
        params = {}
        if ref:
            params["ref"] = ref

        return await self._request(
            "GET",
            f"/projects/{project_id}/repository/files/{encoded_path}/blame",
            params=params,
        )

    # Branch endpoints
    async def list_branches(
        self,
        project_id: str | int,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        """List repository branches."""
        if isinstance(project_id, str):
            project_id = project_id.replace("/", "%2F")

        params = {}
        if search:
            params["search"] = search

        return await self._request(
            "GET",
            f"/projects/{project_id}/repository/branches",
            params=params,
        )

    async def get_branch(
        self,
        project_id: str | int,
        branch: str,
    ) -> dict[str, Any]:
        """Get branch details."""
        if isinstance(project_id, str):
            project_id = project_id.replace("/", "%2F")

        return await self._request(
            "GET",
            f"/projects/{project_id}/repository/branches/{branch}",
        )

    # Commit endpoints
    async def list_commits(
        self,
        project_id: str | int,
        ref_name: str | None = None,
        path: str | None = None,
        per_page: int = 20,
    ) -> list[dict[str, Any]]:
        """List repository commits."""
        if isinstance(project_id, str):
            project_id = project_id.replace("/", "%2F")

        params: dict[str, Any] = {"per_page": per_page}
        if ref_name:
            params["ref_name"] = ref_name
        if path:
            params["path"] = path

        return await self._request(
            "GET",
            f"/projects/{project_id}/repository/commits",
            params=params,
        )

    async def get_commit(
        self,
        project_id: str | int,
        sha: str,
    ) -> dict[str, Any]:
        """Get commit details."""
        if isinstance(project_id, str):
            project_id = project_id.replace("/", "%2F")

        return await self._request(
            "GET",
            f"/projects/{project_id}/repository/commits/{sha}",
        )

    async def get_commit_diff(
        self,
        project_id: str | int,
        sha: str,
    ) -> list[dict[str, Any]]:
        """Get commit diff."""
        if isinstance(project_id, str):
            project_id = project_id.replace("/", "%2F")

        return await self._request(
            "GET",
            f"/projects/{project_id}/repository/commits/{sha}/diff",
        )

    # Merge Request endpoints
    async def list_merge_requests(
        self,
        project_id: str | int,
        state: str = "opened",
        per_page: int = 20,
    ) -> list[dict[str, Any]]:
        """List merge requests."""
        if isinstance(project_id, str):
            project_id = project_id.replace("/", "%2F")

        return await self._request(
            "GET",
            f"/projects/{project_id}/merge_requests",
            params={"state": state, "per_page": per_page},
        )

    async def create_merge_request(
        self,
        project_id: str | int,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str | None = None,
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a merge request."""
        if isinstance(project_id, str):
            project_id = project_id.replace("/", "%2F")

        payload: dict[str, Any] = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
        }
        if description:
            payload["description"] = description
        if labels:
            payload["labels"] = ",".join(labels)

        return await self._request(
            "POST",
            f"/projects/{project_id}/merge_requests",
            json=payload,
        )

    async def get_merge_request(
        self,
        project_id: str | int,
        mr_iid: int,
    ) -> dict[str, Any]:
        """Get merge request details."""
        if isinstance(project_id, str):
            project_id = project_id.replace("/", "%2F")

        return await self._request(
            "GET",
            f"/projects/{project_id}/merge_requests/{mr_iid}",
        )

    async def get_merge_request_changes(
        self,
        project_id: str | int,
        mr_iid: int,
    ) -> dict[str, Any]:
        """Get merge request changes/diff."""
        if isinstance(project_id, str):
            project_id = project_id.replace("/", "%2F")

        return await self._request(
            "GET",
            f"/projects/{project_id}/merge_requests/{mr_iid}/changes",
        )

    # Webhook endpoints
    async def list_webhooks(self, project_id: str | int) -> list[dict[str, Any]]:
        """List project webhooks."""
        if isinstance(project_id, str):
            project_id = project_id.replace("/", "%2F")

        return await self._request("GET", f"/projects/{project_id}/hooks")

    async def create_webhook(
        self,
        project_id: str | int,
        url: str,
        push_events: bool = True,
        merge_requests_events: bool = True,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Create a webhook for the project."""
        if isinstance(project_id, str):
            project_id = project_id.replace("/", "%2F")

        payload: dict[str, Any] = {
            "url": url,
            "push_events": push_events,
            "merge_requests_events": merge_requests_events,
        }
        if token:
            payload["token"] = token

        return await self._request(
            "POST",
            f"/projects/{project_id}/hooks",
            json=payload,
        )

    async def delete_webhook(
        self,
        project_id: str | int,
        hook_id: int,
    ) -> None:
        """Delete a webhook."""
        if isinstance(project_id, str):
            project_id = project_id.replace("/", "%2F")

        await self._request("DELETE", f"/projects/{project_id}/hooks/{hook_id}")
