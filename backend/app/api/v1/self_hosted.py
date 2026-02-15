"""API endpoints for Self-Hosted & Air-Gapped Deployment."""

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB, CopilotDep
from app.services.self_hosted import ClusterSize, DeploymentMode, LicenseType, SelfHostedService


logger = structlog.get_logger()
router = APIRouter()


class GenerateLicenseRequest(BaseModel):
    organization: str = Field(..., min_length=1)
    license_type: str = Field(default="trial")
    max_users: int = Field(default=10, ge=1)
    max_repositories: int = Field(default=5, ge=1)
    validity_days: int = Field(default=30, ge=1)


class ConfigureDeploymentRequest(BaseModel):
    mode: str = Field(default="self_hosted")
    version: str = Field(default="3.0.0")
    local_llm_enabled: bool = Field(default=False)
    local_llm_model: str = Field(default="")
    offline_regulations: list[str] = Field(default_factory=list)
    telemetry_opt_in: bool = Field(default=False)


class LicenseSchema(BaseModel):
    id: str
    license_key: str
    license_type: str
    status: str
    organization: str
    max_users: int
    max_repositories: int
    features: list[str]
    is_valid: bool
    expires_at: str | None


class DeploymentSchema(BaseModel):
    mode: str
    version: str
    local_llm_enabled: bool
    local_llm_model: str
    offline_regulations: list[str]
    telemetry_opt_in: bool


class HealthSchema(BaseModel):
    status: str
    version: str
    uptime_seconds: int
    database_connected: bool
    llm_available: bool
    license_valid: bool
    disk_usage_percent: float
    memory_usage_percent: float


@router.post("/licenses", response_model=LicenseSchema, status_code=status.HTTP_201_CREATED,
             summary="Generate deployment license")
async def generate_license(request: GenerateLicenseRequest, db: DB, copilot: CopilotDep) -> LicenseSchema:
    service = SelfHostedService(db=db, copilot_client=copilot)
    lt = LicenseType(request.license_type) if request.license_type in [t.value for t in LicenseType] else LicenseType.TRIAL
    license = await service.generate_license(
        organization=request.organization, license_type=lt,
        max_users=request.max_users, max_repositories=request.max_repositories,
        validity_days=request.validity_days,
    )
    return LicenseSchema(
        id=str(license.id), license_key=license.license_key, license_type=license.license_type.value,
        status=license.status.value, organization=license.organization,
        max_users=license.max_users, max_repositories=license.max_repositories,
        features=license.features, is_valid=license.is_valid,
        expires_at=license.expires_at.isoformat() if license.expires_at else None,
    )


@router.post("/licenses/validate", summary="Validate a license key")
async def validate_license(license_key: str, db: DB, copilot: CopilotDep) -> dict:
    service = SelfHostedService(db=db, copilot_client=copilot)
    license = await service.validate_license(license_key)
    if not license:
        raise HTTPException(status_code=404, detail="Invalid license key")
    return {"valid": license.is_valid, "type": license.license_type.value, "organization": license.organization}


@router.post("/config", response_model=DeploymentSchema, summary="Configure deployment")
async def configure_deployment(request: ConfigureDeploymentRequest, db: DB, copilot: CopilotDep) -> DeploymentSchema:
    service = SelfHostedService(db=db, copilot_client=copilot)
    mode = DeploymentMode(request.mode) if request.mode in [m.value for m in DeploymentMode] else DeploymentMode.SELF_HOSTED
    config = await service.configure_deployment(
        mode=mode, version=request.version, local_llm_enabled=request.local_llm_enabled,
        local_llm_model=request.local_llm_model, offline_regulations=request.offline_regulations,
        telemetry_opt_in=request.telemetry_opt_in,
    )
    return DeploymentSchema(
        mode=config.mode.value, version=config.version, local_llm_enabled=config.local_llm_enabled,
        local_llm_model=config.local_llm_model, offline_regulations=config.offline_regulations,
        telemetry_opt_in=config.telemetry_opt_in,
    )


@router.get("/config", summary="Get current deployment config")
async def get_config(db: DB, copilot: CopilotDep) -> dict:
    service = SelfHostedService(db=db, copilot_client=copilot)
    config = await service.get_config()
    if not config:
        return {"status": "not_configured"}
    return {"mode": config.mode.value, "version": config.version, "local_llm_enabled": config.local_llm_enabled}


@router.get("/bundles", summary="List offline regulation bundles")
async def list_bundles(db: DB, copilot: CopilotDep) -> list[dict]:
    service = SelfHostedService(db=db, copilot_client=copilot)
    bundles = await service.list_offline_bundles()
    return [{"id": str(b.id), "name": b.name, "version": b.version, "frameworks": b.frameworks,
             "regulation_count": b.regulation_count, "size_mb": b.size_mb} for b in bundles]


