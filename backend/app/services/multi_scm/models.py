"""Multi-SCM Support models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class SCMProvider(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    AZURE_DEVOPS = "azure_devops"


class SCMConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"


class PRStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


@dataclass
class SCMConnection:
    id: UUID = field(default_factory=uuid4)
    provider: SCMProvider = SCMProvider.GITHUB
    organization: str = ""
    base_url: str = ""
    status: SCMConnectionStatus = SCMConnectionStatus.PENDING
    repositories_synced: int = 0
    last_sync_at: datetime | None = None
    connected_at: datetime | None = None
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedRepository:
    id: UUID = field(default_factory=uuid4)
    provider: SCMProvider = SCMProvider.GITHUB
    provider_id: str = ""
    full_name: str = ""
    default_branch: str = "main"
    url: str = ""
    private: bool = False
    language: str = ""
    compliance_score: float = 0.0
    last_scan_at: datetime | None = None


@dataclass
class UnifiedPullRequest:
    id: UUID = field(default_factory=uuid4)
    provider: SCMProvider = SCMProvider.GITHUB
    provider_id: str = ""
    repo_full_name: str = ""
    number: int = 0
    title: str = ""
    status: PRStatus = PRStatus.OPEN
    author: str = ""
    source_branch: str = ""
    target_branch: str = "main"
    compliance_check_status: str = "pending"
    url: str = ""
    created_at: datetime | None = None


@dataclass
class UnifiedWebhook:
    id: UUID = field(default_factory=uuid4)
    provider: SCMProvider = SCMProvider.GITHUB
    event_type: str = ""
    repo_full_name: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    processed: bool = False
    received_at: datetime | None = None


@dataclass
class SCMSyncStatus:
    provider: SCMProvider = SCMProvider.GITHUB
    total_repos: int = 0
    repos_scanned: int = 0
    prs_analyzed: int = 0
    webhooks_processed: int = 0
    last_sync_at: datetime | None = None
    errors: list[str] = field(default_factory=list)
