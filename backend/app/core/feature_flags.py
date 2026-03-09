"""Feature flag configuration system for gating experimental services.

Provides a centralized way to enable/disable services across the application.
Flags can be configured via environment variables with the prefix FEATURE_FLAG_.
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Any

import structlog


logger = structlog.get_logger()


class ServiceTier(str, Enum):
    """Classification of service maturity levels."""
    STABLE = "stable"
    BETA = "beta"
    EXPERIMENTAL = "experimental"
    STUB = "stub"


class FeatureFlag:
    """Represents a single feature flag with metadata."""

    def __init__(
        self,
        name: str,
        default: bool = False,
        tier: ServiceTier = ServiceTier.EXPERIMENTAL,
        description: str = "",
    ) -> None:
        self.name = name
        self.default = default
        self.tier = tier
        self.description = description

    @property
    def env_key(self) -> str:
        return f"FEATURE_FLAG_{self.name.upper()}"

    @property
    def enabled(self) -> bool:
        env_val = os.environ.get(self.env_key)
        if env_val is not None:
            return env_val.lower() in ("1", "true", "yes", "on")
        return self.default


class FeatureFlagRegistry:
    """Central registry for all feature flags."""

    def __init__(self) -> None:
        self._flags: dict[str, FeatureFlag] = {}

    def register(
        self,
        name: str,
        default: bool = False,
        tier: ServiceTier = ServiceTier.EXPERIMENTAL,
        description: str = "",
    ) -> FeatureFlag:
        """Register a new feature flag."""
        flag = FeatureFlag(name=name, default=default, tier=tier, description=description)
        self._flags[name] = flag
        return flag

    def is_enabled(self, name: str) -> bool:
        """Check if a feature flag is enabled."""
        flag = self._flags.get(name)
        if flag is None:
            logger.warning("Unknown feature flag queried", flag=name)
            return False
        return flag.enabled

    def get(self, name: str) -> FeatureFlag | None:
        """Get a feature flag by name."""
        return self._flags.get(name)

    def list_flags(self, tier: ServiceTier | None = None) -> list[dict[str, Any]]:
        """List all registered flags, optionally filtered by tier."""
        flags = self._flags.values()
        if tier is not None:
            flags = [f for f in flags if f.tier == tier]
        return [
            {
                "name": f.name,
                "enabled": f.enabled,
                "tier": f.tier.value,
                "description": f.description,
                "env_key": f.env_key,
            }
            for f in sorted(flags, key=lambda f: f.name)
        ]

    def enabled_flags(self) -> list[str]:
        """Return names of all currently enabled flags."""
        return [name for name, flag in self._flags.items() if flag.enabled]


# Global registry instance
registry = FeatureFlagRegistry()

# ── Stable services (enabled by default) ────────────────────────────
registry.register("compliance", default=True, tier=ServiceTier.STABLE, description="Core compliance engine")
registry.register("audit", default=True, tier=ServiceTier.STABLE, description="Audit trail and logging")
registry.register("regulations", default=True, tier=ServiceTier.STABLE, description="Regulation management")
registry.register("auth", default=True, tier=ServiceTier.STABLE, description="Authentication and authorization")

# ── Beta services (enabled by default, ready for wider testing) ─────
registry.register("drift_detection", default=True, tier=ServiceTier.BETA, description="Compliance drift detection")
registry.register("evidence_vault", default=True, tier=ServiceTier.BETA, description="Evidence storage and chain of custody")
registry.register("cost_calculator", default=True, tier=ServiceTier.BETA, description="Compliance cost estimation")
registry.register("starter_kits", default=True, tier=ServiceTier.BETA, description="Regulation starter kits")

# ── Experimental services (disabled by default) ─────────────────────
registry.register("ai_observatory", default=False, tier=ServiceTier.EXPERIMENTAL, description="AI model risk monitoring")
registry.register("blockchain_audit", default=False, tier=ServiceTier.EXPERIMENTAL, description="Blockchain-based audit trail")
registry.register("chaos_engineering", default=False, tier=ServiceTier.EXPERIMENTAL, description="Compliance chaos testing")
registry.register("cross_border_transfer", default=False, tier=ServiceTier.EXPERIMENTAL, description="Cross-border data transfer management")
registry.register("dao_governance", default=False, tier=ServiceTier.EXPERIMENTAL, description="DAO-based compliance governance")
registry.register("digital_twin", default=False, tier=ServiceTier.EXPERIMENTAL, description="Regulatory digital twin simulation")
registry.register("federated_intel", default=False, tier=ServiceTier.EXPERIMENTAL, description="Federated compliance intelligence")
registry.register("game_engine", default=False, tier=ServiceTier.EXPERIMENTAL, description="Compliance gamification engine")
registry.register("graph_explorer", default=False, tier=ServiceTier.EXPERIMENTAL, description="Compliance graph exploration")
registry.register("impact_simulator", default=False, tier=ServiceTier.EXPERIMENTAL, description="Regulatory impact simulation")
registry.register("incident_playbook", default=False, tier=ServiceTier.EXPERIMENTAL, description="Incident response playbooks")
registry.register("knowledge_fabric", default=False, tier=ServiceTier.EXPERIMENTAL, description="Compliance knowledge graph fabric")
registry.register("multi_llm", default=False, tier=ServiceTier.EXPERIMENTAL, description="Multi-LLM regulatory parsing")
registry.register("prediction_market", default=False, tier=ServiceTier.EXPERIMENTAL, description="Regulatory prediction market")
registry.register("self_healing_mesh", default=False, tier=ServiceTier.EXPERIMENTAL, description="Self-healing compliance mesh")
registry.register("stress_testing", default=False, tier=ServiceTier.EXPERIMENTAL, description="Compliance stress testing")
registry.register("zero_trust_scanner", default=False, tier=ServiceTier.EXPERIMENTAL, description="Zero-trust security scanning")

# ── Stub services (disabled by default, placeholder implementations) ─
registry.register("agent_swarm", default=False, tier=ServiceTier.STUB, description="Agent swarm orchestration")
registry.register("compliance_streaming", default=False, tier=ServiceTier.STUB, description="Real-time compliance streaming")
registry.register("marketplace_revenue", default=False, tier=ServiceTier.STUB, description="Marketplace revenue tracking")
registry.register("mobile_backend", default=False, tier=ServiceTier.STUB, description="Mobile app backend")
registry.register("saas_platform", default=False, tier=ServiceTier.STUB, description="Multi-tenant SaaS platform")
registry.register("twin_simulation", default=False, tier=ServiceTier.STUB, description="Twin simulation engine")
registry.register("white_label_platform", default=False, tier=ServiceTier.STUB, description="White-label platform")


def is_enabled(flag_name: str) -> bool:
    """Convenience function to check if a feature flag is enabled."""
    return registry.is_enabled(flag_name)
