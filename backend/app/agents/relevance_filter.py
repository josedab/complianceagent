"""Relevance filtering for requirements based on customer profile."""

from abc import ABC, abstractmethod
from typing import Any

import structlog

from app.models.customer_profile import CustomerProfile


logger = structlog.get_logger()


class RelevanceStrategy(ABC):
    """Strategy for determining requirement relevance."""

    @abstractmethod
    def is_relevant(self, req: dict[str, Any], profile: CustomerProfile) -> bool:
        """Determine if a requirement is relevant for the given profile."""
        ...


class DataTypeRelevanceStrategy(RelevanceStrategy):
    """Check relevance based on data type overlap."""

    def is_relevant(self, req: dict[str, Any], profile: CustomerProfile) -> bool:
        profile_data_types = set(profile.data_types_processed)
        req_data_types = set(req.get("data_types", []))
        return bool(req_data_types & profile_data_types)


class ProcessRelevanceStrategy(RelevanceStrategy):
    """Check relevance based on business process overlap."""

    def is_relevant(self, req: dict[str, Any], profile: CustomerProfile) -> bool:
        profile_processes = set(profile.business_processes)
        req_processes = set(req.get("processes", []))
        return bool(req_processes & profile_processes)


class PIIRelevanceStrategy(RelevanceStrategy):
    """Check relevance for PII-related requirements."""

    PII_CATEGORIES = frozenset({
        "data_collection",
        "data_storage",
        "data_processing",
        "consent",
        "data_deletion",
    })

    def is_relevant(self, req: dict[str, Any], profile: CustomerProfile) -> bool:
        if not profile.processes_pii:
            return False
        category = req.get("category", "").lower()
        return category in self.PII_CATEGORIES


class HealthDataRelevanceStrategy(RelevanceStrategy):
    """Check relevance for health data requirements."""

    HEALTH_CATEGORIES = frozenset({"data_storage", "security", "audit"})

    def is_relevant(self, req: dict[str, Any], profile: CustomerProfile) -> bool:
        if not profile.processes_health_data:
            return False
        category = req.get("category", "").lower()
        return category in self.HEALTH_CATEGORIES


class AIMLRelevanceStrategy(RelevanceStrategy):
    """Check relevance for AI/ML-related requirements."""

    def is_relevant(self, req: dict[str, Any], profile: CustomerProfile) -> bool:
        if not profile.uses_ai_ml:
            return False
        category = req.get("category", "").lower()
        return category.startswith("ai_")


class RelevanceFilter:
    """Filters requirements based on relevance to customer profile.
    
    Uses Strategy pattern to allow extensible filtering rules.
    """

    def __init__(self, strategies: list[RelevanceStrategy] | None = None):
        """Initialize with filtering strategies.
        
        Args:
            strategies: List of relevance strategies. If None, uses default strategies.
        """
        self._strategies = strategies or self._default_strategies()

    @staticmethod
    def _default_strategies() -> list[RelevanceStrategy]:
        """Create default set of relevance strategies."""
        return [
            DataTypeRelevanceStrategy(),
            ProcessRelevanceStrategy(),
            PIIRelevanceStrategy(),
            HealthDataRelevanceStrategy(),
            AIMLRelevanceStrategy(),
        ]

    def filter(
        self,
        requirements: list[dict[str, Any]],
        profile: CustomerProfile,
    ) -> list[dict[str, Any]]:
        """Filter requirements for relevance to customer profile."""
        relevant = []

        for req in requirements:
            # A requirement is relevant if ANY strategy matches
            for strategy in self._strategies:
                if strategy.is_relevant(req, profile):
                    relevant.append(req)
                    break

        logger.info(
            "Filtered requirements for relevance",
            total=len(requirements),
            relevant=len(relevant),
        )
        return relevant

    def add_strategy(self, strategy: RelevanceStrategy) -> None:
        """Add a custom relevance strategy."""
        self._strategies.append(strategy)
