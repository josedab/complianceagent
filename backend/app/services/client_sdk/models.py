"""Compliance Agent Client SDK models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SDKRuntime(str, Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    GO = "go"


class ClientMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


@dataclass
class SDKConfig:
    base_url: str = "https://api.complianceagent.ai/v1"
    api_key: str = ""
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_backoff_factor: float = 0.5


@dataclass
class SDKEndpoint:
    path: str = ""
    method: ClientMethod = ClientMethod.GET
    description: str = ""
    request_schema: dict[str, Any] = field(default_factory=dict)
    response_schema: dict[str, Any] = field(default_factory=dict)
    requires_auth: bool = True
    rate_limit_group: str = "default"


@dataclass
class SDKPackageInfo:
    runtime: SDKRuntime = SDKRuntime.PYTHON
    name: str = ""
    version: str = "0.1.0"
    install_command: str = ""
    source_url: str = ""
    docs_url: str = ""
    changelog_url: str = ""
    min_runtime_version: str = ""
    dependencies: list[str] = field(default_factory=list)
    code_sample: str = ""


@dataclass
class GeneratedClient:
    runtime: SDKRuntime = SDKRuntime.PYTHON
    code: str = ""
    filename: str = ""
    endpoints_covered: int = 0
    generated_at: datetime | None = None


@dataclass
class SDKStats:
    total_endpoints: int = 0
    packages_available: int = 0
    by_method: dict[str, int] = field(default_factory=dict)
    total_downloads: dict[str, int] = field(default_factory=dict)