@router.get("/health", response_model=HealthSchema, summary="System health check")
async def get_health(db: DB, copilot: CopilotDep) -> HealthSchema:
    service = SelfHostedService(db=db, copilot_client=copilot)
    health = await service.get_system_health()
    return HealthSchema(
        status=health.status, version=health.version, uptime_seconds=health.uptime_seconds,
        database_connected=health.database_connected, llm_available=health.llm_available,
        license_valid=health.license_valid, disk_usage_percent=health.disk_usage_percent,
        memory_usage_percent=health.memory_usage_percent,
    )


@router.post("/backup", summary="Create system backup")
async def create_backup(db: DB, copilot: CopilotDep) -> dict:
    service = SelfHostedService(db=db, copilot_client=copilot)
    return await service.create_backup()


@router.get("/helm-values", summary="Get Helm chart values")
async def get_helm_values(db: DB, copilot: CopilotDep) -> dict:
    service = SelfHostedService(db=db, copilot_client=copilot)
    return await service.get_helm_values()


@router.get("/k8s-resources", summary="Calculate Kubernetes resource requirements")
async def calculate_k8s_resources(
    db: DB, copilot: CopilotDep, size: str = "medium",
) -> dict:
    """Calculate recommended K8s resources for a given cluster size."""
    service = SelfHostedService(db=db, copilot_client=copilot)
    try:
        cluster_size = ClusterSize(size)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid size: {size}. Use: small, medium, large")
    estimate = await service.calculate_k8s_resources(cluster_size)
    return {
        "cluster_size": estimate.cluster_size.value,
        "cpu_cores": estimate.cpu_cores,
        "memory_gi": estimate.memory_gi,
        "storage_gi": estimate.storage_gi,
        "node_count": estimate.node_count,
        "estimated_monthly_cost_usd": estimate.estimated_monthly_cost_usd,
        "components": estimate.components,
    }


@router.get("/airgapped-images", summary="List air-gapped container images")
async def list_airgapped_images(db: DB, copilot: CopilotDep) -> list[dict]:
    """List all container images required for air-gapped deployment."""
    service = SelfHostedService(db=db, copilot_client=copilot)
    images = await service.list_airgapped_images()
    return [
        {"name": img.name, "tag": img.tag, "size_mb": img.size_mb,
         "digest": img.digest, "required": img.required}
        for img in images
    ]


# ── Cryptographic License & Air-Gapped Schemas ──────────────────────────


class CryptoLicenseSchema(BaseModel):
    id: str
    key_hash: str
    organization: str
    tier: str
    features: list[str]
    max_users: int
    max_repos: int
    issued_at: str
    expires_at: str | None
    is_valid: bool
    validation_errors: list[str]


class ValidateLicenseRequest(BaseModel):
    license_key: str = Field(..., description="License key in header.payload.signature format")


class OfflineBundleSchema(BaseModel):
    id: str
    name: str
    version: str
    regulations: list[str]
    total_rules: int
    size_mb: float
    checksum: str
    created_at: str
    is_installed: bool
    auto_update: bool


class AirGapStatusSchema(BaseModel):
    is_air_gapped: bool
    local_llm_available: bool
    local_llm_model: str
    offline_bundles_installed: int
    last_bundle_update: str | None
    license_status: str
    connectivity_check: str
    storage_used_gb: float
    storage_total_gb: float


@router.post("/validate-license", response_model=CryptoLicenseSchema)
async def validate_license_crypto(request: ValidateLicenseRequest, db: DB, copilot: CopilotDep) -> CryptoLicenseSchema:
    """Validate a license key using cryptographic verification."""
    service = SelfHostedService(db=db, copilot_client=copilot)
    result = await service.validate_license_crypto(request.license_key)
    return CryptoLicenseSchema(**result.to_dict())


@router.get("/offline-bundles", response_model=list[OfflineBundleSchema])
async def list_offline_bundles(db: DB, copilot: CopilotDep) -> list[OfflineBundleSchema]:
    """List available offline regulation bundles."""
    service = SelfHostedService(db=db, copilot_client=copilot)
    bundles = await service.list_offline_regulation_bundles()
    return [OfflineBundleSchema(**b.to_dict()) for b in bundles]


@router.post("/offline-bundles/{bundle_id}/install")
async def install_bundle(bundle_id: str, db: DB, copilot: CopilotDep) -> dict[str, Any]:
    """Install an offline regulation bundle."""
    service = SelfHostedService(db=db, copilot_client=copilot)
    return await service.install_regulation_bundle(bundle_id)


@router.get("/air-gap-status", response_model=AirGapStatusSchema)
async def get_air_gap_status(db: DB, copilot: CopilotDep) -> AirGapStatusSchema:
    """Get the current air-gapped deployment status."""
    service = SelfHostedService(db=db, copilot_client=copilot)
    status = await service.get_air_gap_status()
    return AirGapStatusSchema(**status.to_dict())
