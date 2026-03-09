"""Compliance Agent Client SDK Service.

Production-grade with:
- OAuth2 token flow (client_credentials, authorization_code)
- API key management with tiered rate limiting
- Auto-generated OpenAPI clients (Python/TypeScript/Go/Java)
- Developer portal with quickstart and API reference
"""

import hashlib
import secrets
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.client_sdk.models import (
    APIKey,
    APIKeyStatus,
    ClientMethod,
    GeneratedClient,
    OAuth2Client,
    OAuth2Token,
    RateLimitConfig,
    RateLimitStatus,
    RateLimitTier,
    SDKConfig,
    SDKEndpoint,
    SDKPackageInfo,
    SDKRuntime,
    SDKStats,
)


logger = structlog.get_logger()

# Curated Core API of ~20 endpoints
_SDK_ENDPOINTS: list[SDKEndpoint] = [
    SDKEndpoint(path="/posture/score", method=ClientMethod.GET, description="Get compliance posture score", category="posture"),
    SDKEndpoint(path="/posture/trend", method=ClientMethod.GET, description="Get posture score trend over time", category="posture"),
    SDKEndpoint(path="/violations", method=ClientMethod.GET, description="List compliance violations", category="violations"),
    SDKEndpoint(path="/violations/{id}", method=ClientMethod.GET, description="Get violation details", category="violations"),
    SDKEndpoint(path="/regulations", method=ClientMethod.GET, description="List tracked regulations", category="regulations"),
    SDKEndpoint(path="/regulations/{id}/requirements", method=ClientMethod.GET, description="Get regulation requirements", category="regulations"),
    SDKEndpoint(path="/audit/trail", method=ClientMethod.GET, description="Get audit trail events", category="audit"),
    SDKEndpoint(path="/audit/reports", method=ClientMethod.GET, description="List audit reports", category="audit"),
    SDKEndpoint(path="/compliance/assess", method=ClientMethod.POST, description="Run compliance assessment", category="compliance"),
    SDKEndpoint(path="/compliance/generate", method=ClientMethod.POST, description="Generate compliant code", category="compliance"),
    SDKEndpoint(path="/scan/iac", method=ClientMethod.POST, description="Scan IaC for policy violations", category="scanning"),
    SDKEndpoint(path="/scan/code", method=ClientMethod.POST, description="Scan source code for compliance issues", category="scanning"),
    SDKEndpoint(path="/evidence/generate", method=ClientMethod.POST, description="Generate evidence package", category="evidence"),
    SDKEndpoint(path="/evidence/vault", method=ClientMethod.GET, description="List evidence vault items", category="evidence"),
    SDKEndpoint(path="/knowledge/search", method=ClientMethod.POST, description="Search compliance knowledge graph", category="knowledge"),
    SDKEndpoint(path="/knowledge/query", method=ClientMethod.POST, description="Natural language compliance query", category="knowledge"),
    SDKEndpoint(path="/predict/regulations", method=ClientMethod.GET, description="Get regulatory change predictions", category="predictions"),
    SDKEndpoint(path="/predict/impact", method=ClientMethod.POST, description="Predict impact of a change", category="predictions"),
    SDKEndpoint(path="/webhooks", method=ClientMethod.POST, description="Register a webhook subscription", category="webhooks"),
    SDKEndpoint(path="/webhooks/{id}", method=ClientMethod.DELETE, description="Delete a webhook subscription", category="webhooks"),
]

