"""Self-Hosted & Air-Gapped Deployment models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
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


class ClusterSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


@dataclass
class K8sResourceEstimate:
    """Kubernetes resource requirements estimate."""
    cluster_size: ClusterSize = ClusterSize.MEDIUM
    cpu_cores: int = 4
    memory_gi: int = 8
    storage_gi: int = 100
    node_count: int = 3
    estimated_monthly_cost_usd: float = 400.0
    components: list[dict] = field(default_factory=list)


@dataclass
class ContainerImage:
    """Container image for air-gapped deployment."""
    name: str = ""
    tag: str = ""
    size_mb: float = 0.0
    digest: str = ""
    required: bool = True


@dataclass
class CryptoLicenseKey:
    """Cryptographically validated license key."""
    id: UUID = field(default_factory=uuid4)
    key_hash: str = ""
    organization: str = ""
    tier: str = "standard"  # standard, professional, enterprise
    features: list[str] = field(default_factory=list)
    max_users: int = 0
    max_repos: int = 0
    issued_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    signature: str = ""
    is_valid: bool = True
    validation_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "key_hash": self.key_hash[:16] + "..." if self.key_hash else "",
            "organization": self.organization,
            "tier": self.tier,
            "features": self.features,
            "max_users": self.max_users,
            "max_repos": self.max_repos,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
        }


@dataclass
class OfflineRegulationBundle:
    """An offline regulation bundle for air-gapped deployments."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    version: str = "1.0.0"
    regulations: list[str] = field(default_factory=list)
    total_rules: int = 0
    size_mb: float = 0.0
    checksum: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_installed: bool = False
    auto_update: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "version": self.version,
            "regulations": self.regulations,
            "total_rules": self.total_rules,
            "size_mb": self.size_mb,
            "checksum": self.checksum,
            "created_at": self.created_at.isoformat(),
            "is_installed": self.is_installed,
            "auto_update": self.auto_update,
        }


@dataclass
class AirGapStatus:
    """Status of air-gapped deployment."""
    is_air_gapped: bool = False
    local_llm_available: bool = False
    local_llm_model: str = ""
    offline_bundles_installed: int = 0
    last_bundle_update: str | None = None
    license_status: str = "valid"
    connectivity_check: str = "offline"
    storage_used_gb: float = 0.0
    storage_total_gb: float = 100.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_air_gapped": self.is_air_gapped,
            "local_llm_available": self.local_llm_available,
            "local_llm_model": self.local_llm_model,
            "offline_bundles_installed": self.offline_bundles_installed,
            "last_bundle_update": self.last_bundle_update,
            "license_status": self.license_status,
            "connectivity_check": self.connectivity_check,
            "storage_used_gb": self.storage_used_gb,
            "storage_total_gb": self.storage_total_gb,
        }
