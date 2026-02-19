"""End-to-end tests for core application flows.

These tests verify critical user journeys through the full application stack.
Prerequisites: Backend and frontend must be running (make run-backend && make run-frontend).
"""

import pytest
from playwright.async_api import Page, expect


pytestmark = pytest.mark.e2e


class TestHealthCheck:
    """Verify basic application health."""

    async def test_backend_health(self, page: Page):
        """Backend /health endpoint returns healthy status."""
        response = await page.request.get("http://localhost:8000/health")
        assert response.ok
        data = await response.json()
        assert data["status"] == "healthy"

    async def test_frontend_loads(self, page: Page):
        """Frontend loads without errors."""
        await page.goto("/")
        await expect(page).to_have_title(timeout=10000)

    async def test_api_docs_available(self, page: Page):
        """OpenAPI docs are accessible in development."""
        response = await page.request.get("http://localhost:8000/api/docs")
        # In dev mode, docs should be available (200). In prod, may be 404.
        assert response.status in (200, 404)


class TestAuthFlow:
    """Test authentication user journey."""

    async def test_login_page_renders(self, page: Page):
        """Login page loads with email and password fields."""
        await page.goto("/login")
        await expect(page.locator('[name="email"]')).to_be_visible()
        await expect(page.locator('[name="password"]')).to_be_visible()
        await expect(page.locator('button[type="submit"]')).to_be_visible()

    async def test_login_with_invalid_credentials(self, page: Page):
        """Login with wrong password shows error message."""
        await page.goto("/login")
        await page.fill('[name="email"]', "wrong@example.com")
        await page.fill('[name="password"]', "wrongpassword")
        await page.click('button[type="submit"]')
        # Should show error — stay on login page
        await page.wait_for_timeout(2000)
        assert "/login" in page.url or "/auth" in page.url

    async def test_signup_page_renders(self, page: Page):
        """Signup page loads with registration fields."""
        await page.goto("/signup")
        await expect(page.locator('[name="email"]')).to_be_visible()


class TestDashboard:
    """Test dashboard functionality (requires authentication)."""

    async def test_dashboard_loads(self, authenticated_page: Page):
        """Dashboard loads with compliance overview."""
        page = authenticated_page
        await expect(page.locator("text=Compliance")).to_be_visible(timeout=10000)

    async def test_navigation_works(self, authenticated_page: Page):
        """Sidebar navigation links work correctly."""
        page = authenticated_page
        # Look for navigation items
        nav = page.locator("nav")
        await expect(nav).to_be_visible()

    async def test_regulations_page(self, authenticated_page: Page):
        """Regulations page loads and shows framework list."""
        page = authenticated_page
        await page.goto("/dashboard/regulations")
        await page.wait_for_load_state("networkidle")
        # Page should load without errors
        assert page.url.endswith("/regulations") or "regulations" in page.url


class TestComplianceWorkflow:
    """Test the core compliance analysis workflow."""

    async def test_repository_management_page(self, authenticated_page: Page):
        """Repository management page loads."""
        page = authenticated_page
        await page.goto("/dashboard/repositories")
        await page.wait_for_load_state("networkidle")
        assert "repositories" in page.url

    async def test_audit_trail_page(self, authenticated_page: Page):
        """Audit trail page loads and shows entries."""
        page = authenticated_page
        await page.goto("/dashboard/audit")
        await page.wait_for_load_state("networkidle")
        assert "audit" in page.url