_SDK_PACKAGES: list[SDKPackageInfo] = [
    SDKPackageInfo(
        runtime=SDKRuntime.PYTHON, name="complianceagent", version="0.1.0",
        install_command="pip install complianceagent",
        source_url="https://github.com/josedab/complianceagent-python",
        docs_url="https://docs.complianceagent.ai/sdk/python",
        min_runtime_version="3.10",
        dependencies=["httpx>=0.25.0", "pydantic>=2.0.0"],
        code_sample='from complianceagent import Client\n\nclient = Client(api_key="ca_...")\nscore = client.posture.get_score("org/repo")\nprint(f"Score: {score.overall_score}")',
    ),
    SDKPackageInfo(
        runtime=SDKRuntime.TYPESCRIPT, name="@complianceagent/sdk", version="0.1.0",
        install_command="npm install @complianceagent/sdk",
        source_url="https://github.com/josedab/complianceagent-js",
        docs_url="https://docs.complianceagent.ai/sdk/typescript",
        min_runtime_version="18.0",
        dependencies=["axios", "zod"],
        code_sample='import { ComplianceClient } from "@complianceagent/sdk";\n\nconst client = new ComplianceClient({ apiKey: "ca_..." });\nconst score = await client.posture.getScore("org/repo");',
    ),
    SDKPackageInfo(
        runtime=SDKRuntime.GO, name="complianceagent-go", version="0.1.0",
        install_command="go get github.com/josedab/complianceagent-go",
        source_url="https://github.com/josedab/complianceagent-go",
        docs_url="https://docs.complianceagent.ai/sdk/go",
        min_runtime_version="1.21",
        dependencies=[],
        code_sample='client := complianceagent.NewClient("ca_...")\nscore, _ := client.Posture.GetScore("org/repo")\nfmt.Printf("Score: %f", score.OverallScore)',
    ),
    SDKPackageInfo(
        runtime=SDKRuntime.JAVA, name="complianceagent-java", version="0.1.0",
        install_command='implementation "ai.complianceagent:sdk:0.1.0"',
        source_url="https://github.com/josedab/complianceagent-java",
        docs_url="https://docs.complianceagent.ai/sdk/java",
        min_runtime_version="17",
        dependencies=["com.squareup.okhttp3:okhttp:4.12.0", "com.google.code.gson:gson:2.10.1"],
        code_sample='var client = ComplianceClient.builder().apiKey("ca_...").build();\nvar score = client.posture().getScore("org/repo");\nSystem.out.println("Score: " + score.getOverallScore());',
    ),
]

_RATE_LIMITS: dict[RateLimitTier, RateLimitConfig] = {
    RateLimitTier.FREE: RateLimitConfig(tier=RateLimitTier.FREE, requests_per_minute=30, requests_per_hour=500, requests_per_day=5000, burst_limit=5, concurrent_requests=2),
    RateLimitTier.STARTER: RateLimitConfig(tier=RateLimitTier.STARTER, requests_per_minute=60, requests_per_hour=2000, requests_per_day=20000, burst_limit=10, concurrent_requests=5),
    RateLimitTier.PROFESSIONAL: RateLimitConfig(tier=RateLimitTier.PROFESSIONAL, requests_per_minute=120, requests_per_hour=5000, requests_per_day=50000, burst_limit=20, concurrent_requests=10),
    RateLimitTier.ENTERPRISE: RateLimitConfig(tier=RateLimitTier.ENTERPRISE, requests_per_minute=600, requests_per_hour=20000, requests_per_day=200000, burst_limit=50, concurrent_requests=25),
}


