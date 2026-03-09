"""Tests for authentication API."""

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestAuthAPI:
    """Test suite for authentication endpoints."""

    async def test_register_user(self, client: AsyncClient):
        """Test user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User",
            },
        )
        # Registration should create user successfully
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"

    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with existing email fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,  # Already exists
                "password": "securepassword123",
                "full_name": "Duplicate User",
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
            },
        )
        # Accept 429 (rate-limiting) alongside 401 for invalid credentials
        assert response.status_code in (401, 429)

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without auth."""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    async def test_expired_token_rejected(self, client: AsyncClient):
        """Test that an expired access token returns 401."""
        from datetime import timedelta

        from app.core.security import create_access_token

        expired_token = create_access_token(
            subject="user-123",
            expires_delta=timedelta(seconds=-1),
        )
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401

    async def test_malformed_token_rejected(self, client: AsyncClient):
        """Test that a malformed JWT returns 401."""
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer not.a.valid.jwt.token"},
        )
        assert response.status_code == 401

    async def test_missing_bearer_prefix_rejected(self, client: AsyncClient):
        """Test that auth header without Bearer prefix is rejected."""
        from app.core.security import create_access_token

        token = create_access_token(subject="user-123")
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": token},
        )
        # Should fail with 401 or 422
        assert response.status_code in (401, 422)
