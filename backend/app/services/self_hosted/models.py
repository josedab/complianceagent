"""Self-Hosted & Air-Gapped Deployment models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class DeploymentMode(str, Enum):
    SAAS = "saas"
    SELF_HOSTED = "self_hosted"
    AIR_GAPPED = "air_gapped"


class LicenseType(str, Enum):
    TRIAL = "trial"
    STANDARD = "standard"
    ENTERPRISE = "enterprise"
    GOVERNMENT = "government"


class LicenseStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    TRIAL = "trial"


class UpdateChannel(str, Enum):
    STABLE = "stable"
    BETA = "beta"
    LTS = "lts"


@dataclass
class License:
    """Deployment license information."""
    id: UUID = field(default_factory=uuid4)
    license_key: str = ""
    license_type: LicenseType = LicenseType.TRIAL
    status: LicenseStatus = LicenseStatus.TRIAL
    organization: str = ""
    max_users: int = 10
    max_repositories: int = 5
    features: list[str] = field(default_factory=list)
    issued_at: datetime | None = None
    expires_at: datetime | None = None

    @property
    def is_valid(self) -> bool:
        if self.status in (LicenseStatus.EXPIRED, LicenseStatus.REVOKED):
            return False
        if self.expires_at and datetime.now(self.expires_at.tzinfo) > self.expires_at:
            return False
        return True


@dataclass
class DeploymentConfig:
    """Self-hosted deployment configuration."""
    id: UUID = field(default_factory=uuid4)
    mode: DeploymentMode = DeploymentMode.SELF_HOSTED
    version: str = ""
    license: License = field(default_factory=License)
    update_channel: UpdateChannel = UpdateChannel.STABLE
    local_llm_enabled: bool = False
    local_llm_model: str = ""
    offline_regulations: list[str] = field(default_factory=list)
    backup_enabled: bool = True
    backup_schedule: str = "0 2 * * *"  # cron: 2 AM daily
    telemetry_opt_in: bool = False
    configured_at: datetime | None = None


@dataclass
class OfflineBundle:
    """An offline regulation bundle for air-gapped deployments."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    version: str = ""
    frameworks: list[str] = field(default_factory=list)
    regulation_count: int = 0
    size_mb: float = 0.0
    checksum: str = ""
    created_at: datetime | None = None


@dataclass
class SystemHealth:
    """Self-hosted system health check."""
    status: str = "healthy"
    version: str = ""
    uptime_seconds: int = 0
    database_connected: bool = True
    llm_available: bool = False
    license_valid: bool = True
    disk_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    last_backup: datetime | None = None
    last_regulation_update: datetime | None = None
