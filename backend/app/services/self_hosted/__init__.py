"""Self-Hosted & Air-Gapped Deployment."""
from app.services.self_hosted.service import SelfHostedService
from app.services.self_hosted.models import (
    DeploymentConfig, DeploymentMode, License, LicenseStatus, LicenseType,
    OfflineBundle, SystemHealth, UpdateChannel,
)
__all__ = ["SelfHostedService", "DeploymentConfig", "DeploymentMode", "License",
           "LicenseStatus", "LicenseType", "OfflineBundle", "SystemHealth", "UpdateChannel"]
