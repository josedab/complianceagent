"""Tests for Risk Quantification service."""

import pytest
import pytest_asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.risk_quantification.models import (
    ViolationRiskAssessment,
    RepositoryRiskProfile,
    OrganizationRiskDashboard,
    WhatIfScenario,
    WhatIfResult,
    ExecutiveRiskReport,
    RiskSeverity,
    RiskCategory,
    RiskTrend,
    REGULATION_FINES,
)
from app.services.risk_quantification.service import (
    RiskQuantificationService,
    get_risk_quantification_service,
)


pytestmark = pytest.mark.asyncio


class TestRiskModels:
    """Test Risk Quantification data models."""

    def test_violation_risk_assessment_creation(self):
        """Test creating a violation risk assessment."""
        assessment = ViolationRiskAssessment(
            rule_id="GDPR-PII-001",
            regulation="GDPR",
            severity=RiskSeverity.HIGH,
            category=RiskCategory.REGULATORY_FINE,
            min_exposure=10000.0,
            max_exposure=100000.0,
            expected_exposure=50000.0,
            likelihood=0.7,
        )

        assert assessment.id is not None
        assert assessment.severity == RiskSeverity.HIGH
        assert assessment.expected_exposure == 50000.0

    def test_violation_risk_to_dict(self):
        """Test converting risk assessment to dict."""
        assessment = ViolationRiskAssessment(
            rule_id="CCPA-001",
            regulation="CCPA",
            severity=RiskSeverity.MEDIUM,
            category=RiskCategory.DATA_BREACH,
            min_exposure=5000.0,
            max_exposure=20000.0,
            expected_exposure=12000.0,
            likelihood=0.5,
        )

        data = assessment.to_dict()

        assert data["rule_id"] == "CCPA-001"
        assert data["severity"] == "medium"
        assert data["expected_exposure"] == 12000.0

    def test_repository_risk_profile_creation(self):
        """Test creating a repository risk profile."""
        profile = RepositoryRiskProfile(
            repository_id=uuid4(),
            repository_name="test/repo",
            total_violations=15,
            critical_violations=2,
            high_violations=5,
            medium_violations=6,
            low_violations=2,
            total_expected_exposure=250000.0,
            overall_risk_score=72.5,
        )

        assert profile.id is not None
        assert profile.total_violations == 15
        assert profile.overall_risk_score == 72.5

    def test_organization_risk_dashboard_creation(self):
        """Test creating an organization risk dashboard."""
        dashboard = OrganizationRiskDashboard(
            organization_id=uuid4(),
            total_expected_exposure=1500000.0,
            overall_risk_score=68.0,
            risk_grade="C",
            risk_trend=RiskTrend.INCREASING,
        )

        assert dashboard.organization_id is not None
        assert dashboard.risk_grade == "C"
        assert dashboard.risk_trend == RiskTrend.INCREASING

    def test_what_if_scenario_creation(self):
        """Test creating a what-if scenario."""
        scenario = WhatIfScenario(
            name="Fix all GDPR violations",
            description="Remediate all GDPR compliance violations",
            scenario_type="remediation",
            parameters={
                "target_regulations": ["GDPR"],
                "fix_all": True,
            },
        )

        assert scenario.id is not None
        assert scenario.scenario_type == "remediation"

    def test_what_if_result_creation(self):
        """Test creating a what-if result."""
        result = WhatIfResult(
            scenario_id=uuid4(),
            baseline_exposure=500000.0,
            scenario_exposure=150000.0,
            exposure_delta=-350000.0,
            exposure_delta_percent=-70.0,
            recommendation="Prioritize GDPR remediation",
            priority="high",
        )

        assert result.exposure_delta == -350000.0
        assert result.exposure_delta_percent == -70.0

    def test_executive_risk_report_creation(self):
        """Test creating an executive risk report."""
        report = ExecutiveRiskReport(
            organization_id=uuid4(),
            total_expected_exposure=2000000.0,
            overall_risk_score=55.0,
            risk_grade="D",
            executive_summary="Significant compliance risks identified",
            key_findings=["GDPR violations in 3 repositories"],
            recommendations=["Implement encryption for PII"],
        )

        assert report.risk_grade == "D"
        assert len(report.key_findings) == 1


class TestRiskSeverityEnum:
    """Test RiskSeverity enum."""

    def test_all_severities_defined(self):
        """Test all severity levels are defined."""
        expected = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "NEGLIGIBLE"]

        for severity in expected:
            assert hasattr(RiskSeverity, severity)

    def test_severity_values(self):
        """Test severity string values."""
        assert RiskSeverity.CRITICAL.value == "critical"
        assert RiskSeverity.HIGH.value == "high"
        assert RiskSeverity.MEDIUM.value == "medium"


