"""Tests for RelevanceFilter strategies and composition."""

from unittest.mock import MagicMock

import pytest

from app.agents.relevance_filter import (
    AIMLRelevanceStrategy,
    DataTypeRelevanceStrategy,
    HealthDataRelevanceStrategy,
    PIIRelevanceStrategy,
    ProcessRelevanceStrategy,
    RelevanceFilter,
    RelevanceStrategy,
)


def _make_profile(**overrides) -> MagicMock:
    """Create a mock CustomerProfile with sensible defaults."""
    profile = MagicMock()
    profile.data_types_processed = overrides.get("data_types_processed", [])
    profile.business_processes = overrides.get("business_processes", [])
    profile.processes_pii = overrides.get("processes_pii", False)
    profile.processes_health_data = overrides.get("processes_health_data", False)
    profile.uses_ai_ml = overrides.get("uses_ai_ml", False)
    return profile


# ---------------------------------------------------------------------------
# DataTypeRelevanceStrategy
# ---------------------------------------------------------------------------


class TestDataTypeRelevanceStrategy:
    strategy = DataTypeRelevanceStrategy()

    def test_matching_data_types(self):
        profile = _make_profile(data_types_processed=["personal data", "financial"])
        req = {"data_types": ["personal data", "health"]}
        assert self.strategy.is_relevant(req, profile) is True

    def test_no_overlap(self):
        profile = _make_profile(data_types_processed=["financial"])
        req = {"data_types": ["personal data"]}
        assert self.strategy.is_relevant(req, profile) is False

    def test_empty_req_data_types(self):
        profile = _make_profile(data_types_processed=["personal data"])
        req = {"data_types": []}
        assert self.strategy.is_relevant(req, profile) is False

    def test_missing_data_types_key(self):
        profile = _make_profile(data_types_processed=["personal data"])
        req = {}
        assert self.strategy.is_relevant(req, profile) is False

    def test_empty_profile_data_types(self):
        profile = _make_profile(data_types_processed=[])
        req = {"data_types": ["personal data"]}
        assert self.strategy.is_relevant(req, profile) is False


# ---------------------------------------------------------------------------
# ProcessRelevanceStrategy
# ---------------------------------------------------------------------------


class TestProcessRelevanceStrategy:
    strategy = ProcessRelevanceStrategy()

    def test_matching_processes(self):
        profile = _make_profile(business_processes=["data_collection", "marketing"])
        req = {"processes": ["data_collection"]}
        assert self.strategy.is_relevant(req, profile) is True

    def test_no_overlap(self):
        profile = _make_profile(business_processes=["marketing"])
        req = {"processes": ["data_deletion"]}
        assert self.strategy.is_relevant(req, profile) is False

    def test_missing_processes_key(self):
        profile = _make_profile(business_processes=["marketing"])
        req = {}
        assert self.strategy.is_relevant(req, profile) is False


# ---------------------------------------------------------------------------
# PIIRelevanceStrategy
# ---------------------------------------------------------------------------


class TestPIIRelevanceStrategy:
    strategy = PIIRelevanceStrategy()

    def test_pii_profile_matching_category(self):
        profile = _make_profile(processes_pii=True)
        req = {"category": "data_collection"}
        assert self.strategy.is_relevant(req, profile) is True

    def test_pii_profile_non_matching_category(self):
        profile = _make_profile(processes_pii=True)
        req = {"category": "networking"}
        assert self.strategy.is_relevant(req, profile) is False

    def test_non_pii_profile(self):
        profile = _make_profile(processes_pii=False)
        req = {"category": "data_collection"}
        assert self.strategy.is_relevant(req, profile) is False

    def test_case_insensitive_category(self):
        profile = _make_profile(processes_pii=True)
        req = {"category": "Data_Storage"}
        assert self.strategy.is_relevant(req, profile) is True

    def test_all_pii_categories(self):
        profile = _make_profile(processes_pii=True)
        for cat in ["data_collection", "data_storage", "data_processing", "consent", "data_deletion"]:
            assert self.strategy.is_relevant({"category": cat}, profile) is True

    def test_missing_category_key(self):
        profile = _make_profile(processes_pii=True)
        req = {}
        assert self.strategy.is_relevant(req, profile) is False