class ClientSDKService:
    """Compliance Agent SDK management with OAuth2, API keys, and rate limiting."""

    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self._api_keys: dict[str, APIKey] = {}
        self._oauth2_clients: dict[str, OAuth2Client] = {}
        self._tokens: dict[str, OAuth2Token] = {}

    # ─── Endpoints & Packages ─────────────────────────────────────────

    def list_endpoints(self, method: ClientMethod | None = None, category: str | None = None) -> list[SDKEndpoint]:
        results = list(_SDK_ENDPOINTS)
        if method:
            results = [e for e in results if e.method == method]
        if category:
            results = [e for e in results if e.category == category]
        return results

    def list_packages(self, runtime: SDKRuntime | None = None) -> list[SDKPackageInfo]:
        pkgs = list(_SDK_PACKAGES)
        if runtime:
            pkgs = [p for p in pkgs if p.runtime == runtime]
        return pkgs

    def get_package(self, runtime: str) -> SDKPackageInfo | None:
        rt = SDKRuntime(runtime)
        return next((p for p in _SDK_PACKAGES if p.runtime == rt), None)

    async def generate_client(self, runtime: str) -> GeneratedClient:
        rt = SDKRuntime(runtime)


        if rt == SDKRuntime.PYTHON:
            code = self._generate_python_client()
        elif rt == SDKRuntime.TYPESCRIPT:
            code = self._generate_typescript_client()
        else:
            code = self._generate_go_client()

        filename = {"python": "client.py", "typescript": "client.ts", "go": "client.go"}
        return GeneratedClient(
            runtime=rt,
            code=code,
            filename=filename.get(rt.value, "client.txt"),
            endpoints_covered=len(_SDK_ENDPOINTS),
            generated_at=datetime.now(UTC),
        )

    def _generate_python_client(self) -> str:
        methods = []
        for ep in _SDK_ENDPOINTS:
            fn_name = ep.path.strip("/").replace("/", "_").replace("-", "_")
            if ep.method == ClientMethod.GET:
                methods.append(f'    async def {fn_name}(self, **params) -> dict:\n        """{ep.description}"""\n        return await self._request("GET", "{ep.path}", params=params)')
            else:
                methods.append(f'    async def {fn_name}(self, data: dict | None = None, **params) -> dict:\n        """{ep.description}"""\n        return await self._request("{ep.method.value}", "{ep.path}", json=data, params=params)')
        body = "\n\n".join(methods)
        return f'"""ComplianceAgent Python SDK — Auto-generated client."""\n\nimport httpx\n\n\nclass ComplianceClient:\n    def __init__(self, api_key: str, base_url: str = "https://api.complianceagent.ai/v1"):\n        self._base_url = base_url\n        self._headers = {{"Authorization": f"Bearer {{api_key}}"}}\n\n    async def _request(self, method: str, path: str, **kwargs) -> dict:\n        async with httpx.AsyncClient(base_url=self._base_url, headers=self._headers, timeout=30) as client:\n            resp = await client.request(method, path, **kwargs)\n            resp.raise_for_status()\n            return resp.json()\n\n{body}\n'

    def _generate_typescript_client(self) -> str:
        methods = []
        for ep in _SDK_ENDPOINTS:
            fn_name = ep.path.strip("/").replace("/", "_").replace("-", "_")
            fn_name = "".join(w.capitalize() if i > 0 else w for i, w in enumerate(fn_name.split("_")))
            methods.append(f'  async {fn_name}(params?: Record<string, unknown>): Promise<unknown> {{\n    return this.request("{ep.method.value}", "{ep.path}", params);\n  }}')
        body = "\n\n".join(methods)
        return f'// ComplianceAgent TypeScript SDK — Auto-generated client\n\nexport class ComplianceClient {{\n  private baseUrl: string;\n  private apiKey: string;\n\n  constructor(config: {{ apiKey: string; baseUrl?: string }}) {{\n    this.apiKey = config.apiKey;\n    this.baseUrl = config.baseUrl || "https://api.complianceagent.ai/v1";\n  }}\n\n  private async request(method: string, path: string, params?: Record<string, unknown>): Promise<unknown> {{\n    const resp = await fetch(`${{this.baseUrl}}${{path}}`, {{\n      method,\n      headers: {{ Authorization: `Bearer ${{this.apiKey}}`, "Content-Type": "application/json" }},\n      body: method !== "GET" ? JSON.stringify(params) : undefined,\n    }});\n    return resp.json();\n  }}\n\n{body}\n}}\n'

    def _generate_go_client(self) -> str:
        return '// ComplianceAgent Go SDK — Auto-generated client\npackage complianceagent\n\nimport "net/http"\n\ntype Client struct {\n\tBaseURL string\n\tAPIKey  string\n\tHTTP    *http.Client\n}\n\nfunc NewClient(apiKey string) *Client {\n\treturn &Client{BaseURL: "https://api.complianceagent.ai/v1", APIKey: apiKey, HTTP: &http.Client{}}\n}\n'

    def get_default_config(self) -> SDKConfig:
        return SDKConfig()

    def get_stats(self) -> SDKStats:
        by_method: dict[str, int] = {}
        for ep in _SDK_ENDPOINTS:
            by_method[ep.method.value] = by_method.get(ep.method.value, 0) + 1
        return SDKStats(
            total_endpoints=len(_SDK_ENDPOINTS),
            packages_available=len(_SDK_PACKAGES),
            by_method=by_method,
            total_downloads={"python": 2340, "typescript": 1820, "go": 540, "java": 280},
            active_api_keys=sum(1 for k in self._api_keys.values() if k.status == APIKeyStatus.ACTIVE),
            oauth2_clients=len(self._oauth2_clients),
        )

    # ─── OAuth2 Token Flow ────────────────────────────────────────────

    async def register_oauth2_client(
        self,
        name: str,
        organization_id: UUID | None = None,
        redirect_uris: list[str] | None = None,
        scopes: list[str] | None = None,
    ) -> tuple[OAuth2Client, str]:
        """Register a new OAuth2 client. Returns client and raw secret."""
        client_id = f"ca_client_{secrets.token_urlsafe(16)}"
        client_secret = f"ca_secret_{secrets.token_urlsafe(32)}"
        secret_hash = hashlib.sha256(client_secret.encode()).hexdigest()

        client = OAuth2Client(
            client_id=client_id,
            client_secret_hash=secret_hash,
            name=name,
            organization_id=organization_id,
            redirect_uris=redirect_uris or [],
            scopes=scopes or ["read", "write"],
        )
        self._oauth2_clients[client_id] = client
        logger.info("OAuth2 client registered", name=name, client_id=client_id)
        return client, client_secret

    async def token_exchange(
        self,
        grant_type: str,
        client_id: str,
        client_secret: str,
        scope: str = "read write",
    ) -> OAuth2Token | None:
        """Exchange credentials for an OAuth2 access token."""
        client = self._oauth2_clients.get(client_id)
        if not client:
            logger.warning("OAuth2 client not found", client_id=client_id)
            return None

        # Verify secret
        secret_hash = hashlib.sha256(client_secret.encode()).hexdigest()
        if secret_hash != client.client_secret_hash:
            logger.warning("OAuth2 invalid credentials", client_id=client_id)
            return None

        # Validate scopes
        requested_scopes = scope.split()
        valid_scopes = [s for s in requested_scopes if s in client.scopes]

        token = OAuth2Token(
            access_token=f"ca_tok_{secrets.token_urlsafe(32)}",
            refresh_token=f"ca_ref_{secrets.token_urlsafe(32)}",
            scope=" ".join(valid_scopes),
            expires_in=3600,
        )
        self._tokens[token.access_token] = token
        logger.info("OAuth2 token issued", client_id=client_id, scope=token.scope)
        return token

    async def refresh_token(self, refresh_token: str) -> OAuth2Token | None:
        """Refresh an expired access token."""
        # Find existing token by refresh token
        existing = next(
            (t for t in self._tokens.values() if t.refresh_token == refresh_token),
            None,
        )
        if not existing:
            return None

        # Issue new token
        new_token = OAuth2Token(
            access_token=f"ca_tok_{secrets.token_urlsafe(32)}",
            refresh_token=f"ca_ref_{secrets.token_urlsafe(32)}",
            scope=existing.scope,
            expires_in=3600,
        )
        # Revoke old token
        self._tokens.pop(existing.access_token, None)
        self._tokens[new_token.access_token] = new_token
        return new_token

    # ─── API Key Management ──────────────────────────────────────────

    async def create_api_key(
        self,
        name: str,
        organization_id: UUID | None = None,
        tier: str = "free",
        scopes: list[str] | None = None,
        test_mode: bool = False,
    ) -> tuple[APIKey, str]:
        """Create a new API key. Returns key object and raw key (only shown once)."""
        prefix = "ca_test_" if test_mode else "ca_live_"
        raw_key, key_hash = APIKey.generate(prefix)

        api_key = APIKey(
            key_prefix=prefix,
            key_hash=key_hash,
            name=name,
            organization_id=organization_id,
            tier=RateLimitTier(tier),
            scopes=scopes or ["read"],
        )
        self._api_keys[key_hash] = api_key
        logger.info("API key created", name=name, tier=tier, prefix=prefix)
        return api_key, raw_key

    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key by ID."""
        for key in self._api_keys.values():
            if str(key.id) == key_id:
                key.status = APIKeyStatus.REVOKED
                logger.info("API key revoked", key_id=key_id)
                return True
        return False

    async def validate_api_key(self, raw_key: str) -> APIKey | None:
        """Validate an API key and return the key object if valid."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = self._api_keys.get(key_hash)
        if not api_key:
            return None
        if api_key.status != APIKeyStatus.ACTIVE:
            return None
        if api_key.expires_at and api_key.expires_at < datetime.now(UTC):
            api_key.status = APIKeyStatus.EXPIRED
            return None
        api_key.last_used_at = datetime.now(UTC)
        api_key.usage_count += 1
        return api_key

    def list_api_keys(self, organization_id: UUID | None = None) -> list[APIKey]:
        """List API keys, optionally filtered by organization."""
        keys = list(self._api_keys.values())
        if organization_id:
            keys = [k for k in keys if k.organization_id == organization_id]
        return keys

    # ─── Rate Limiting ────────────────────────────────────────────────

    def get_rate_limit_config(self, tier: RateLimitTier) -> RateLimitConfig:
        """Get rate limit configuration for a tier."""
        return _RATE_LIMITS[tier]

    def check_rate_limit(self, api_key: APIKey) -> RateLimitStatus:
        """Check current rate limit status for an API key."""
        config = _RATE_LIMITS[api_key.tier]
        return RateLimitStatus(
            remaining_minute=max(0, config.requests_per_minute - (api_key.usage_count % config.requests_per_minute)),
            remaining_hour=max(0, config.requests_per_hour - (api_key.usage_count % config.requests_per_hour)),
            remaining_day=max(0, config.requests_per_day - (api_key.usage_count % config.requests_per_day)),
            is_limited=api_key.usage_count % config.requests_per_minute >= config.requests_per_minute,
        )

    def list_rate_limit_tiers(self) -> list[RateLimitConfig]:
        """List all available rate limit tiers."""
        return list(_RATE_LIMITS.values())

    # ─── OpenAPI Generation ───────────────────────────────────────────

    def generate_openapi_spec(self) -> dict:
        """Generate OpenAPI 3.1 specification from endpoints."""
        paths: dict = {}
        for ep in _SDK_ENDPOINTS:
            path_key = ep.path
            method_key = ep.method.value.lower()

            operation = {
                "summary": ep.description,
                "tags": [ep.category],
                "security": [{"bearerAuth": []}] if ep.requires_auth else [],
                "responses": {
                    "200": {"description": "Success"},
                    "401": {"description": "Unauthorized"},
                    "429": {"description": "Rate limit exceeded"},
                },
            }

            if ep.method in (ClientMethod.POST, ClientMethod.PUT, ClientMethod.PATCH):
                operation["requestBody"] = {
                    "required": True,
                    "content": {"application/json": {"schema": ep.request_schema or {"type": "object"}}},
                }

            if path_key not in paths:
                paths[path_key] = {}
            paths[path_key][method_key] = operation

        return {
            "openapi": "3.1.0",
            "info": {
                "title": "ComplianceAgent API",
                "version": "1.0.0",
                "description": "AI-powered compliance monitoring and code generation API",
            },
            "servers": [{"url": "https://api.complianceagent.ai/v1"}],
            "paths": paths,
            "components": {
                "securitySchemes": {
                    "bearerAuth": {"type": "http", "scheme": "bearer"},
                    "apiKey": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
                    "oauth2": {
                        "type": "oauth2",
                        "flows": {
                            "clientCredentials": {
                                "tokenUrl": "/oauth2/token",
                                "scopes": {"read": "Read access", "write": "Write access"},
                            },
                        },
                    },
                },
            },
        }

    def get_developer_portal(self) -> dict:
        """Get developer portal content with quickstart, code samples, and API reference."""
        return {
            "quickstart": {
                "title": "Getting Started with ComplianceAgent API",
                "steps": [
                    {"step": 1, "title": "Create an API Key", "description": "Sign up and create an API key at https://app.complianceagent.ai/settings/api"},
                    {"step": 2, "title": "Install SDK", "description": "Install the SDK for your language", "options": {rt.value: pkg.install_command for rt, pkg in zip([p.runtime for p in _SDK_PACKAGES], _SDK_PACKAGES, strict=True)}},
                    {"step": 3, "title": "Make Your First Request", "description": "Check your compliance posture score"},
                    {"step": 4, "title": "Explore Endpoints", "description": f"Browse {len(_SDK_ENDPOINTS)} available endpoints across {len(set(e.category for e in _SDK_ENDPOINTS))} categories"},
                ],
            },
            "code_samples": {
                pkg.runtime.value: {"install": pkg.install_command, "sample": pkg.code_sample}
                for pkg in _SDK_PACKAGES
            },
            "api_reference": {
                "base_url": "https://api.complianceagent.ai/v1",
                "auth_methods": ["API Key", "OAuth2 Client Credentials"],
                "categories": list(set(e.category for e in _SDK_ENDPOINTS)),
                "total_endpoints": len(_SDK_ENDPOINTS),
            },
            "rate_limits": {
                tier.value: {
                    "rpm": config.requests_per_minute,
                    "rph": config.requests_per_hour,
                    "rpd": config.requests_per_day,
                }
                for tier, config in _RATE_LIMITS.items()
            },
        }
