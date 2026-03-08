"""Outgoing webhook delivery with HMAC signing and retry logic."""

import hashlib
import hmac
import json
from ipaddress import ip_address
from urllib.parse import urlparse

import httpx
import structlog


logger = structlog.get_logger(__name__)

_BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "[::1]"}
_MAX_RETRIES = 5
_TIMEOUT_SECONDS = 10


def _validate_url(url: str) -> bool:
    """Reject URLs targeting internal/metadata services (SSRF protection)."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host in _BLOCKED_HOSTS:
        return False
    try:
        addr = ip_address(host)
        if addr.is_private or addr.is_loopback or addr.is_link_local:
            return False
    except ValueError:
        pass  # Hostname, not IP — allow
    return parsed.scheme in ("http", "https")


def sign_payload(payload: bytes, secret: str) -> str:
    """Create HMAC-SHA256 signature for webhook payload."""
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def verify_signature(payload: bytes, secret: str, signature: str) -> bool:
    """Verify an incoming webhook signature."""
    expected = sign_payload(payload, secret)
    return hmac.compare_digest(expected, signature)


async def deliver(
    url: str,
    payload: dict,
    secret: str = "",
    headers: dict | None = None,
    timeout: int = _TIMEOUT_SECONDS,
) -> tuple[bool, int, str]:
    """Deliver a webhook payload to a URL.

    Returns (success, status_code, error_message).
    """
    if not _validate_url(url):
        return False, 0, "URL blocked by SSRF protection"

    body = json.dumps(payload, default=str).encode()
    request_headers = {"Content-Type": "application/json", **(headers or {})}

    if secret:
        sig = sign_payload(body, secret)
        request_headers["X-ComplianceAgent-Signature"] = f"sha256={sig}"

    request_headers["X-ComplianceAgent-Event"] = payload.get("event_type", "unknown")
    request_headers["X-ComplianceAgent-Delivery"] = payload.get("delivery_id", "")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, content=body, headers=request_headers, timeout=timeout
            )
        success = response.status_code < 400
        if not success:
            logger.warning(
                "webhook.delivery_failed",
                url=url,
                status=response.status_code,
                body=response.text[:200],
            )
        return success, response.status_code, "" if success else response.text[:200]
    except httpx.TimeoutException:
        return False, 0, "Request timed out"
    except Exception as exc:
        return False, 0, str(exc)[:200]


def backoff_seconds(retry: int) -> int:
    """Exponential backoff: 1, 2, 4, 8, 16 seconds."""
    return min(2**retry, 60)