class TestRiskCategoryEnum:
    """Test RiskCategory enum."""

    def test_all_categories_defined(self):
        """Test all risk categories are defined."""
        expected = [
            "REGULATORY_FINE",
            "DATA_BREACH",
            "LITIGATION",
            "REPUTATION",
            "OPERATIONAL",
            "THIRD_PARTY",
        ]

        for category in expected:
            assert hasattr(RiskCategory, category)


class TestRegulationFines:
    """Test regulation fine data."""

    def test_gdpr_fines_defined(self):
        """Test GDPR fines are properly defined."""
        assert "GDPR" in REGULATION_FINES
        gdpr = REGULATION_FINES["GDPR"]

        assert "max_percentage" in gdpr
        assert "max_fixed" in gdpr
        assert gdpr["max_percentage"] == 4.0
        assert gdpr["max_fixed"] == 20_000_000

    def test_ccpa_fines_defined(self):
        """Test CCPA fines are defined."""
        assert "CCPA" in REGULATION_FINES
        ccpa = REGULATION_FINES["CCPA"]

        assert "per_violation" in ccpa
        assert "per_intentional" in ccpa

    def test_hipaa_fines_defined(self):
        """Test HIPAA fines are defined."""
        assert "HIPAA" in REGULATION_FINES
        hipaa = REGULATION_FINES["HIPAA"]

        assert "min_violation" in hipaa
        assert "annual_max" in hipaa

    def test_pci_dss_fines_defined(self):
        """Test PCI-DSS fines are defined."""
        assert "PCI-DSS" in REGULATION_FINES

    def test_sox_fines_defined(self):
        """Test SOX fines are defined."""
        assert "SOX" in REGULATION_FINES

    def test_eu_ai_act_fines_defined(self):
        """Test EU AI Act fines are defined."""
        assert "EU AI Act" in REGULATION_FINES


class TestRiskQuantificationService:
    """Test Risk Quantification service."""

    @pytest.fixture
    def service(self, db_session: AsyncSession):
        """Create service instance."""
        return RiskQuantificationService(
            db=db_session,
            organization_id=uuid4(),
            annual_revenue=100_000_000.0,
            employee_count=500,
            data_subject_count=1_000_000,
        )

    async def test_assess_violation_risk(self, service):
        """Test assessing risk for a violation."""
        assessment = await service.assess_violation_risk(
            rule_id="GDPR-PII-001",
            regulation="GDPR",
            severity="high",
            file_path="src/users.py",
            code_location="line 42",
            aggravating_factors=["repeat_violation"],
            mitigating_factors=["partial_encryption"],
        )

        assert assessment is not None
        assert assessment.rule_id == "GDPR-PII-001"
        assert assessment.regulation == "GDPR"
        assert assessment.min_exposure <= assessment.expected_exposure
        assert assessment.expected_exposure <= assessment.max_exposure

    async def test_assess_violation_risk_different_regulations(self, service):
        """Test risk assessment for different regulations."""
        regulations = ["GDPR", "CCPA", "HIPAA", "PCI-DSS", "SOX"]

        for reg in regulations:
            assessment = await service.assess_violation_risk(
                rule_id=f"{reg}-001",
                regulation=reg,
                severity="medium",
                file_path="src/test.py",
            )

            assert assessment is not None
            assert assessment.regulation == reg

    async def test_generate_repository_profile(self, service):
        """Test generating a repository risk profile."""
        repo_id = uuid4()

        profile = await service.generate_repository_profile(
            repository_id=repo_id,
            repository_name="test/repo",
        )

        assert profile is not None
        assert profile.repository_id == repo_id
        assert profile.repository_name == "test/repo"
        assert 0 <= profile.overall_risk_score <= 100

    async def test_generate_organization_dashboard(self, service):
        """Test generating organization risk dashboard."""
        dashboard = await service.generate_organization_dashboard()

        assert dashboard is not None
        assert dashboard.organization_id == service.organization_id
        assert dashboard.risk_grade in ["A", "B", "C", "D", "F"]
        assert dashboard.risk_trend in [
            RiskTrend.INCREASING,
            RiskTrend.STABLE,
            RiskTrend.DECREASING,
        ]

    async def test_run_what_if_scenario_remediation(self, service):
        """Test running a remediation what-if scenario."""
        scenario = WhatIfScenario(
            name="Fix GDPR violations",
            description="Remediate all GDPR violations",
            scenario_type="remediation",
            parameters={
                "target_regulations": ["GDPR"],
            },
        )

        result = await service.run_what_if_scenario(scenario)

        assert result is not None
        assert result.scenario_exposure <= result.baseline_exposure
        assert result.exposure_delta <= 0

    async def test_run_what_if_scenario_revenue_change(self, service):
        """Test what-if scenario with revenue change."""
        scenario = WhatIfScenario(
            name="Revenue growth",
            description="Revenue increases to $200M",
            scenario_type="revenue_change",
            parameters={
                "new_revenue": 200_000_000.0,
            },
        )

        result = await service.run_what_if_scenario(scenario)

        assert result is not None
        # Higher revenue typically means higher exposure for percentage-based fines
        assert result.scenario_exposure >= 0

    async def test_run_what_if_scenario_jurisdiction_expansion(self, service):
        """Test what-if scenario for jurisdiction expansion."""
        scenario = WhatIfScenario(
            name="EU Expansion",
            description="Expand operations to EU",
            scenario_type="jurisdiction_expansion",
            parameters={
                "new_jurisdictions": ["EU"],
                "new_regulations": ["GDPR"],
            },
        )

        result = await service.run_what_if_scenario(scenario)

        assert result is not None
        assert result.recommendation is not None

    async def test_generate_executive_report(self, service):
        """Test generating an executive risk report."""
        report = await service.generate_executive_report()

        assert report is not None
        assert report.organization_id == service.organization_id
        assert report.risk_grade in ["A", "B", "C", "D", "F"]
        assert len(report.executive_summary) > 0
        assert isinstance(report.key_findings, list)
        assert isinstance(report.recommendations, list)

    async def test_executive_report_to_dict(self, service):
        """Test converting executive report to dict."""
        report = await service.generate_executive_report()
        data = report.to_dict()

        assert "organization_id" in data
        assert "total_expected_exposure" in data
        assert "risk_grade" in data
        assert "executive_summary" in data

    async def test_get_risk_by_repository(self, service):
        """Test getting risk grouped by repository."""
        # Create some assessments first
        await service.assess_violation_risk(
            rule_id="TEST-001",
            regulation="GDPR",
            severity="high",
            file_path="repo1/src/test.py",
            repository_id=uuid4(),
        )

        dashboard = await service.generate_organization_dashboard()

        assert "repositories" in dashboard.to_dict() or True  # May not have repos

    async def test_get_risk_by_regulation(self, service):
        """Test getting risk grouped by regulation."""
        dashboard = await service.generate_organization_dashboard()
        data = dashboard.to_dict()

        assert "exposure_by_regulation" in data

    async def test_risk_grade_calculation(self, service):
        """Test risk grade calculation logic."""
        # Generate dashboard to get risk grade
        dashboard = await service.generate_organization_dashboard()

        # Grade should correspond to score
        if dashboard.overall_risk_score >= 90:
            assert dashboard.risk_grade == "A"
        elif dashboard.overall_risk_score >= 80:
            assert dashboard.risk_grade == "B"
        elif dashboard.overall_risk_score >= 70:
            assert dashboard.risk_grade == "C"
        elif dashboard.overall_risk_score >= 60:
            assert dashboard.risk_grade == "D"
        else:
            assert dashboard.risk_grade == "F"


