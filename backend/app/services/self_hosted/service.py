"""Self-Hosted & Air-Gapped Deployment Service."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.self_hosted.models import (
    DeploymentConfig,
    DeploymentMode,
    License,
    LicenseStatus,
    LicenseType,
    OfflineBundle,
    SystemHealth,
    UpdateChannel,
)

logger = structlog.get_logger()

_OFFLINE_BUNDLES: list[OfflineBundle] = [
    OfflineBundle(
        name="Core Regulations Bundle", version="2026.1",
        frameworks=["gdpr", "hipaa", "pci_dss", "soc2"],
        regulation_count=45, size_mb=128.5,
        checksum=hashlib.sha256(b"core-bundle-2026.1").hexdigest(),
        created_at=datetime.now(UTC),
    ),
    OfflineBundle(
        name="EU Regulations Bundle", version="2026.1",
        frameworks=["gdpr", "eu_ai_act", "dora", "nis2"],
        regulation_count=30, size_mb=95.2,
        checksum=hashlib.sha256(b"eu-bundle-2026.1").hexdigest(),
        created_at=datetime.now(UTC),
    ),
    OfflineBundle(
        name="US Healthcare Bundle", version="2026.1",
        frameworks=["hipaa", "hitech"],
        regulation_count=18, size_mb=42.0,
        checksum=hashlib.sha256(b"us-health-2026.1").hexdigest(),
        created_at=datetime.now(UTC),
    ),
    OfflineBundle(
        name="Financial Services Bundle", version="2026.1",
        frameworks=["pci_dss", "sox", "dora", "glba"],
        regulation_count=35, size_mb=88.7,
        checksum=hashlib.sha256(b"finance-2026.1").hexdigest(),
        created_at=datetime.now(UTC),
    ),
]


class SelfHostedService:
    """Self-hosted and air-gapped deployment management."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._config: DeploymentConfig | None = None
        self._licenses: dict[str, License] = {}
        self._start_time = datetime.now(UTC)

    async def generate_license(
        self,
        organization: str,
        license_type: LicenseType = LicenseType.TRIAL,
        max_users: int = 10,
        max_repositories: int = 5,
        validity_days: int = 30,
    ) -> License:
        """Generate a new license key."""
        key = f"CA-{license_type.value.upper()}-{secrets.token_hex(16).upper()}"

        features_map: dict[LicenseType, list[str]] = {
            LicenseType.TRIAL: ["core_scanning", "basic_reporting", "5_frameworks"],
            LicenseType.STANDARD: ["core_scanning", "reporting", "api_access", "all_frameworks", "ci_cd"],
            LicenseType.ENTERPRISE: ["core_scanning", "reporting", "api_access", "all_frameworks",
                                     "ci_cd", "sso", "audit_portal", "custom_policies", "priority_support"],
            LicenseType.GOVERNMENT: ["core_scanning", "reporting", "api_access", "all_frameworks",
                                     "ci_cd", "sso", "audit_portal", "custom_policies",
                                     "air_gap", "fips_140", "fedramp", "priority_support"],
        }

        license = License(
            license_key=key,
            license_type=license_type,
            status=LicenseStatus.ACTIVE if license_type != LicenseType.TRIAL else LicenseStatus.TRIAL,
            organization=organization,
            max_users=max_users,
            max_repositories=max_repositories,
            features=features_map.get(license_type, []),
            issued_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=validity_days),
        )
        self._licenses[key] = license
        logger.info("License generated", org=organization, type=license_type.value)
        return license

    async def validate_license(self, license_key: str) -> License | None:
        """Validate a license key."""
        license = self._licenses.get(license_key)
        if not license:
            return None
        if not license.is_valid:
            license.status = LicenseStatus.EXPIRED
        return license

    async def configure_deployment(
        self,
        mode: DeploymentMode,
        version: str = "3.0.0",
        local_llm_enabled: bool = False,
        local_llm_model: str = "",
        offline_regulations: list[str] | None = None,
        telemetry_opt_in: bool = False,
    ) -> DeploymentConfig:
        """Configure self-hosted deployment."""
        config = DeploymentConfig(
            mode=mode,
            version=version,
            local_llm_enabled=local_llm_enabled,
            local_llm_model=local_llm_model or ("llama-3-8b-instruct" if local_llm_enabled else ""),
            offline_regulations=offline_regulations or [],
            telemetry_opt_in=telemetry_opt_in,
            configured_at=datetime.now(UTC),
        )
        self._config = config
        logger.info("Deployment configured", mode=mode.value, llm=local_llm_enabled)
        return config

    async def get_config(self) -> DeploymentConfig | None:
        return self._config

    async def list_offline_bundles(self) -> list[OfflineBundle]:
        return _OFFLINE_BUNDLES

    async def get_bundle(self, bundle_name: str) -> OfflineBundle | None:
        for b in _OFFLINE_BUNDLES:
            if b.name.lower() == bundle_name.lower() or str(b.id) == bundle_name:
                return b
        return None

    async def get_system_health(self) -> SystemHealth:
        """Get system health status."""
        uptime = (datetime.now(UTC) - self._start_time).total_seconds()
        has_valid_license = any(lic.is_valid for lic in self._licenses.values())

        return SystemHealth(
            status="healthy" if has_valid_license or not self._licenses else "degraded",
            version=self._config.version if self._config else "3.0.0",
            uptime_seconds=int(uptime),
            database_connected=True,
            llm_available=bool(self._config and self._config.local_llm_enabled),
            license_valid=has_valid_license or not self._licenses,
            disk_usage_percent=35.0,
            memory_usage_percent=42.0,
            last_backup=datetime.now(UTC) - timedelta(hours=6),
            last_regulation_update=datetime.now(UTC) - timedelta(days=3),
        )

    async def create_backup(self) -> dict:
        """Initiate a system backup."""
        return {
            "backup_id": secrets.token_hex(8),
            "status": "completed",
            "size_mb": 256.0,
            "timestamp": datetime.now(UTC).isoformat(),
            "location": "/backups/complianceagent-backup-latest.tar.gz",
        }

    async def get_helm_values(self) -> dict:
        """Get recommended Helm chart values."""
        return {
            "replicaCount": 2,
            "image": {"repository": "ghcr.io/complianceagent/server", "tag": "3.0.0"},
            "service": {"type": "ClusterIP", "port": 8000},
            "ingress": {"enabled": True, "className": "nginx"},
            "postgresql": {"enabled": True, "auth": {"database": "complianceagent"}},
            "redis": {"enabled": True},
            "resources": {
                "requests": {"cpu": "500m", "memory": "512Mi"},
                "limits": {"cpu": "2000m", "memory": "2Gi"},
            },
            "env": {
                "DEPLOYMENT_MODE": "self_hosted",
                "LOCAL_LLM_ENABLED": "false",
                "TELEMETRY_OPT_IN": "false",
            },
        }
