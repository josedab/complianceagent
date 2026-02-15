"""Self-Hosted & Air-Gapped Deployment."""
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
    UpdateChannel,
)
from app.services.self_hosted.service import SelfHostedService


__all__ = ["AirGapStatus", "ClusterSize", "ContainerImage",
           "CryptoLicenseKey", "DeploymentConfig", "DeploymentMode",
           "K8sResourceEstimate", "License", "LicenseStatus", "LicenseType",
           "OfflineBundle", "OfflineRegulationBundle", "SelfHostedService",
           "SystemHealth", "UpdateChannel"]
