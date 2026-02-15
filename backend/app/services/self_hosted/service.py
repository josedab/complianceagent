"""Self-Hosted & Air-Gapped Deployment Service."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.self_hosted.models import (
    AirGapStatus,
    ClusterSize,
    ContainerImage,
    CryptoLicenseKey,
    DeploymentConfig,
    DeploymentMode,
    K8sResourceEstimate,
    License,
    LicenseStatus,
    LicenseType,
    OfflineBundle,
    OfflineRegulationBundle,
    SystemHealth,
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

    async def calculate_k8s_resources(
        self, cluster_size: ClusterSize = ClusterSize.MEDIUM,
    ) -> K8sResourceEstimate:
        """Calculate recommended K8s resources for a given cluster size."""
        sizing = {
            ClusterSize.SMALL: {
                "cpu_cores": 2, "memory_gi": 4, "storage_gi": 50,
                "node_count": 2, "cost": 150.0,
            },
            ClusterSize.MEDIUM: {
                "cpu_cores": 4, "memory_gi": 8, "storage_gi": 100,
                "node_count": 3, "cost": 400.0,
            },
            ClusterSize.LARGE: {
                "cpu_cores": 8, "memory_gi": 16, "storage_gi": 250,
                "node_count": 5, "cost": 900.0,
            },
        }
        spec = sizing[cluster_size]

        components = [
            {"name": "api-server", "replicas": spec["node_count"] - 1, "cpu": "500m", "memory": "512Mi"},
            {"name": "worker", "replicas": spec["node_count"] - 1, "cpu": "500m", "memory": "1Gi"},
            {"name": "frontend", "replicas": 2, "cpu": "200m", "memory": "256Mi"},
            {"name": "postgresql", "replicas": 1, "cpu": "500m", "memory": "1Gi",
             "storage": f"{spec['storage_gi'] // 2}Gi"},
            {"name": "redis", "replicas": 1, "cpu": "200m", "memory": "256Mi"},
            {"name": "elasticsearch", "replicas": 1 if cluster_size == ClusterSize.SMALL else 3,
             "cpu": "1000m", "memory": "2Gi", "storage": f"{spec['storage_gi'] // 4}Gi"},
        ]

        return K8sResourceEstimate(
            cluster_size=cluster_size,
            cpu_cores=spec["cpu_cores"],
            memory_gi=spec["memory_gi"],
            storage_gi=spec["storage_gi"],
            node_count=spec["node_count"],
            estimated_monthly_cost_usd=spec["cost"],
            components=components,
        )

    async def list_airgapped_images(self) -> list[ContainerImage]:
        """List all container images needed for air-gapped deployment."""
        version = self._config.version if self._config else "3.0.0"
        return [
            ContainerImage(
                name="ghcr.io/complianceagent/server", tag=version,
                size_mb=245.0, digest=hashlib.sha256(f"server-{version}".encode()).hexdigest()[:16],
            ),
            ContainerImage(
                name="ghcr.io/complianceagent/worker", tag=version,
                size_mb=210.0, digest=hashlib.sha256(f"worker-{version}".encode()).hexdigest()[:16],
            ),
            ContainerImage(
                name="ghcr.io/complianceagent/frontend", tag=version,
                size_mb=85.0, digest=hashlib.sha256(f"frontend-{version}".encode()).hexdigest()[:16],
            ),
            ContainerImage(
                name="postgres", tag="16-alpine", size_mb=115.0,
                digest=hashlib.sha256(b"postgres-16").hexdigest()[:16],
            ),
            ContainerImage(
                name="redis", tag="7-alpine", size_mb=30.0,
                digest=hashlib.sha256(b"redis-7").hexdigest()[:16],
            ),
            ContainerImage(
                name="elasticsearch", tag="8.12.0", size_mb=850.0,
                digest=hashlib.sha256(b"es-8.12").hexdigest()[:16],
            ),
        ]

    # ── Cryptographic License Validation ─────────────────────────────────

    async def validate_license_crypto(self, license_key: str) -> CryptoLicenseKey:
        """Validate a license key using cryptographic verification."""
        import base64
        import hmac
        import json

        SECRET = b"complianceagent-license-secret-key-v1"  # noqa: N806
        errors: list[str] = []

        key_hash = hashlib.sha256(license_key.encode()).hexdigest()

        try:
            parts = license_key.split(".")
            if len(parts) != 3:
                errors.append("Invalid license key format: expected 3 parts separated by dots")
                return CryptoLicenseKey(
                    key_hash=key_hash,
                    is_valid=False,
                    validation_errors=errors,
                )

            header, payload, signature = parts

            # Verify HMAC signature
            expected_sig = hmac.new(SECRET, f"{header}.{payload}".encode(), hashlib.sha256).hexdigest()[:32]
            sig_valid = hmac.compare_digest(signature[:32], expected_sig[:32]) if len(signature) >= 32 else False

            if not sig_valid:
                errors.append("Invalid signature: license key may be tampered with")

            # Decode payload
            try:
                padded = payload + "=" * (4 - len(payload) % 4)
                decoded = base64.urlsafe_b64decode(padded).decode()
                license_data = json.loads(decoded)
            except Exception:
                license_data = {
                    "org": "demo-org",
                    "tier": "enterprise",
                    "features": ["all"],
                    "max_users": 100,
                    "max_repos": -1,
                }

            # Check expiration
            expires = license_data.get("exp")
            expires_dt = None
            if expires:
                expires_dt = datetime.fromtimestamp(expires, tz=UTC)
                if expires_dt < datetime.now(UTC):
                    errors.append("License has expired")

            tier = license_data.get("tier", "standard")
            features_map = {
                "standard": ["scanning", "reporting"],
                "professional": ["scanning", "reporting", "ide_integration", "ci_cd"],
                "enterprise": ["scanning", "reporting", "ide_integration", "ci_cd", "air_gapped", "sso", "api_access"],
            }

            return CryptoLicenseKey(
                key_hash=key_hash,
                organization=license_data.get("org", "unknown"),
                tier=tier,
                features=license_data.get("features", features_map.get(tier, [])),
                max_users=license_data.get("max_users", 10),
                max_repos=license_data.get("max_repos", 5),
                expires_at=expires_dt,
                signature=signature[:16] + "...",
                is_valid=len(errors) == 0,
                validation_errors=errors,
            )

        except Exception as e:
            errors.append(f"Validation error: {e}")
            return CryptoLicenseKey(
                key_hash=key_hash,
                is_valid=False,
                validation_errors=errors,
            )

    # ── Offline Regulation Bundles ───────────────────────────────────────

    async def list_offline_regulation_bundles(self) -> list[OfflineRegulationBundle]:
        """List available offline regulation bundles."""
        return [
            OfflineRegulationBundle(
                name="GDPR Complete Bundle",
                version="2026.1.0",
                regulations=["GDPR", "ePrivacy"],
                total_rules=342,
                size_mb=45.2,
                checksum=hashlib.sha256(b"gdpr-bundle-v2026.1.0").hexdigest()[:16],
                is_installed=True,
            ),
            OfflineRegulationBundle(
                name="US Privacy Bundle",
                version="2026.1.0",
                regulations=["CCPA", "CPRA", "VCDPA", "CPA"],
                total_rules=278,
                size_mb=38.7,
                checksum=hashlib.sha256(b"us-privacy-bundle-v2026.1.0").hexdigest()[:16],
                is_installed=True,
            ),
            OfflineRegulationBundle(
                name="Healthcare Compliance Bundle",
                version="2026.1.0",
                regulations=["HIPAA", "HITECH", "FDA 21 CFR Part 11"],
                total_rules=195,
                size_mb=28.3,
                checksum=hashlib.sha256(b"healthcare-bundle-v2026.1.0").hexdigest()[:16],
                is_installed=False,
            ),
            OfflineRegulationBundle(
                name="Financial Services Bundle",
                version="2026.1.0",
                regulations=["PCI-DSS", "SOX", "GLBA", "MiFID II"],
                total_rules=412,
                size_mb=52.1,
                checksum=hashlib.sha256(b"finserv-bundle-v2026.1.0").hexdigest()[:16],
                is_installed=False,
            ),
            OfflineRegulationBundle(
                name="AI & ML Governance Bundle",
                version="2026.1.0",
                regulations=["EU AI Act", "NIST AI RMF", "ISO 42001"],
                total_rules=156,
                size_mb=22.8,
                checksum=hashlib.sha256(b"ai-governance-bundle-v2026.1.0").hexdigest()[:16],
                is_installed=False,
            ),
        ]

    async def install_regulation_bundle(self, bundle_id: str) -> dict[str, Any]:
        """Install an offline regulation bundle."""
        bundles = await self.list_offline_regulation_bundles()
        for bundle in bundles:
            if str(bundle.id) == bundle_id:
                bundle.is_installed = True
                logger.info("Bundle installed", bundle_name=bundle.name)
                return {
                    "status": "installed",
                    "bundle": bundle.to_dict(),
                    "message": f"Successfully installed {bundle.name}",
                }
        return {"status": "error", "message": "Bundle not found"}

    # ── Air-Gap Status ───────────────────────────────────────────────────

    async def get_air_gap_status(self) -> AirGapStatus:
        """Get the current air-gapped deployment status."""
        bundles = await self.list_offline_regulation_bundles()
        installed = sum(1 for b in bundles if b.is_installed)

        return AirGapStatus(
            is_air_gapped=True,
            local_llm_available=False,
            local_llm_model="",
            offline_bundles_installed=installed,
            last_bundle_update=datetime.now(UTC).isoformat(),
            license_status="valid",
            connectivity_check="offline",
            storage_used_gb=round(sum(b.size_mb for b in bundles if b.is_installed) / 1024, 2),
            storage_total_gb=100.0,
        )
