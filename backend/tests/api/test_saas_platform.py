"""Tests for SaaS Platform API endpoints."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestSaaSPlatformAPI:
    """Test SaaS Platform API endpoints."""

    async def test_provision_tenant(self, client: AsyncClient, auth_headers: dict):
        """Test provisioning a new tenant."""
        response = await client.post(
            "/api/v1/saas-platform/provision",
            headers=auth_headers,
            json={
                "name": "Acme Corp",
                "slug": "acme-corp",
                "plan": "starter",
                "owner_email": "admin@acme.com",
                "industry": "technology",
                "jurisdictions": ["US", "EU"],
                "github_org": "acme-corp",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "provisioned"
        assert data["tenant_id"]
        assert data["api_key"]
        assert len(data["onboarding_steps"]) > 0
        assert data["dashboard_url"]

    async def test_provision_tenant_default_plan(self, client: AsyncClient, auth_headers: dict):
        """Test provisioning with default free plan."""
        response = await client.post(
            "/api/v1/saas-platform/provision",
            headers=auth_headers,
            json={
                "name": "Free Org",
                "slug": "free-org",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "provisioned"

    async def test_get_tenant(self, client: AsyncClient, auth_headers: dict):
        """Test getting tenant details."""
        # First provision a tenant
        provision_response = await client.post(
            "/api/v1/saas-platform/provision",
            headers=auth_headers,
            json={
                "name": "Test Tenant",
                "slug": "test-tenant-get",
                "plan": "professional",
            },
        )
        assert provision_response.status_code == 201
        tenant_id = provision_response.json()["tenant_id"]

        # Get tenant details
        response = await client.get(
            f"/api/v1/saas-platform/{tenant_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Tenant"
        assert data["slug"] == "test-tenant-get"
        assert data["plan"] == "professional"
        assert data["status"] == "trial"

    async def test_get_tenant_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting non-existent tenant."""
        response = await client.get(
            "/api/v1/saas-platform/00000000-0000-0000-0000-000000000099",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_update_tenant_plan(self, client: AsyncClient, auth_headers: dict):
        """Test updating tenant plan."""
        # Provision a tenant
        provision_response = await client.post(
            "/api/v1/saas-platform/provision",
            headers=auth_headers,
            json={
                "name": "Upgrade Org",
                "slug": "upgrade-org",
                "plan": "free",
            },
        )
        assert provision_response.status_code == 201
        tenant_id = provision_response.json()["tenant_id"]

        # Update plan
        response = await client.put(
            f"/api/v1/saas-platform/{tenant_id}/plan",
            headers=auth_headers,
            json={"plan": "professional"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "professional"
        assert data["status"] == "active"

    async def test_update_tenant_plan_invalid(self, client: AsyncClient, auth_headers: dict):
        """Test updating to invalid plan."""
        # Provision a tenant
        provision_response = await client.post(
            "/api/v1/saas-platform/provision",
            headers=auth_headers,
            json={
                "name": "Bad Plan Org",
                "slug": "bad-plan-org",
            },
        )
        assert provision_response.status_code == 201
        tenant_id = provision_response.json()["tenant_id"]

        response = await client.put(
            f"/api/v1/saas-platform/{tenant_id}/plan",
            headers=auth_headers,
            json={"plan": "invalid_plan"},
        )

        assert response.status_code == 400

    async def test_suspend_tenant(self, client: AsyncClient, auth_headers: dict):
        """Test suspending a tenant."""
        # Provision a tenant
        provision_response = await client.post(
            "/api/v1/saas-platform/provision",
            headers=auth_headers,
            json={
                "name": "Suspend Org",
                "slug": "suspend-org",
            },
        )
        assert provision_response.status_code == 201
        tenant_id = provision_response.json()["tenant_id"]

        # Suspend
        response = await client.post(
            f"/api/v1/saas-platform/{tenant_id}/suspend",
            headers=auth_headers,
            json={"reason": "Non-payment"},
        )

        assert response.status_code == 204

        # Verify suspended
        get_response = await client.get(
            f"/api/v1/saas-platform/{tenant_id}",
            headers=auth_headers,
        )
        assert get_response.json()["status"] == "suspended"

    async def test_get_onboarding_status(self, client: AsyncClient, auth_headers: dict):
        """Test getting onboarding status."""
        # Provision a tenant
        provision_response = await client.post(
            "/api/v1/saas-platform/provision",
            headers=auth_headers,
            json={
                "name": "Onboard Org",
                "slug": "onboard-org",
            },
        )
        assert provision_response.status_code == 201
        tenant_id = provision_response.json()["tenant_id"]

        # Get onboarding
        response = await client.get(
            f"/api/v1/saas-platform/{tenant_id}/onboarding",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["status"] == "pending"

    async def test_complete_onboarding_step(self, client: AsyncClient, auth_headers: dict):
        """Test completing an onboarding step."""
        # Provision a tenant
        provision_response = await client.post(
            "/api/v1/saas-platform/provision",
            headers=auth_headers,
            json={
                "name": "Step Org",
                "slug": "step-org",
            },
        )
        assert provision_response.status_code == 201
        tenant_id = provision_response.json()["tenant_id"]

        # Complete a step
        response = await client.post(
            f"/api/v1/saas-platform/{tenant_id}/onboarding/connect-github/complete",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "connect-github"
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    async def test_complete_onboarding_step_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test completing non-existent onboarding step."""
        # Provision a tenant
        provision_response = await client.post(
            "/api/v1/saas-platform/provision",
            headers=auth_headers,
            json={
                "name": "Bad Step Org",
                "slug": "bad-step-org",
            },
        )
        assert provision_response.status_code == 201
        tenant_id = provision_response.json()["tenant_id"]

        response = await client.post(
            f"/api/v1/saas-platform/{tenant_id}/onboarding/nonexistent/complete",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_get_usage_summary(self, client: AsyncClient, auth_headers: dict):
        """Test getting usage summary."""
        # Provision a tenant
        provision_response = await client.post(
            "/api/v1/saas-platform/provision",
            headers=auth_headers,
            json={
                "name": "Usage Org",
                "slug": "usage-org",
            },
        )
        assert provision_response.status_code == 201
        tenant_id = provision_response.json()["tenant_id"]

        # Get usage
        response = await client.get(
            f"/api/v1/saas-platform/{tenant_id}/usage",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == tenant_id
        assert data["period"] == "current"
        assert "api_calls" in data
        assert "scans_run" in data

    async def test_check_resource_limit(self, client: AsyncClient, auth_headers: dict):
        """Test checking resource limits."""
        # Provision a tenant
        provision_response = await client.post(
            "/api/v1/saas-platform/provision",
            headers=auth_headers,
            json={
                "name": "Limits Org",
                "slug": "limits-org",
                "plan": "starter",
            },
        )
        assert provision_response.status_code == 201
        tenant_id = provision_response.json()["tenant_id"]

        # Check limit
        response = await client.get(
            f"/api/v1/saas-platform/{tenant_id}/limits/check",
            headers=auth_headers,
            params={"resource": "scans"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resource"] == "scans"
        assert data["within_limits"] is True
