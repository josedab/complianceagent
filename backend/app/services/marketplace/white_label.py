"""White-Label Support - Customization for resellers."""

from datetime import datetime
from typing import Any
from uuid import UUID

import structlog

from app.services.marketplace.models import (
    APIKey,
    PlanTier,
    WhiteLabelConfig,
)


logger = structlog.get_logger()


# Default white-label themes
DEFAULT_THEMES = {
    "default": {
        "primary_color": "#0066cc",
        "secondary_color": "#ffffff",
        "accent_color": "#00cc66",
        "font_family": "Inter, sans-serif",
    },
    "dark": {
        "primary_color": "#1a1a2e",
        "secondary_color": "#16213e",
        "accent_color": "#0f3460",
        "font_family": "Inter, sans-serif",
    },
    "enterprise": {
        "primary_color": "#2c3e50",
        "secondary_color": "#ecf0f1",
        "accent_color": "#3498db",
        "font_family": "Roboto, sans-serif",
    },
}


class WhiteLabelService:
    """Manages white-label configurations for resellers."""

    def __init__(self):
        self._configs: dict[UUID, WhiteLabelConfig] = {}
        self._by_domain: dict[str, UUID] = {}

    def create_config(
        self,
        organization_id: UUID,
        brand_name: str,
        custom_domain: str | None = None,
        logo_url: str | None = None,
        theme: str = "default",
        custom_colors: dict[str, str] | None = None,
    ) -> WhiteLabelConfig:
        """Create a white-label configuration."""
        theme_colors = DEFAULT_THEMES.get(theme, DEFAULT_THEMES["default"])
        
        config = WhiteLabelConfig(
            organization_id=organization_id,
            brand_name=brand_name,
            logo_url=logo_url or "",
            primary_color=custom_colors.get("primary", theme_colors["primary_color"]) if custom_colors else theme_colors["primary_color"],
            secondary_color=custom_colors.get("secondary", theme_colors["secondary_color"]) if custom_colors else theme_colors["secondary_color"],
            custom_domain=custom_domain or "",
        )
        
        self._configs[organization_id] = config
        
        if custom_domain:
            self._by_domain[custom_domain] = organization_id
        
        logger.info(
            "Created white-label config",
            organization_id=str(organization_id),
            brand_name=brand_name,
            custom_domain=custom_domain,
        )
        
        return config

    def get_config(self, organization_id: UUID) -> WhiteLabelConfig | None:
        """Get white-label config by organization."""
        return self._configs.get(organization_id)

    def get_config_by_domain(self, domain: str) -> WhiteLabelConfig | None:
        """Get white-label config by custom domain."""
        org_id = self._by_domain.get(domain)
        if org_id:
            return self._configs.get(org_id)
        return None

    def update_config(
        self,
        organization_id: UUID,
        updates: dict[str, Any],
    ) -> WhiteLabelConfig | None:
        """Update white-label configuration."""
        config = self._configs.get(organization_id)
        if not config:
            return None
        
        # Handle domain change
        if "custom_domain" in updates:
            old_domain = config.custom_domain
            new_domain = updates["custom_domain"]
            
            if old_domain and old_domain in self._by_domain:
                del self._by_domain[old_domain]
            
            if new_domain:
                self._by_domain[new_domain] = organization_id
            
            config.custom_domain = new_domain
        
        # Update other fields
        for key, value in updates.items():
            if hasattr(config, key) and key not in ["id", "organization_id", "created_at"]:
                setattr(config, key, value)
        
        return config

    def generate_embed_config(
        self,
        organization_id: UUID,
        component: str = "full",
    ) -> dict[str, Any]:
        """Generate embeddable configuration for white-label partners.
        
        Args:
            organization_id: Partner organization ID
            component: Which component to embed (full, dashboard, scanner, reports)
            
        Returns:
            Configuration object for embedding
        """
        config = self._configs.get(organization_id)
        if not config:
            # Return default branding
            return {
                "branding": DEFAULT_THEMES["default"],
                "component": component,
                "embed_url": f"/embed/{component}",
            }
        
        return {
            "branding": {
                "name": config.brand_name,
                "logo_url": config.logo_url,
                "primary_color": config.primary_color,
                "secondary_color": config.secondary_color,
            },
            "component": component,
            "embed_url": f"https://{config.custom_domain}/embed/{component}" if config.custom_domain else f"/embed/{component}",
            "custom_domain": config.custom_domain,
            "features": {
                "show_powered_by": True,  # Could be toggled for premium
                "custom_css": True,
                "iframe_allowed": True,
            },
        }

    def generate_sdk_config(
        self,
        organization_id: UUID,
        api_key: APIKey,
    ) -> dict[str, Any]:
        """Generate SDK configuration for white-label integration.
        
        Returns configuration for the JavaScript/Python SDK.
        """
        config = self._configs.get(organization_id)
        
        base_url = "https://api.complianceagent.io"
        if config and config.custom_domain:
            base_url = f"https://{config.custom_domain}/api"
        
        return {
            "sdk_version": "1.0.0",
            "base_url": base_url,
            "api_key_prefix": api_key.key_prefix if api_key else None,
            "branding": {
                "name": config.brand_name if config else "ComplianceAgent",
                "logo_url": config.logo_url if config else None,
            },
            "endpoints": {
                "analysis": f"{base_url}/v1/analysis",
                "intelligence": f"{base_url}/v1/intelligence",
                "evidence": f"{base_url}/v1/evidence",
                "pr_review": f"{base_url}/v1/pr-review",
            },
            "rate_limits": {
                "requests_per_minute": api_key.rate_limit if api_key else 10,
                "monthly_quota": api_key.monthly_limit if api_key else 100,
            },
        }

    def verify_domain(
        self,
        organization_id: UUID,
        domain: str,
    ) -> dict[str, Any]:
        """Generate DNS verification records for custom domain.
        
        Returns records that need to be added for domain verification.
        """
        verification_token = f"ca-verify-{organization_id.hex[:16]}"
        
        return {
            "domain": domain,
            "status": "pending_verification",
            "dns_records": [
                {
                    "type": "TXT",
                    "name": f"_complianceagent.{domain}",
                    "value": verification_token,
                    "purpose": "Domain ownership verification",
                },
                {
                    "type": "CNAME",
                    "name": f"api.{domain}",
                    "value": "gateway.complianceagent.io",
                    "purpose": "API routing",
                },
            ],
            "ssl_provisioning": "automatic",
            "estimated_time": "24-48 hours after DNS propagation",
        }

    def get_partner_dashboard_url(
        self,
        organization_id: UUID,
    ) -> str:
        """Get partner dashboard URL."""
        config = self._configs.get(organization_id)
        
        if config and config.custom_domain:
            return f"https://{config.custom_domain}/partner/dashboard"
        
        return f"https://app.complianceagent.io/partner/{organization_id}/dashboard"


# Global instance
_white_label: WhiteLabelService | None = None


def get_white_label_service() -> WhiteLabelService:
    """Get or create white-label service."""
    global _white_label
    if _white_label is None:
        _white_label = WhiteLabelService()
    return _white_label
