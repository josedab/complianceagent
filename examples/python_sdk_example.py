"""
ComplianceAgent Python SDK Example

This example demonstrates how to interact with the ComplianceAgent API
using Python. It covers common workflows including:
- Authentication
- Creating and managing regulations
- Monitoring repository compliance
- Processing compliance fixes

Prerequisites:
    pip install httpx python-dotenv

Environment:
    Set COMPLIANCEAGENT_API_URL and COMPLIANCEAGENT_API_KEY in your environment
    or create a .env file.
"""

import asyncio
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


class ComplianceAgentClient:
    """A simple client for the ComplianceAgent API."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
    ):
        self.base_url = (
            base_url or os.getenv("COMPLIANCEAGENT_API_URL", "http://localhost:8000")
        ).rstrip("/")
        self.api_key = api_key or os.getenv("COMPLIANCEAGENT_API_KEY", "")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(self.timeout),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def _request(
        self, method: str, path: str, **kwargs
    ) -> dict[str, Any]:
        """Make an API request with error handling."""
        if not self._client:
            msg = "Client not initialized. Use 'async with'."
            raise RuntimeError(msg)

        response = await self._client.request(method, f"/api/v1{path}", **kwargs)
        response.raise_for_status()
        return response.json()

    # -------------------------------------------------------------------------
    # Health & Status
    # -------------------------------------------------------------------------

    async def health_check(self) -> dict[str, Any]:
        """Check if the API is healthy."""
        response = await self._client.get("/health")
        response.raise_for_status()
        return response.json()

    # -------------------------------------------------------------------------
    # Regulations
    # -------------------------------------------------------------------------

    async def list_regulations(
        self, skip: int = 0, limit: int = 100
    ) -> list[dict[str, Any]]:
        """List all regulations."""
        return await self._request(
            "GET", "/regulations", params={"skip": skip, "limit": limit}
        )

    async def get_regulation(self, regulation_id: str) -> dict[str, Any]:
        """Get a specific regulation by ID."""
        return await self._request("GET", f"/regulations/{regulation_id}")

    async def create_regulation(
        self,
        name: str,
        description: str,
        source_url: str,
        jurisdiction: str = "US",
        industry: str | None = None,
        effective_date: str | None = None,
    ) -> dict[str, Any]:
        """Create a new regulation to monitor."""
        return await self._request(
            "POST",
            "/regulations",
            json={
                "name": name,
                "description": description,
                "source_url": source_url,
                "jurisdiction": jurisdiction,
                "industry": industry,
                "effective_date": effective_date,
            },
        )

    async def sync_regulation(self, regulation_id: str) -> dict[str, Any]:
        """Trigger a sync for a regulation to fetch latest changes."""
        return await self._request("POST", f"/regulations/{regulation_id}/sync")

    # -------------------------------------------------------------------------
    # Requirements
    # -------------------------------------------------------------------------

    async def list_requirements(
        self, regulation_id: str, skip: int = 0, limit: int = 100
    ) -> list[dict[str, Any]]:
        """List requirements for a regulation."""
        return await self._request(
            "GET",
            f"/regulations/{regulation_id}/requirements",
            params={"skip": skip, "limit": limit},
        )

    async def get_requirement(
        self, regulation_id: str, requirement_id: str
    ) -> dict[str, Any]:
        """Get a specific requirement."""
        return await self._request(
            "GET", f"/regulations/{regulation_id}/requirements/{requirement_id}"
        )

    # -------------------------------------------------------------------------
    # Repositories
    # -------------------------------------------------------------------------

    async def list_repositories(
        self, skip: int = 0, limit: int = 100
    ) -> list[dict[str, Any]]:
        """List monitored repositories."""
        return await self._request(
            "GET", "/repositories", params={"skip": skip, "limit": limit}
        )

    async def add_repository(
        self,
        url: str,
        name: str | None = None,
        branch: str = "main",
        scan_patterns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Add a repository to monitor for compliance."""
        return await self._request(
            "POST",
            "/repositories",
            json={
                "url": url,
                "name": name,
                "branch": branch,
                "scan_patterns": scan_patterns or ["**/*.py", "**/*.js", "**/*.ts"],
            },
        )

    async def scan_repository(self, repository_id: str) -> dict[str, Any]:
        """Trigger a compliance scan for a repository."""
        return await self._request("POST", f"/repositories/{repository_id}/scan")

    async def get_repository_status(self, repository_id: str) -> dict[str, Any]:
        """Get the compliance status of a repository."""
        return await self._request("GET", f"/repositories/{repository_id}/status")

    # -------------------------------------------------------------------------
    # Compliance Mappings
    # -------------------------------------------------------------------------

    async def list_mappings(
        self, repository_id: str | None = None, skip: int = 0, limit: int = 100
    ) -> list[dict[str, Any]]:
        """List compliance mappings (requirement to code mappings)."""
        params = {"skip": skip, "limit": limit}
        if repository_id:
            params["repository_id"] = repository_id
        return await self._request("GET", "/mappings", params=params)

    async def create_mapping(
        self,
        requirement_id: str,
        repository_id: str,
        file_path: str,
        code_snippet: str,
        confidence: float = 1.0,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Create a manual compliance mapping."""
        return await self._request(
            "POST",
            "/mappings",
            json={
                "requirement_id": requirement_id,
                "repository_id": repository_id,
                "file_path": file_path,
                "code_snippet": code_snippet,
                "confidence": confidence,
                "notes": notes,
            },
        )

    # -------------------------------------------------------------------------
    # Compliance Fixes
    # -------------------------------------------------------------------------

    async def list_fixes(
        self,
        repository_id: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List generated compliance fixes."""
        params = {"skip": skip, "limit": limit}
        if repository_id:
            params["repository_id"] = repository_id
        if status:
            params["status"] = status
        return await self._request("GET", "/fixes", params=params)

    async def generate_fix(
        self, mapping_id: str, auto_apply: bool = False
    ) -> dict[str, Any]:
        """Generate a compliance fix for a specific mapping."""
        return await self._request(
            "POST",
            "/fixes/generate",
            json={"mapping_id": mapping_id, "auto_apply": auto_apply},
        )

    async def apply_fix(self, fix_id: str) -> dict[str, Any]:
        """Apply a compliance fix (creates a PR)."""
        return await self._request("POST", f"/fixes/{fix_id}/apply")

    async def reject_fix(self, fix_id: str, reason: str) -> dict[str, Any]:
        """Reject a compliance fix with a reason."""
        return await self._request(
            "POST", f"/fixes/{fix_id}/reject", json={"reason": reason}
        )

    # -------------------------------------------------------------------------
    # Audit Trail
    # -------------------------------------------------------------------------

    async def list_audit_events(
        self,
        entity_type: str | None = None,
        entity_id: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List audit events for compliance tracking."""
        params = {"skip": skip, "limit": limit}
        if entity_type:
            params["entity_type"] = entity_type
        if entity_id:
            params["entity_id"] = entity_id
        return await self._request("GET", "/audit", params=params)

    # -------------------------------------------------------------------------
    # IDE Integration
    # -------------------------------------------------------------------------

    async def analyze_code(
        self,
        file_path: str,
        code: str,
        regulation_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Analyze code snippet for compliance (IDE integration)."""
        return await self._request(
            "POST",
            "/ide/analyze",
            json={
                "file_path": file_path,
                "code": code,
                "regulation_ids": regulation_ids,
            },
        )

    async def get_suggestions(
        self, file_path: str, code: str, cursor_position: int
    ) -> list[dict[str, Any]]:
        """Get compliance suggestions at cursor position (IDE integration)."""
        return await self._request(
            "POST",
            "/ide/suggest",
            json={
                "file_path": file_path,
                "code": code,
                "cursor_position": cursor_position,
            },
        )


# =============================================================================
# Example Usage
# =============================================================================


async def main():
    """Demonstrate common ComplianceAgent workflows."""

    print("=" * 60)
    print("ComplianceAgent Python SDK Example")
    print("=" * 60)

    async with ComplianceAgentClient() as client:
        # Health check
        print("\n[1] Health Check")
        try:
            health = await client.health_check()
            print(f"    Status: {health.get('status', 'unknown')}")
            print(f"    Version: {health.get('version', 'unknown')}")
        except httpx.HTTPError as e:
            print(f"    Error: {e}")
            print("    Make sure ComplianceAgent is running at the configured URL.")
            return

        # List regulations
        print("\n[2] List Regulations")
        try:
            regulations = await client.list_regulations(limit=5)
            if regulations:
                for reg in regulations:
                    print(f"    - {reg.get('name')} ({reg.get('jurisdiction')})")
            else:
                print("    No regulations found. Create one first!")
        except httpx.HTTPError as e:
            print(f"    Error: {e}")

        # List repositories
        print("\n[3] List Monitored Repositories")
        try:
            repos = await client.list_repositories(limit=5)
            if repos:
                for repo in repos:
                    print(f"    - {repo.get('name')} ({repo.get('url')})")
            else:
                print("    No repositories monitored. Add one first!")
        except httpx.HTTPError as e:
            print(f"    Error: {e}")

        # Example: Create a regulation (commented out to avoid side effects)
        print("\n[4] Create Regulation (example - uncomment to run)")
        print("""
    regulation = await client.create_regulation(
        name="GDPR Article 17 - Right to Erasure",
        description="Users have the right to have personal data erased",
        source_url="https://gdpr-info.eu/art-17-gdpr/",
        jurisdiction="EU",
        industry="Technology",
    )
    print(f"Created: {regulation['id']}")
""")

        # Example: Add a repository (commented out)
        print("\n[5] Add Repository (example - uncomment to run)")
        print("""
    repo = await client.add_repository(
        url="https://github.com/myorg/myapp",
        name="myapp",
        branch="main",
        scan_patterns=["**/*.py", "**/*.js"],
    )
    print(f"Added: {repo['id']}")
""")

        # Example: Scan repository and generate fixes
        print("\n[6] Compliance Workflow (example - uncomment to run)")
        print("""
    # Scan a repository
    scan_result = await client.scan_repository(repository_id)
    print(f"Scan started: {scan_result['task_id']}")

    # Wait for scan to complete and check mappings
    mappings = await client.list_mappings(repository_id=repository_id)
    for mapping in mappings:
        if mapping['compliance_status'] == 'non_compliant':
            # Generate a fix
            fix = await client.generate_fix(mapping['id'])
            print(f"Fix generated: {fix['id']}")

            # Review and apply the fix
            await client.apply_fix(fix['id'])
            print(f"Fix applied: PR created")
""")

        print("\n" + "=" * 60)
        print("Example complete!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
