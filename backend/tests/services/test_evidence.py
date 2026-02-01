"""Tests for evidence collection service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.evidence import (
    EvidenceCollector,
    EvidenceItem,
    ControlMapping,
    EvidenceExport,
    ControlFramework,
)

pytestmark = pytest.mark.asyncio


class TestEvidenceCollector:
    """Test suite for EvidenceCollector."""

    @pytest.fixture
    def collector(self):
        """Create EvidenceCollector instance."""
        return EvidenceCollector()

    def test_list_supported_frameworks(self, collector):
        """Test listing supported control frameworks."""
        frameworks = collector.list_supported_frameworks()
        
        assert len(frameworks) >= 4
        framework_ids = [f.framework_id for f in frameworks]
        assert "soc2" in framework_ids
        assert "iso27001" in framework_ids
        assert "hipaa" in framework_ids
        assert "pci-dss" in framework_ids

    def test_get_framework_controls(self, collector):
        """Test getting controls for a framework."""
        controls = collector.get_framework_controls("soc2")
        
        assert len(controls) >= 1
        for control in controls:
            assert "control_id" in control
            assert "title" in control
            assert "description" in control

    async def test_collect_evidence_for_control(self, collector):
        """Test collecting evidence for a specific control."""
        with patch.object(collector, "_gather_evidence_sources") as mock_gather:
            mock_gather.return_value = [
                EvidenceItem(
                    evidence_id="EV-001",
                    control_id="CC6.1",
                    framework="soc2",
                    title="Access Control Policy",
                    description="Documentation of access control policy",
                    evidence_type="documentation",
                    source="policy_repository",
                    collected_at=datetime.utcnow(),
                    status="verified",
                ),
            ]
            
            evidence = await collector.collect_for_control(
                framework="soc2",
                control_id="CC6.1",
            )
            
            assert len(evidence) >= 1
            assert evidence[0].control_id == "CC6.1"

    async def test_collect_evidence_for_framework(self, collector):
        """Test collecting evidence for entire framework."""
        with patch.object(collector, "collect_for_control") as mock_collect:
            mock_collect.return_value = [
                EvidenceItem(
                    evidence_id="EV-001",
                    control_id="CC6.1",
                    framework="soc2",
                    title="Test Evidence",
                    description="Test",
                    evidence_type="documentation",
                    source="test",
                    collected_at=datetime.utcnow(),
                    status="verified",
                ),
            ]
            
            result = await collector.collect_for_framework("soc2")
            
            assert "evidence" in result
            assert "coverage" in result

    async def test_map_code_to_controls(self, collector):
        """Test mapping code artifacts to controls."""
        code_artifacts = [
            {
                "file": "src/auth/login.py",
                "type": "authentication",
                "functions": ["authenticate_user", "validate_mfa"],
            },
            {
                "file": "src/logging/audit.py",
                "type": "audit_logging",
                "functions": ["log_event", "log_access"],
            },
        ]
        
        with patch.object(collector, "_analyze_code_for_controls") as mock_analyze:
            mock_analyze.return_value = [
                ControlMapping(
                    control_id="CC6.1",
                    framework="soc2",
                    code_artifacts=["src/auth/login.py"],
                    compliance_status="compliant",
                    confidence=0.85,
                ),
                ControlMapping(
                    control_id="CC7.2",
                    framework="soc2",
                    code_artifacts=["src/logging/audit.py"],
                    compliance_status="compliant",
                    confidence=0.92,
                ),
            ]
            
            mappings = await collector.map_code_to_controls(
                framework="soc2",
                code_artifacts=code_artifacts,
            )
            
            assert len(mappings) >= 2

    async def test_generate_audit_report(self, collector):
        """Test generating audit report."""
        with patch.object(collector, "collect_for_framework") as mock_collect:
            mock_collect.return_value = {
                "evidence": [
                    EvidenceItem(
                        evidence_id="EV-001",
                        control_id="CC6.1",
                        framework="soc2",
                        title="Test Evidence",
                        description="Test",
                        evidence_type="documentation",
                        source="test",
                        collected_at=datetime.utcnow(),
                        status="verified",
                    ),
                ],
                "coverage": {"total_controls": 10, "covered_controls": 8},
            }
            
            report = await collector.generate_audit_report(
                framework="soc2",
                report_format="pdf",
            )
            
            assert report is not None
            assert "report_id" in report

    async def test_export_evidence(self, collector):
        """Test exporting evidence."""
        evidence_items = [
            EvidenceItem(
                evidence_id="EV-001",
                control_id="CC6.1",
                framework="soc2",
                title="Test Evidence",
                description="Test description",
                evidence_type="documentation",
                source="test",
                collected_at=datetime.utcnow(),
                status="verified",
            ),
        ]
        
        export = await collector.export_evidence(
            evidence=evidence_items,
            export_format="json",
        )
        
        assert export is not None
        assert isinstance(export, EvidenceExport)
        assert export.format == "json"

    async def test_export_evidence_csv(self, collector):
        """Test exporting evidence as CSV."""
        evidence_items = [
            EvidenceItem(
                evidence_id="EV-001",
                control_id="CC6.1",
                framework="soc2",
                title="Test Evidence",
                description="Test",
                evidence_type="documentation",
                source="test",
                collected_at=datetime.utcnow(),
                status="verified",
            ),
        ]
        
        export = await collector.export_evidence(
            evidence=evidence_items,
            export_format="csv",
        )
        
        assert export.format == "csv"
        assert export.content is not None

    def test_get_control_mapping_template(self, collector):
        """Test getting control mapping template."""
        template = collector.get_control_mapping_template("soc2")
        
        assert template is not None
        assert "controls" in template
        assert "mapping_fields" in template

    async def test_verify_evidence(self, collector):
        """Test verifying evidence validity."""
        evidence = EvidenceItem(
            evidence_id="EV-001",
            control_id="CC6.1",
            framework="soc2",
            title="Test Evidence",
            description="Test",
            evidence_type="documentation",
            source="test",
            collected_at=datetime.utcnow(),
            status="pending",
        )
        
        with patch.object(collector, "_validate_evidence") as mock_validate:
            mock_validate.return_value = {
                "is_valid": True,
                "issues": [],
                "confidence": 0.95,
            }
            
            result = await collector.verify_evidence(evidence)
            
            assert result["is_valid"] is True

    async def test_get_coverage_report(self, collector):
        """Test getting coverage report."""
        with patch.object(collector, "_calculate_coverage") as mock_coverage:
            mock_coverage.return_value = {
                "framework": "soc2",
                "total_controls": 50,
                "covered_controls": 42,
                "coverage_percentage": 84.0,
                "gaps": [
                    {"control_id": "CC8.1", "status": "not_covered"},
                ],
            }
            
            report = await collector.get_coverage_report("soc2")
            
            assert report["coverage_percentage"] == 84.0
            assert len(report["gaps"]) >= 1


class TestEvidenceItem:
    """Test EvidenceItem dataclass."""

    def test_evidence_item_creation(self):
        """Test creating an evidence item."""
        item = EvidenceItem(
            evidence_id="EV-001",
            control_id="CC6.1",
            framework="soc2",
            title="Access Policy",
            description="Access control policy document",
            evidence_type="documentation",
            source="policy_repo",
            collected_at=datetime.utcnow(),
            status="verified",
        )
        
        assert item.evidence_id == "EV-001"
        assert item.control_id == "CC6.1"
        assert item.status == "verified"

    def test_evidence_item_to_dict(self):
        """Test converting evidence item to dict."""
        item = EvidenceItem(
            evidence_id="EV-002",
            control_id="CC7.1",
            framework="soc2",
            title="Test",
            description="Test description",
            evidence_type="screenshot",
            source="manual",
            collected_at=datetime(2024, 1, 15),
            status="pending",
        )
        
        item_dict = item.to_dict()
        
        assert item_dict["evidence_id"] == "EV-002"
        assert item_dict["evidence_type"] == "screenshot"


class TestControlMapping:
    """Test ControlMapping dataclass."""

    def test_control_mapping_creation(self):
        """Test creating a control mapping."""
        mapping = ControlMapping(
            control_id="CC6.1",
            framework="soc2",
            code_artifacts=["src/auth.py", "src/mfa.py"],
            compliance_status="compliant",
            confidence=0.9,
        )
        
        assert mapping.control_id == "CC6.1"
        assert len(mapping.code_artifacts) == 2
        assert mapping.confidence == 0.9

    def test_control_mapping_to_dict(self):
        """Test converting control mapping to dict."""
        mapping = ControlMapping(
            control_id="CC7.2",
            framework="soc2",
            code_artifacts=["src/logging.py"],
            compliance_status="partial",
            confidence=0.75,
        )
        
        mapping_dict = mapping.to_dict()
        
        assert mapping_dict["compliance_status"] == "partial"


class TestControlFramework:
    """Test ControlFramework dataclass."""

    def test_framework_creation(self):
        """Test creating a control framework."""
        framework = ControlFramework(
            framework_id="soc2",
            name="SOC 2 Type II",
            description="Service Organization Control 2",
            version="2017",
            total_controls=50,
        )
        
        assert framework.framework_id == "soc2"
        assert framework.total_controls == 50


class TestEvidenceExport:
    """Test EvidenceExport dataclass."""

    def test_export_creation(self):
        """Test creating an export."""
        export = EvidenceExport(
            export_id="EXP-001",
            format="json",
            content='{"evidence": []}',
            created_at=datetime.utcnow(),
            framework="soc2",
        )
        
        assert export.format == "json"
        assert export.framework == "soc2"
