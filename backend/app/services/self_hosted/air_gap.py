"""Air-gapped deployment support with license management, offline regulation
bundles, and local LLM configuration.
"""

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog


logger = structlog.get_logger()


class LicenseTier(str, Enum):
    TRIAL = "trial"
    STANDARD = "standard"
    ENTERPRISE = "enterprise"
    GOVERNMENT = "government"


class DeploymentMode(str, Enum):
    SAAS = "saas"
    SELF_HOSTED = "self_hosted"
    AIR_GAPPED = "air_gapped"


class LLMBackend(str, Enum):
    CLOUD_COPILOT = "cloud_copilot"
    LOCAL_OLLAMA = "local_ollama"
    LOCAL_VLLM = "local_vllm"
    HYBRID = "hybrid"


@dataclass
class LicenseKey:
    """A validated license key for self-hosted deployments."""

    id: UUID = field(default_factory=uuid4)
    key: str = ""
    tier: LicenseTier = LicenseTier.TRIAL
    organization: str = ""
    issued_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    max_users: int = 5
    max_repos: int = 10
    features: list[str] = field(default_factory=list)
    valid: bool = True
    fingerprint: str = ""

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now(UTC) > self.expires_at


@dataclass
class RegulationBundle:
    """An offline regulation bundle for air-gapped deployments."""

    id: str = ""
    name: str = ""
    description: str = ""
    frameworks: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    size_mb: float = 0.0
    checksum_sha256: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class LocalLLMConfig:
    """Configuration for a local LLM backend."""

    backend: LLMBackend = LLMBackend.LOCAL_OLLAMA
    model_name: str = "llama3:8b"
    base_url: str = "http://localhost:11434"
    max_tokens: int = 4096
    temperature: float = 0.1
    gpu_layers: int = -1
    context_window: int = 8192
    enabled: bool = False


@dataclass
class AirGapConfig:
    """Configuration for air-gapped deployments."""

    deployment_mode: DeploymentMode = DeploymentMode.SELF_HOSTED
    license_key: str = ""
    llm_config: LocalLLMConfig = field(default_factory=LocalLLMConfig)
    regulation_bundles: list[str] = field(default_factory=list)
    update_channel: str = "stable"
    telemetry_enabled: bool = False
    backup_encryption_key: str = ""


# Built-in regulation bundles
OFFLINE_BUNDLES: list[RegulationBundle] = [
    RegulationBundle(
        id="core",
        name="Core Compliance Bundle",
        description="GDPR, CCPA, SOC 2 — essential frameworks for any software company",
        frameworks=["gdpr", "ccpa", "soc2"],
        version="2026.1",
        size_mb=12.5,
    ),
    RegulationBundle(
        id="eu",
        name="EU Regulatory Bundle",
        description="Full EU regulatory coverage: GDPR, EU AI Act, NIS2, DORA, CSRD",
        frameworks=["gdpr", "eu_ai_act", "nis2", "dora", "csrd"],
        version="2026.1",
        size_mb=28.3,
    ),
    RegulationBundle(
        id="healthcare",
        name="Healthcare Bundle",
        description="HIPAA, HITRUST, FDA 21 CFR Part 11",
        frameworks=["hipaa", "hitrust", "fda_21cfr11"],
        version="2026.1",
        size_mb=18.7,
    ),
    RegulationBundle(
        id="financial",
        name="Financial Services Bundle",
        description="PCI-DSS, SOX, DORA, SEC rules, GLBA",
        frameworks=["pci_dss", "sox", "dora", "sec_cyber", "glba"],
        version="2026.1",
        size_mb=22.1,
    ),
]

LICENSE_TIER_LIMITS: dict[str, dict[str, Any]] = {
    "trial": {"max_users": 5, "max_repos": 3, "duration_days": 30, "features": ["core"]},
    "standard": {
        "max_users": 50,
        "max_repos": 25,
        "duration_days": 365,
        "features": ["core", "ai", "ide"],
    },
    "enterprise": {
        "max_users": -1,
        "max_repos": -1,
        "duration_days": 365,
        "features": ["core", "ai", "ide", "sso", "audit"],
    },
    "government": {
        "max_users": -1,
        "max_repos": -1,
        "duration_days": 365,
        "features": ["core", "ai", "ide", "sso", "audit", "air_gapped"],
    },
}


