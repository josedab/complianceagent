"""Webhook signature verification and GitHub App OAuth helpers."""

import hashlib
import hmac
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

import structlog


logger = structlog.get_logger()


class OAuthState(str, Enum):
    """OAuth flow state."""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class OAuthSession:
    """Tracks a GitHub App OAuth authorization flow."""

    state: str = ""
    code: str | None = None
    installation_id: int | None = None
    status: OAuthState = OAuthState.PENDING
    access_token: str | None = None
    token_expires_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# GitHub App manifest — defines the app's requested permissions and events
APP_MANIFEST = {
    "name": "ComplianceAgent",
    "url": "https://complianceagent.ai",
    "hook_attributes": {"url": "https://api.complianceagent.ai/api/v1/marketplace-app/webhook"},
    "redirect_url": "https://complianceagent.ai/auth/callback",
    "callback_urls": ["https://complianceagent.ai/auth/callback"],
    "setup_url": "https://complianceagent.ai/setup",
    "description": "Autonomous regulatory compliance scanning for your codebase",
    "public": True,
    "default_events": [
        "pull_request",
        "push",
        "check_run",
        "check_suite",
        "installation",
        "installation_repositories",
    ],
    "default_permissions": {
        "checks": "write",
        "pull_requests": "write",
        "contents": "read",
        "metadata": "read",
        "statuses": "write",
    },
}


def verify_webhook_signature(
    payload_body: bytes,
    signature_header: str,
    webhook_secret: str,
) -> bool:
    """Verify GitHub webhook HMAC-SHA256 signature.

    GitHub sends the signature in the ``X-Hub-Signature-256`` header as
    ``sha256=<hex-digest>``.
    """
    if not signature_header or not signature_header.startswith("sha256="):
        logger.warning("Missing or malformed webhook signature header")
        return False

    expected_sig = signature_header.removeprefix("sha256=")
    computed = hmac.new(
        webhook_secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    is_valid = hmac.compare_digest(computed, expected_sig)
    if not is_valid:
        logger.warning("Webhook signature verification failed")
    return is_valid


def generate_installation_token_request(
    app_id: str,
    private_key_pem: str,
    installation_id: int,
) -> dict:
    """Build a JWT for GitHub App authentication.

    Returns the headers and URL needed to request an installation
    access token via ``POST /app/installations/{id}/access_tokens``.
    """
    import jwt  # type: ignore[import-untyped]

    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + (10 * 60),
        "iss": app_id,
    }

    encoded = jwt.encode(payload, private_key_pem, algorithm="RS256")

    return {
        "url": f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        "headers": {
            "Authorization": f"Bearer {encoded}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    }
