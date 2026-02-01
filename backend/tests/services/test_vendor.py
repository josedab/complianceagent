"""Tests for vendor risk service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.vendor import (
    VendorRiskAssessor,
    VendorAssessment,
    DependencyRisk,
    RiskLevel,
)

pytestmark = pytest.mark.asyncio


class TestVendorRiskAssessor:
    """Test suite for VendorRiskAssessor."""

    @pytest.fixture
    def assessor(self):
        """Create VendorRiskAssessor instance."""
        return VendorRiskAssessor()

    async def test_assess_vendor(self, assessor):
        """Test assessing a vendor."""
        with patch.object(assessor, "_fetch_vendor_data") as mock_fetch:
            mock_fetch.return_value = {
                "name": "Stripe",
                "certifications": ["SOC2", "PCI-DSS", "ISO27001"],
                "data_processing_locations": ["US", "EU"],
                "subprocessors": ["AWS", "Google Cloud"],
            }
            
            assessment = await assessor.assess_vendor(
                vendor_name="Stripe",
                data_types=["payment_data", "pii"],
                regulations=["GDPR", "PCI-DSS"],
            )
            
            assert assessment is not None
            assert assessment.vendor_name == "Stripe"
            assert assessment.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]

    async def test_assess_vendor_high_risk(self, assessor):
        """Test assessing a high-risk vendor."""
        with patch.object(assessor, "_fetch_vendor_data") as mock_fetch:
            mock_fetch.return_value = {
                "name": "UnknownVendor",
                "certifications": [],
                "data_processing_locations": ["Unknown"],
                "subprocessors": [],
            }
            
            assessment = await assessor.assess_vendor(
                vendor_name="UnknownVendor",
                data_types=["health_data", "financial_data"],
                regulations=["HIPAA", "PCI-DSS"],
            )
            
            assert assessment is not None
            assert assessment.risk_level == RiskLevel.HIGH

    async def test_scan_dependencies_npm(self, assessor):
        """Test scanning npm dependencies."""
        package_json = """{
            "dependencies": {
                "lodash": "^4.17.21",
                "express": "^4.18.2",
                "moment": "^2.29.4"
            }
        }"""
        
        with patch.object(assessor, "_check_vulnerability_db") as mock_vuln:
            mock_vuln.return_value = {
                "lodash": {"vulnerabilities": [], "license": "MIT"},
                "express": {"vulnerabilities": [], "license": "MIT"},
                "moment": {
                    "vulnerabilities": [{"id": "CVE-2022-12345", "severity": "medium"}],
                    "license": "MIT",
                },
            }
            
            risks = await assessor.scan_dependencies(
                manifest_content=package_json,
                manifest_type="npm",
                regulations=["SOC2"],
            )
            
            assert len(risks) >= 1
            moment_risks = [r for r in risks if r.package_name == "moment"]
            assert len(moment_risks) >= 1

    async def test_scan_dependencies_pip(self, assessor):
        """Test scanning pip dependencies."""
        requirements_txt = """
        django==4.2.0
        requests==2.31.0
        cryptography==41.0.0
        """
        
        with patch.object(assessor, "_check_vulnerability_db") as mock_vuln:
            mock_vuln.return_value = {
                "django": {"vulnerabilities": [], "license": "BSD"},
                "requests": {"vulnerabilities": [], "license": "Apache-2.0"},
                "cryptography": {"vulnerabilities": [], "license": "Apache-2.0"},
            }
            
            risks = await assessor.scan_dependencies(
                manifest_content=requirements_txt,
                manifest_type="pip",
                regulations=["HIPAA"],
            )
            
            assert isinstance(risks, list)

    async def test_scan_dependencies_with_vulnerabilities(self, assessor):
        """Test scanning dependencies with vulnerabilities."""
        package_json = """{
            "dependencies": {
                "vulnerable-package": "1.0.0"
            }
        }"""
        
        with patch.object(assessor, "_check_vulnerability_db") as mock_vuln:
            mock_vuln.return_value = {
                "vulnerable-package": {
                    "vulnerabilities": [
                        {"id": "CVE-2023-99999", "severity": "critical"},
                        {"id": "CVE-2023-88888", "severity": "high"},
                    ],
                    "license": "MIT",
                },
            }
            
            risks = await assessor.scan_dependencies(
                manifest_content=package_json,
                manifest_type="npm",
                regulations=["SOC2"],
            )
            
            assert len(risks) >= 1
            assert risks[0].risk_level == RiskLevel.HIGH

    async def test_generate_risk_report(self, assessor):
        """Test generating risk report."""
        vendors = ["AWS", "Stripe", "SendGrid"]
        
        with patch.object(assessor, "assess_vendor") as mock_assess:
            mock_assess.side_effect = [
                VendorAssessment(
                    vendor_name="AWS",
                    risk_level=RiskLevel.LOW,
                    certifications=["SOC2", "ISO27001"],
                    issues=[],
                    recommendations=[],
                ),
                VendorAssessment(
                    vendor_name="Stripe",
                    risk_level=RiskLevel.LOW,
                    certifications=["PCI-DSS", "SOC2"],
                    issues=[],
                    recommendations=[],
                ),
                VendorAssessment(
                    vendor_name="SendGrid",
                    risk_level=RiskLevel.MEDIUM,
                    certifications=["SOC2"],
                    issues=["No ISO27001 certification"],
                    recommendations=["Review DPA terms"],
                ),
            ]
            
            report = await assessor.generate_risk_report(
                vendors=vendors,
                regulations=["SOC2", "ISO27001"],
            )
            
            assert "summary" in report
            assert report["summary"]["total_vendors"] == 3
            assert report["summary"]["high_risk"] == 0
            assert report["summary"]["medium_risk"] == 1

    def test_list_supported_manifest_types(self, assessor):
        """Test listing supported manifest types."""
        types = assessor.list_supported_manifest_types()
        
        assert "npm" in types
        assert "pip" in types
        assert "maven" in types or "gradle" in types

    async def test_check_license_compliance(self, assessor):
        """Test checking license compliance."""
        dependencies = [
            {"name": "package-a", "license": "MIT"},
            {"name": "package-b", "license": "Apache-2.0"},
            {"name": "package-c", "license": "GPL-3.0"},
        ]
        
        allowed_licenses = ["MIT", "Apache-2.0", "BSD-3-Clause"]
        
        issues = await assessor.check_license_compliance(
            dependencies=dependencies,
            allowed_licenses=allowed_licenses,
        )
        
        assert len(issues) >= 1
        assert any("GPL-3.0" in str(issue) for issue in issues)


class TestVendorAssessment:
    """Test VendorAssessment dataclass."""

    def test_assessment_creation(self):
        """Test creating an assessment."""
        assessment = VendorAssessment(
            vendor_name="TestVendor",
            risk_level=RiskLevel.MEDIUM,
            certifications=["SOC2"],
            issues=["Missing ISO27001"],
            recommendations=["Request ISO certification"],
        )
        
        assert assessment.vendor_name == "TestVendor"
        assert assessment.risk_level == RiskLevel.MEDIUM
        assert len(assessment.certifications) == 1

    def test_assessment_to_dict(self):
        """Test converting assessment to dict."""
        assessment = VendorAssessment(
            vendor_name="TestVendor",
            risk_level=RiskLevel.LOW,
            certifications=[],
            issues=[],
            recommendations=[],
        )
        
        assessment_dict = assessment.to_dict()
        
        assert assessment_dict["vendor_name"] == "TestVendor"
        assert assessment_dict["risk_level"] == "low"


class TestDependencyRisk:
    """Test DependencyRisk dataclass."""

    def test_dependency_risk_creation(self):
        """Test creating a dependency risk."""
        risk = DependencyRisk(
            package_name="vulnerable-lib",
            version="1.0.0",
            risk_level=RiskLevel.HIGH,
            vulnerabilities=[
                {"id": "CVE-2023-12345", "severity": "critical"},
            ],
            license="MIT",
            recommendations=["Upgrade to version 2.0.0"],
        )
        
        assert risk.package_name == "vulnerable-lib"
        assert risk.risk_level == RiskLevel.HIGH
        assert len(risk.vulnerabilities) == 1

    def test_dependency_risk_to_dict(self):
        """Test converting dependency risk to dict."""
        risk = DependencyRisk(
            package_name="safe-lib",
            version="2.0.0",
            risk_level=RiskLevel.LOW,
            vulnerabilities=[],
            license="MIT",
            recommendations=[],
        )
        
        risk_dict = risk.to_dict()
        
        assert risk_dict["package_name"] == "safe-lib"
        assert risk_dict["risk_level"] == "low"


class TestRiskLevel:
    """Test RiskLevel enum."""

    def test_risk_levels(self):
        """Test risk level values."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_risk_level_comparison(self):
        """Test risk level comparison."""
        # Assuming risk levels can be compared
        assert RiskLevel.LOW != RiskLevel.HIGH
        assert RiskLevel.CRITICAL != RiskLevel.LOW
