"""Tests for compliance sandbox service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.sandbox import (
    ComplianceSandbox,
    SimulationScenario,
    SimulationResult,
    ScenarioType,
)

pytestmark = pytest.mark.asyncio


class TestComplianceSandbox:
    """Test suite for ComplianceSandbox."""

    @pytest.fixture
    def sandbox(self):
        """Create ComplianceSandbox instance."""
        return ComplianceSandbox()

    async def test_simulate_code_change(self, sandbox):
        """Test simulating a code change."""
        scenario = SimulationScenario(
            scenario_type=ScenarioType.CODE_CHANGE,
            description="Add user data export feature",
            parameters={
                "file_path": "src/api/users.py",
                "change_type": "add_function",
                "function_name": "export_user_data",
                "data_types": ["personal_data", "usage_data"],
            },
            regulations=["GDPR", "CCPA"],
        )
        
        with patch.object(sandbox, "_analyze_code_change") as mock_analyze:
            mock_analyze.return_value = SimulationResult(
                scenario_id="test-123",
                status="completed",
                compliance_impact={
                    "GDPR": {"status": "requires_changes", "issues": ["Missing consent check"]},
                    "CCPA": {"status": "compliant", "issues": []},
                },
                recommendations=["Add consent verification before export"],
                estimated_effort_hours=4,
                risk_level="medium",
            )
            
            result = await sandbox.simulate(scenario)
            
            assert result.status == "completed"
            assert "GDPR" in result.compliance_impact
            assert result.risk_level == "medium"

    async def test_simulate_architecture_change(self, sandbox):
        """Test simulating an architecture change."""
        scenario = SimulationScenario(
            scenario_type=ScenarioType.ARCHITECTURE_CHANGE,
            description="Migrate to multi-region deployment",
            parameters={
                "current_architecture": "single-region",
                "target_architecture": "multi-region",
                "regions": ["us-east-1", "eu-west-1", "ap-southeast-1"],
                "data_replication": True,
            },
            regulations=["GDPR", "LGPD"],
        )
        
        with patch.object(sandbox, "_analyze_architecture_change") as mock_analyze:
            mock_analyze.return_value = SimulationResult(
                scenario_id="test-456",
                status="completed",
                compliance_impact={
                    "GDPR": {
                        "status": "requires_changes",
                        "issues": ["Data residency requirements for EU data"],
                    },
                    "LGPD": {
                        "status": "requires_changes", 
                        "issues": ["Brazil data localization requirements"],
                    },
                },
                recommendations=[
                    "Implement data residency controls",
                    "Add region-aware data routing",
                ],
                estimated_effort_hours=40,
                risk_level="high",
            )
            
            result = await sandbox.simulate(scenario)
            
            assert result.status == "completed"
            assert result.risk_level == "high"
            assert len(result.recommendations) >= 2

    async def test_simulate_vendor_change(self, sandbox):
        """Test simulating a vendor change."""
        scenario = SimulationScenario(
            scenario_type=ScenarioType.VENDOR_CHANGE,
            description="Switch from AWS to Azure",
            parameters={
                "current_vendor": "aws",
                "target_vendor": "azure",
                "services_affected": ["storage", "database", "compute"],
            },
            regulations=["SOC2", "ISO27001"],
        )
        
        with patch.object(sandbox, "_analyze_vendor_change") as mock_analyze:
            mock_analyze.return_value = SimulationResult(
                scenario_id="test-789",
                status="completed",
                compliance_impact={
                    "SOC2": {"status": "review_required", "issues": ["New vendor SOC2 attestation needed"]},
                    "ISO27001": {"status": "review_required", "issues": ["Update security controls mapping"]},
                },
                recommendations=["Request Azure SOC2 Type II report"],
                estimated_effort_hours=80,
                risk_level="medium",
            )
            
            result = await sandbox.simulate(scenario)
            
            assert result.status == "completed"
            assert "SOC2" in result.compliance_impact

    async def test_simulate_regulation_change(self, sandbox):
        """Test simulating adoption of new regulation."""
        scenario = SimulationScenario(
            scenario_type=ScenarioType.REGULATION_CHANGE,
            description="Prepare for EU AI Act compliance",
            parameters={
                "new_regulation": "EU_AI_ACT",
                "ai_systems": ["recommendation_engine", "fraud_detection"],
                "risk_category": "high_risk",
            },
            regulations=["EU_AI_ACT"],
        )
        
        with patch.object(sandbox, "_analyze_regulation_change") as mock_analyze:
            mock_analyze.return_value = SimulationResult(
                scenario_id="test-abc",
                status="completed",
                compliance_impact={
                    "EU_AI_ACT": {
                        "status": "requires_changes",
                        "issues": [
                            "Missing AI system documentation",
                            "No human oversight mechanism",
                            "Missing bias testing",
                        ],
                    },
                },
                recommendations=[
                    "Implement model documentation",
                    "Add human review workflow",
                    "Establish bias testing pipeline",
                ],
                estimated_effort_hours=200,
                risk_level="high",
            )
            
            result = await sandbox.simulate(scenario)
            
            assert result.status == "completed"
            assert len(result.compliance_impact["EU_AI_ACT"]["issues"]) >= 3

    async def test_simulate_data_flow_change(self, sandbox):
        """Test simulating a data flow change."""
        scenario = SimulationScenario(
            scenario_type=ScenarioType.DATA_FLOW_CHANGE,
            description="Add third-party analytics integration",
            parameters={
                "data_types": ["user_behavior", "page_views"],
                "destination": "analytics_provider",
                "transfer_mechanism": "api",
            },
            regulations=["GDPR", "CCPA"],
        )
        
        with patch.object(sandbox, "_analyze_data_flow_change") as mock_analyze:
            mock_analyze.return_value = SimulationResult(
                scenario_id="test-def",
                status="completed",
                compliance_impact={
                    "GDPR": {
                        "status": "requires_changes",
                        "issues": ["Third-party data processing agreement required"],
                    },
                    "CCPA": {
                        "status": "requires_changes",
                        "issues": ["Update privacy policy for data sharing"],
                    },
                },
                recommendations=["Execute DPA with analytics provider"],
                estimated_effort_hours=16,
                risk_level="medium",
            )
            
            result = await sandbox.simulate(scenario)
            
            assert result.status == "completed"

    def test_list_scenarios(self, sandbox):
        """Test listing available scenario types."""
        scenarios = sandbox.list_scenario_types()
        
        assert len(scenarios) >= 5
        types = [s["type"] for s in scenarios]
        assert "code_change" in types
        assert "architecture_change" in types
        assert "vendor_change" in types

    async def test_get_scenario_template(self, sandbox):
        """Test getting scenario template."""
        template = sandbox.get_scenario_template(ScenarioType.CODE_CHANGE)
        
        assert template is not None
        assert "parameters" in template
        assert "description" in template

    async def test_compare_scenarios(self, sandbox):
        """Test comparing multiple scenarios."""
        scenarios = [
            SimulationScenario(
                scenario_type=ScenarioType.ARCHITECTURE_CHANGE,
                description="Option A: Single region with backup",
                parameters={"regions": ["us-east-1"]},
                regulations=["GDPR"],
            ),
            SimulationScenario(
                scenario_type=ScenarioType.ARCHITECTURE_CHANGE,
                description="Option B: Multi-region active-active",
                parameters={"regions": ["us-east-1", "eu-west-1"]},
                regulations=["GDPR"],
            ),
        ]
        
        with patch.object(sandbox, "simulate") as mock_simulate:
            mock_simulate.side_effect = [
                SimulationResult(
                    scenario_id="opt-a",
                    status="completed",
                    compliance_impact={"GDPR": {"status": "compliant"}},
                    recommendations=[],
                    estimated_effort_hours=20,
                    risk_level="low",
                ),
                SimulationResult(
                    scenario_id="opt-b",
                    status="completed",
                    compliance_impact={"GDPR": {"status": "requires_changes"}},
                    recommendations=["Data residency controls"],
                    estimated_effort_hours=60,
                    risk_level="medium",
                ),
            ]
            
            comparison = await sandbox.compare_scenarios(scenarios)
            
            assert "results" in comparison
            assert len(comparison["results"]) == 2


class TestSimulationScenario:
    """Test SimulationScenario dataclass."""

    def test_scenario_creation(self):
        """Test creating a scenario."""
        scenario = SimulationScenario(
            scenario_type=ScenarioType.CODE_CHANGE,
            description="Test scenario",
            parameters={"key": "value"},
            regulations=["GDPR"],
        )
        
        assert scenario.scenario_type == ScenarioType.CODE_CHANGE
        assert scenario.description == "Test scenario"

    def test_scenario_to_dict(self):
        """Test converting scenario to dict."""
        scenario = SimulationScenario(
            scenario_type=ScenarioType.VENDOR_CHANGE,
            description="Test",
            parameters={},
            regulations=["SOC2"],
        )
        
        scenario_dict = scenario.to_dict()
        
        assert scenario_dict["scenario_type"] == "vendor_change"
        assert "regulations" in scenario_dict


class TestSimulationResult:
    """Test SimulationResult dataclass."""

    def test_result_creation(self):
        """Test creating a result."""
        result = SimulationResult(
            scenario_id="test-123",
            status="completed",
            compliance_impact={"GDPR": {"status": "compliant"}},
            recommendations=["No changes needed"],
            estimated_effort_hours=0,
            risk_level="low",
        )
        
        assert result.scenario_id == "test-123"
        assert result.status == "completed"
        assert result.risk_level == "low"

    def test_result_to_dict(self):
        """Test converting result to dict."""
        result = SimulationResult(
            scenario_id="test-456",
            status="failed",
            compliance_impact={},
            recommendations=[],
            estimated_effort_hours=0,
            risk_level="unknown",
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["status"] == "failed"


class TestScenarioType:
    """Test ScenarioType enum."""

    def test_scenario_types(self):
        """Test scenario type values."""
        assert ScenarioType.CODE_CHANGE.value == "code_change"
        assert ScenarioType.ARCHITECTURE_CHANGE.value == "architecture_change"
        assert ScenarioType.DATA_FLOW_CHANGE.value == "data_flow_change"
        assert ScenarioType.REGULATION_CHANGE.value == "regulation_change"
        assert ScenarioType.VENDOR_CHANGE.value == "vendor_change"
