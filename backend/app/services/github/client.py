"""GitHub integration for repository access and PR creation."""

import base64
from dataclasses import dataclass
from typing import Any

import httpx
import structlog


logger = structlog.get_logger()


@dataclass
class GitHubFile:
    """A file from GitHub."""
    path: str
    content: str
    sha: str
    size: int
    encoding: str = "base64"


@dataclass
class GitHubPR:
    """A GitHub pull request."""
    number: int
    url: str
    html_url: str
    state: str
    title: str
    body: str
    head_sha: str
    base_branch: str
    head_branch: str


class GitHubClient:
    """Client for GitHub API."""

    def __init__(
        self,
        access_token: str | None = None,
        base_url: str = "https://api.github.com",
    ):
        self.access_token = access_token
        self.base_url = base_url
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=30.0,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        """Get repository information."""
        response = await self._client.get(f"/repos/{owner}/{repo}")
        response.raise_for_status()
        return response.json()

    async def get_repository_tree(
        self,
        owner: str,
        repo: str,
        tree_sha: str = "HEAD",
        recursive: bool = True,
    ) -> list[dict[str, Any]]:
        """Get repository file tree."""
        params = {"recursive": "1"} if recursive else {}
        response = await self._client.get(
            f"/repos/{owner}/{repo}/git/trees/{tree_sha}",
            params=params,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("tree", [])

    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str = "HEAD",
    ) -> GitHubFile:
        """Get file content from repository."""
        response = await self._client.get(
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": ref},
        )
        response.raise_for_status()
        data = response.json()

        content = ""
        if data.get("encoding") == "base64" and data.get("content"):
            content = base64.b64decode(data["content"]).decode("utf-8")

        return GitHubFile(
            path=data["path"],
            content=content,
            sha=data["sha"],
            size=data["size"],
            encoding=data.get("encoding", "base64"),
        )

    async def get_directory_contents(
        self,
        owner: str,
        repo: str,
        path: str = "",
        ref: str = "HEAD",
    ) -> list[dict[str, Any]]:
        """Get directory contents."""
        response = await self._client.get(
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": ref},
        )
        response.raise_for_status()
        return response.json()

    async def create_branch(
        self,
        owner: str,
        repo: str,
        branch_name: str,
        from_sha: str,
    ) -> dict[str, Any]:
        """Create a new branch."""
        response = await self._client.post(
            f"/repos/{owner}/{repo}/git/refs",
            json={
                "ref": f"refs/heads/{branch_name}",
                "sha": from_sha,
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_default_branch_sha(self, owner: str, repo: str) -> str:
        """Get SHA of default branch."""
        repo_info = await self.get_repository(owner, repo)
        default_branch = repo_info["default_branch"]

        response = await self._client.get(
            f"/repos/{owner}/{repo}/git/ref/heads/{default_branch}"
        )
        response.raise_for_status()
        return response.json()["object"]["sha"]

    async def create_or_update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str,
        sha: str | None = None,
    ) -> dict[str, Any]:
        """Create or update a file."""
        payload = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha

        response = await self._client.put(
            f"/repos/{owner}/{repo}/contents/{path}",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str,
        draft: bool = False,
    ) -> GitHubPR:
        """Create a pull request."""
        response = await self._client.post(
            f"/repos/{owner}/{repo}/pulls",
            json={
                "title": title,
                "body": body,
                "head": head,
                "base": base,
                "draft": draft,
            },
        )
        response.raise_for_status()
        data = response.json()

        return GitHubPR(
            number=data["number"],
            url=data["url"],
            html_url=data["html_url"],
            state=data["state"],
            title=data["title"],
            body=data["body"],
            head_sha=data["head"]["sha"],
            base_branch=data["base"]["ref"],
            head_branch=data["head"]["ref"],
        )

    async def add_labels_to_pr(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        labels: list[str],
    ) -> list[dict[str, Any]]:
        """Add labels to a pull request."""
        response = await self._client.post(
            f"/repos/{owner}/{repo}/issues/{pr_number}/labels",
            json={"labels": labels},
        )
        response.raise_for_status()
        return response.json()

    async def get_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> GitHubPR:
        """Get pull request details."""
        response = await self._client.get(
            f"/repos/{owner}/{repo}/pulls/{pr_number}"
        )
        response.raise_for_status()
        data = response.json()

        return GitHubPR(
            number=data["number"],
            url=data["url"],
            html_url=data["html_url"],
            state=data["state"],
            title=data["title"],
            body=data["body"],
            head_sha=data["head"]["sha"],
            base_branch=data["base"]["ref"],
            head_branch=data["head"]["ref"],
        )

    async def search_code(
        self,
        query: str,
        owner: str | None = None,
        repo: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search code in repositories."""
        q = query
        if owner and repo:
            q += f" repo:{owner}/{repo}"
        elif owner:
            q += f" user:{owner}"

        response = await self._client.get(
            "/search/code",
            params={"q": q, "per_page": 100},
        )
        response.raise_for_status()
        return response.json().get("items", [])


class GitHubAppClient(GitHubClient):
    """Client for GitHub App installations."""

    def __init__(
        self,
        app_id: str,
        private_key: str,
        installation_id: str,
    ):
        super().__init__()
        self.app_id = app_id
        self.private_key = private_key
        self.installation_id = installation_id
        self._installation_token: str | None = None

    async def _get_installation_token(self) -> str:
        """Get installation access token."""
        # In production, would use JWT to authenticate as the app
        # and exchange for an installation token
        return self._installation_token or ""

    async def __aenter__(self):
        self.access_token = await self._get_installation_token()
        return await super().__aenter__()


async def get_github_client(access_token: str) -> GitHubClient:
    """Create a GitHub client with the given token."""
    return GitHubClient(access_token=access_token)