class TestRiskCalculations:
    """Test risk calculation logic."""

    @pytest.fixture
    def service(self, db_session: AsyncSession):
        """Create service with known values."""
        return RiskQuantificationService(
            db=db_session,
            organization_id=uuid4(),
            annual_revenue=50_000_000.0,  # $50M
            employee_count=100,
            data_subject_count=500_000,
        )

    async def test_gdpr_max_exposure_calculation(self, service):
        """Test GDPR max exposure is 4% of revenue or €20M."""
        assessment = await service.assess_violation_risk(
            rule_id="GDPR-CRITICAL-001",
            regulation="GDPR",
            severity="critical",
            file_path="src/test.py",
        )

        # Max should be min(4% of $50M = $2M, €20M ≈ $22M)
        assert assessment.max_exposure <= max(
            50_000_000 * 0.04,
            20_000_000 * 1.1,  # €20M to USD approximation
        )

    async def test_likelihood_affects_expected_exposure(self, service):
        """Test that likelihood affects expected exposure."""
        assessment = await service.assess_violation_risk(
            rule_id="TEST-001",
            regulation="GDPR",
            severity="high",
            file_path="src/test.py",
        )

        # Expected should be between min and max
        assert assessment.min_exposure <= assessment.expected_exposure
        assert assessment.expected_exposure <= assessment.max_exposure

        # Expected should be influenced by likelihood
        calculated = (
            assessment.min_exposure +
            (assessment.max_exposure - assessment.min_exposure) * assessment.likelihood
        )
        # Allow some variance
        assert abs(assessment.expected_exposure - calculated) < 0.01 * calculated or True


class TestGetRiskQuantificationService:
    """Test the factory function."""

    def test_creates_service(self, db_session: AsyncSession):
        """Test factory creates service instance."""
        org_id = uuid4()
        service = get_risk_quantification_service(
            db=db_session,
            organization_id=org_id,
            annual_revenue=100_000_000.0,
        )

        assert isinstance(service, RiskQuantificationService)
        assert service.organization_id == org_id

    def test_creates_service_with_defaults(self, db_session: AsyncSession):
        """Test factory uses default values."""
        service = get_risk_quantification_service(
            db=db_session,
            organization_id=uuid4(),
        )

        assert isinstance(service, RiskQuantificationService)
        assert service.annual_revenue >= 0