class AirGapService:
    """Manages air-gapped deployment features."""

    LICENSE_SECRET = "complianceagent-license-signing-key"  # noqa: S105

    def __init__(self):
        self._licenses: dict[str, LicenseKey] = {}
        self._configs: dict[str, AirGapConfig] = {}

    def generate_license(
        self,
        organization: str,
        tier: LicenseTier = LicenseTier.TRIAL,
    ) -> LicenseKey:
        """Generate a new license key."""
        limits = LICENSE_TIER_LIMITS.get(tier.value, LICENSE_TIER_LIMITS["trial"])
        duration = limits["duration_days"]
        expires = datetime.now(UTC) + timedelta(days=duration)

        payload = json.dumps(
            {
                "org": organization,
                "tier": tier.value,
                "exp": expires.isoformat(),
            },
            sort_keys=True,
        )

        signature = hmac.new(
            self.LICENSE_SECRET.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]

        key_str = f"CA-{tier.value.upper()}-{signature}"

        license_key = LicenseKey(
            key=key_str,
            tier=tier,
            organization=organization,
            expires_at=expires,
            max_users=limits["max_users"],
            max_repos=limits["max_repos"],
            features=limits["features"],
            fingerprint=signature,
        )
        self._licenses[key_str] = license_key

        logger.info("License generated", org=organization, tier=tier.value, key=key_str)
        return license_key

    def validate_license(self, key: str) -> LicenseKey | None:
        """Validate a license key and return its details."""
        license_key = self._licenses.get(key)
        if not license_key:
            return None
        if license_key.is_expired():
            license_key.valid = False
        return license_key

    def get_available_bundles(self) -> list[RegulationBundle]:
        """List available offline regulation bundles."""
        return OFFLINE_BUNDLES

    def get_bundle(self, bundle_id: str) -> RegulationBundle | None:
        """Get a specific regulation bundle."""
        for b in OFFLINE_BUNDLES:
            if b.id == bundle_id:
                return b
        return None

    def create_deployment_config(
        self,
        organization: str,
        mode: DeploymentMode = DeploymentMode.SELF_HOSTED,
        license_key: str = "",
        llm_backend: LLMBackend = LLMBackend.CLOUD_COPILOT,
        bundles: list[str] | None = None,
    ) -> AirGapConfig:
        """Create a deployment configuration."""
        llm_config = LocalLLMConfig(
            backend=llm_backend,
            enabled=llm_backend != LLMBackend.CLOUD_COPILOT,
        )

        config = AirGapConfig(
            deployment_mode=mode,
            license_key=license_key,
            llm_config=llm_config,
            regulation_bundles=bundles or ["core"],
            telemetry_enabled=mode == DeploymentMode.SAAS,
        )
        self._configs[organization] = config

        logger.info(
            "Deployment config created",
            org=organization,
            mode=mode.value,
            llm=llm_backend.value,
        )
        return config

    def generate_helm_values(
        self,
        organization: str,
        config: AirGapConfig | None = None,
    ) -> dict[str, Any]:
        """Generate Helm chart values.yaml for deployment."""
        cfg = config or self._configs.get(organization, AirGapConfig())

        return {
            "global": {
                "environment": "production",
                "deploymentMode": cfg.deployment_mode.value,
                "licenseKey": cfg.license_key,
                "telemetry": {"enabled": cfg.telemetry_enabled},
            },
            "backend": {
                "image": {"repository": "ghcr.io/complianceagent/backend", "tag": "latest"},
                "replicas": 2,
                "resources": {
                    "requests": {"cpu": "500m", "memory": "1Gi"},
                    "limits": {"cpu": "2", "memory": "4Gi"},
                },
                "env": {
                    "DEPLOYMENT_MODE": cfg.deployment_mode.value,
                    "LLM_BACKEND": cfg.llm_config.backend.value,
                    "LLM_BASE_URL": cfg.llm_config.base_url,
                    "LLM_MODEL": cfg.llm_config.model_name,
                },
            },
            "frontend": {
                "image": {"repository": "ghcr.io/complianceagent/frontend", "tag": "latest"},
                "replicas": 2,
            },
            "postgresql": {
                "enabled": True,
                "auth": {"database": "complianceagent"},
                "primary": {"persistence": {"size": "50Gi"}},
            },
            "redis": {"enabled": True, "architecture": "standalone"},
            "elasticsearch": {
                "enabled": True,
                "replicas": 1,
                "volumeClaimTemplate": {"resources": {"requests": {"storage": "30Gi"}}},
            },
            "regulationBundles": cfg.regulation_bundles,
        }