# ---------------------------------------------------------------------------
# HealthDataRelevanceStrategy
# ---------------------------------------------------------------------------


class TestHealthDataRelevanceStrategy:
    strategy = HealthDataRelevanceStrategy()

    def test_health_profile_matching_category(self):
        profile = _make_profile(processes_health_data=True)
        req = {"category": "security"}
        assert self.strategy.is_relevant(req, profile) is True

    def test_health_profile_non_matching_category(self):
        profile = _make_profile(processes_health_data=True)
        req = {"category": "marketing"}
        assert self.strategy.is_relevant(req, profile) is False

    def test_non_health_profile(self):
        profile = _make_profile(processes_health_data=False)
        req = {"category": "security"}
        assert self.strategy.is_relevant(req, profile) is False

    def test_all_health_categories(self):
        profile = _make_profile(processes_health_data=True)
        for cat in ["data_storage", "security", "audit"]:
            assert self.strategy.is_relevant({"category": cat}, profile) is True


# ---------------------------------------------------------------------------
# AIMLRelevanceStrategy
# ---------------------------------------------------------------------------


class TestAIMLRelevanceStrategy:
    strategy = AIMLRelevanceStrategy()

    def test_ai_profile_ai_category(self):
        profile = _make_profile(uses_ai_ml=True)
        req = {"category": "ai_transparency"}
        assert self.strategy.is_relevant(req, profile) is True

    def test_ai_profile_non_ai_category(self):
        profile = _make_profile(uses_ai_ml=True)
        req = {"category": "data_storage"}
        assert self.strategy.is_relevant(req, profile) is False

    def test_non_ai_profile(self):
        profile = _make_profile(uses_ai_ml=False)
        req = {"category": "ai_transparency"}
        assert self.strategy.is_relevant(req, profile) is False

    def test_ai_prefix_variations(self):
        profile = _make_profile(uses_ai_ml=True)
        for cat in ["ai_bias", "ai_governance", "ai_safety"]:
            assert self.strategy.is_relevant({"category": cat}, profile) is True

    def test_category_not_starting_with_ai(self):
        profile = _make_profile(uses_ai_ml=True)
        req = {"category": "fair_ai"}  # contains "ai" but doesn't start with "ai_"
        assert self.strategy.is_relevant(req, profile) is False


# ---------------------------------------------------------------------------
# RelevanceFilter (composition)
# ---------------------------------------------------------------------------


class TestRelevanceFilter:
    def test_default_strategies_populated(self):
        f = RelevanceFilter()
        assert len(f._strategies) == 5

    def test_filters_matching_requirements(self):
        profile = _make_profile(data_types_processed=["personal data"])
        reqs = [
            {"data_types": ["personal data"], "id": "match"},
            {"data_types": ["financial"], "id": "no-match"},
        ]
        result = RelevanceFilter().filter(reqs, profile)
        assert len(result) == 1
        assert result[0]["id"] == "match"

    def test_any_strategy_match_is_sufficient(self):
        profile = _make_profile(
            data_types_processed=[],
            processes_pii=True,
        )
        req = {"category": "consent", "data_types": []}
        result = RelevanceFilter().filter([req], profile)
        assert len(result) == 1

    def test_empty_requirements_list(self):
        profile = _make_profile(data_types_processed=["personal data"])
        result = RelevanceFilter().filter([], profile)
        assert result == []

    def test_no_matching_requirements(self):
        profile = _make_profile()  # empty profile
        reqs = [{"data_types": ["personal data"], "category": "marketing"}]
        result = RelevanceFilter().filter(reqs, profile)
        assert result == []

    def test_add_custom_strategy(self):
        class AlwaysRelevant(RelevanceStrategy):
            def is_relevant(self, req, profile):
                return True

        f = RelevanceFilter(strategies=[])
        f.add_strategy(AlwaysRelevant())
        result = f.filter([{"id": "test"}], _make_profile())
        assert len(result) == 1

    def test_requirement_matched_by_multiple_strategies_not_duplicated(self):
        profile = _make_profile(
            data_types_processed=["personal data"],
            processes_pii=True,
        )
        req = {"data_types": ["personal data"], "category": "data_collection"}
        result = RelevanceFilter().filter([req], profile)
        assert len(result) == 1  # should not be duplicated
