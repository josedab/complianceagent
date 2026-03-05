"""Tests for CustomerProfile.get_applicable_frameworks."""

from unittest.mock import MagicMock, patch

import pytest

from app.models.regulation import RegulatoryFramework


def _make_profile(**overrides):
    """Create a mock CustomerProfile with sensible defaults."""
    profile = MagicMock()
    profile.applicable_frameworks = overrides.get("applicable_frameworks", [])
    profile.excluded_frameworks = overrides.get("excluded_frameworks", [])
    profile.operating_jurisdictions = overrides.get("operating_jurisdictions", [])
    profile.customer_jurisdictions = overrides.get("customer_jurisdictions", [])
    profile.processes_health_data = overrides.get("processes_health_data", False)
    profile.processes_financial_data = overrides.get("processes_financial_data", False)
    profile.is_publicly_traded = overrides.get("is_publicly_traded", False)
    profile.uses_ai_ml = overrides.get("uses_ai_ml", False)
    return profile


def _call_get_applicable_frameworks(profile):
    """Call the real method on a mock profile."""
    from app.models.customer_profile import CustomerProfile
    return CustomerProfile.get_applicable_frameworks(profile)


class TestJurisdictionInference:
    def test_eu_jurisdiction_adds_gdpr(self):
        profile = _make_profile(operating_jurisdictions=["eu"])
        result = _call_get_applicable_frameworks(profile)
        values = [f.value for f in result]
        assert "gdpr" in values

    def test_uk_jurisdiction_adds_gdpr_and_uk_gdpr(self):
        profile = _make_profile(operating_jurisdictions=["uk"])
        result = _call_get_applicable_frameworks(profile)
        values = [f.value for f in result]
        assert "gdpr" in values
        assert "uk_gdpr" in values

    def test_us_california_adds_ccpa_and_cpra(self):
        profile = _make_profile(customer_jurisdictions=["us_california"])
        result = _call_get_applicable_frameworks(profile)
        values = [f.value for f in result]
        assert "ccpa" in values
        assert "cpra" in values

    def test_no_jurisdictions_no_frameworks(self):
        profile = _make_profile()
        result = _call_get_applicable_frameworks(profile)
        assert result == []


class TestDataTypeInference:
    def test_health_data_adds_hipaa(self):
        profile = _make_profile(processes_health_data=True)
        result = _call_get_applicable_frameworks(profile)
        values = [f.value for f in result]
        assert "hipaa" in values

    def test_financial_data_adds_pci_dss(self):
        profile = _make_profile(processes_financial_data=True)
        result = _call_get_applicable_frameworks(profile)
        values = [f.value for f in result]
        assert "pci_dss" in values

    def test_financial_and_publicly_traded_adds_sox(self):
        profile = _make_profile(processes_financial_data=True, is_publicly_traded=True)
        result = _call_get_applicable_frameworks(profile)
        values = [f.value for f in result]
        assert "sox" in values
        assert "pci_dss" in values

    def test_financial_not_publicly_traded_no_sox(self):
        profile = _make_profile(processes_financial_data=True, is_publicly_traded=False)
        result = _call_get_applicable_frameworks(profile)
        values = [f.value for f in result]
        assert "sox" not in values


class TestAIInference:
    def test_ai_in_eu_adds_eu_ai_act(self):
        profile = _make_profile(uses_ai_ml=True, operating_jurisdictions=["eu"])
        result = _call_get_applicable_frameworks(profile)
        values = [f.value for f in result]
        assert "eu_ai_act" in values

    def test_ai_outside_eu_no_eu_ai_act(self):
        profile = _make_profile(uses_ai_ml=True, operating_jurisdictions=["us_federal"])
        result = _call_get_applicable_frameworks(profile)
        values = [f.value for f in result]
        assert "eu_ai_act" not in values

    def test_no_ai_in_eu_no_eu_ai_act(self):
        profile = _make_profile(uses_ai_ml=False, operating_jurisdictions=["eu"])
        result = _call_get_applicable_frameworks(profile)
        values = [f.value for f in result]
        assert "eu_ai_act" not in values


class TestExplicitFrameworks:
    def test_explicit_framework_added(self):
        profile = _make_profile(applicable_frameworks=["soc2"])
        result = _call_get_applicable_frameworks(profile)
        values = [f.value for f in result]
        assert "soc2" in values

    def test_excluded_framework_removed(self):
        profile = _make_profile(
            operating_jurisdictions=["eu"],
            excluded_frameworks=["gdpr"],
        )
        result = _call_get_applicable_frameworks(profile)
        values = [f.value for f in result]
        assert "gdpr" not in values


class TestCombinedProfile:
    def test_complex_profile(self):
        profile = _make_profile(
            operating_jurisdictions=["eu", "us_california"],
            processes_health_data=True,
            processes_financial_data=True,
            is_publicly_traded=True,
            uses_ai_ml=True,
            applicable_frameworks=["soc2"],
            excluded_frameworks=["cpra"],
        )
        result = _call_get_applicable_frameworks(profile)
        values = [f.value for f in result]
        assert "gdpr" in values
        assert "ccpa" in values
        assert "cpra" not in values  # excluded
        assert "hipaa" in values
        assert "pci_dss" in values
        assert "sox" in values
        assert "eu_ai_act" in values
        assert "soc2" in values
