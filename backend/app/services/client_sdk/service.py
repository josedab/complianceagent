"""Compliance Agent Client SDK Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.client_sdk.models import (
    ClientMethod,
    GeneratedClient,
    SDKConfig,
    SDKEndpoint,
    SDKPackageInfo,
    SDKRuntime,
    SDKStats,
)


logger = structlog.get_logger()

_SDK_ENDPOINTS: list[SDKEndpoint] = [
    SDKEndpoint(path="/posture/score", method=ClientMethod.GET, description="Get compliance posture score"),
    SDKEndpoint(path="/violations", method=ClientMethod.GET, description="List violations"),
    SDKEndpoint(path="/regulations", method=ClientMethod.GET, description="List regulations"),
    SDKEndpoint(path="/audit", method=ClientMethod.GET, description="Get audit trail"),
    SDKEndpoint(path="/compliance/assess", method=ClientMethod.POST, description="Assess compliance"),
    SDKEndpoint(path="/compliance/generate", method=ClientMethod.POST, description="Generate compliant code"),
    SDKEndpoint(path="/scan", method=ClientMethod.POST, description="Trigger compliance scan"),
    SDKEndpoint(path="/evidence/generate", method=ClientMethod.POST, description="Generate evidence package"),
    SDKEndpoint(path="/knowledge/search", method=ClientMethod.POST, description="Search knowledge fabric"),
    SDKEndpoint(path="/predict/violations", method=ClientMethod.POST, description="Predict violations"),
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
]


class ClientSDKService:
    """Compliance Agent SDK management and client generation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def list_endpoints(self, method: ClientMethod | None = None) -> list[SDKEndpoint]:
        results = list(_SDK_ENDPOINTS)
        if method:
            results = [e for e in results if e.method == method]
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
            total_downloads={"python": 2340, "typescript": 1820, "go": 540},
        )
