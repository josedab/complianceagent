"""White-label platform service."""

from app.services.white_label_platform.models import (
    BrandingElement,
    InstanceStatus,
    PartnerAnalytics,
    PartnerConfig,
    PartnerTier,
    WhiteLabelInstance,
    WhiteLabelStats,
)
from app.services.white_label_platform.service import WhiteLabelPlatformService


__all__ = [
    "BrandingElement",
    "InstanceStatus",
    "PartnerAnalytics",
    "PartnerConfig",
    "PartnerTier",
    "WhiteLabelInstance",
    "WhiteLabelPlatformService",
    "WhiteLabelStats",
]
