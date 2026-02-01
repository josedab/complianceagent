"""Tests for cloud compliance service."""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.cloud import (
    CloudComplianceAnalyzer,
    IaCType,
    CloudComplianceFinding,
    CloudComplianceReport,
)

pytestmark = pytest.mark.asyncio


class TestCloudComplianceAnalyzer:
    """Test suite for CloudComplianceAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create CloudComplianceAnalyzer instance."""
        return CloudComplianceAnalyzer()

    def test_detect_iac_type_terraform(self, analyzer):
        """Test detecting Terraform files."""
        terraform_content = """
        resource "aws_s3_bucket" "example" {
            bucket = "my-bucket"
        }
        """
        iac_type = analyzer.detect_iac_type(terraform_content, "main.tf")
        assert iac_type == IaCType.TERRAFORM

    def test_detect_iac_type_cloudformation_yaml(self, analyzer):
        """Test detecting CloudFormation YAML files."""
        cfn_content = """
        AWSTemplateFormatVersion: '2010-09-09'
        Resources:
          MyBucket:
            Type: AWS::S3::Bucket
        """
        iac_type = analyzer.detect_iac_type(cfn_content, "template.yaml")
        assert iac_type == IaCType.CLOUDFORMATION

    def test_detect_iac_type_cloudformation_json(self, analyzer):
        """Test detecting CloudFormation JSON files."""
        cfn_content = """{
            "AWSTemplateFormatVersion": "2010-09-09",
            "Resources": {}
        }"""
        iac_type = analyzer.detect_iac_type(cfn_content, "template.json")
        assert iac_type == IaCType.CLOUDFORMATION

    def test_detect_iac_type_kubernetes(self, analyzer):
        """Test detecting Kubernetes files."""
        k8s_content = """
        apiVersion: v1
        kind: Pod
        metadata:
          name: my-pod
        """
        iac_type = analyzer.detect_iac_type(k8s_content, "deployment.yaml")
        assert iac_type == IaCType.KUBERNETES

    async def test_analyze_terraform_unencrypted_s3(self, analyzer):
        """Test analyzing Terraform for unencrypted S3 bucket."""
        terraform_code = """
        resource "aws_s3_bucket" "data" {
            bucket = "sensitive-data-bucket"
        }
        """
        
        findings = await analyzer.analyze(
            content=terraform_code,
            filename="main.tf",
            regulations=["GDPR", "HIPAA"],
        )
        
        # Should find unencrypted storage issue
        assert len(findings) >= 1
        encryption_findings = [f for f in findings if "encrypt" in f.description.lower()]
        assert len(encryption_findings) >= 1

    async def test_analyze_terraform_compliant_s3(self, analyzer):
        """Test analyzing Terraform for compliant S3 bucket."""
        terraform_code = """
        resource "aws_s3_bucket" "data" {
            bucket = "sensitive-data-bucket"
        }
        
        resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
            bucket = aws_s3_bucket.data.id
            rule {
                apply_server_side_encryption_by_default {
                    sse_algorithm = "aws:kms"
                }
            }
        }
        """
        
        findings = await analyzer.analyze(
            content=terraform_code,
            filename="main.tf",
            regulations=["GDPR"],
        )
        
        # Should have fewer or no encryption findings
        encryption_findings = [f for f in findings if "encrypt" in f.description.lower() and f.severity == "high"]
        assert len(encryption_findings) == 0

    async def test_analyze_cloudformation_unencrypted_rds(self, analyzer):
        """Test analyzing CloudFormation for unencrypted RDS."""
        cfn_code = """
        AWSTemplateFormatVersion: '2010-09-09'
        Resources:
          Database:
            Type: AWS::RDS::DBInstance
            Properties:
              DBInstanceClass: db.t3.micro
              Engine: postgres
        """
        
        findings = await analyzer.analyze(
            content=cfn_code,
            filename="database.yaml",
            regulations=["HIPAA"],
        )
        
        # Should find unencrypted database issue
        assert len(findings) >= 1

    async def test_analyze_kubernetes_privileged_container(self, analyzer):
        """Test analyzing Kubernetes for privileged container."""
        k8s_code = """
        apiVersion: v1
        kind: Pod
        metadata:
          name: privileged-pod
        spec:
          containers:
          - name: app
            image: myapp
            securityContext:
              privileged: true
        """
        
        findings = await analyzer.analyze(
            content=k8s_code,
            filename="pod.yaml",
            regulations=["SOC2"],
        )
        
        # Should find privileged container issue
        privileged_findings = [f for f in findings if "privileged" in f.description.lower()]
        assert len(privileged_findings) >= 1

    async def test_generate_report(self, analyzer):
        """Test generating compliance report."""
        files = {
            "main.tf": """
            resource "aws_s3_bucket" "data" {
                bucket = "my-bucket"
            }
            """,
            "database.tf": """
            resource "aws_rds_cluster" "db" {
                cluster_identifier = "my-db"
            }
            """,
        }
        
        report = await analyzer.generate_report(
            files=files,
            regulations=["GDPR", "HIPAA"],
        )
        
        assert isinstance(report, CloudComplianceReport)
        assert report.total_files == 2
        assert len(report.findings) >= 0


class TestCloudComplianceFinding:
    """Test CloudComplianceFinding dataclass."""

    def test_finding_creation(self):
        """Test creating a finding."""
        finding = CloudComplianceFinding(
            rule_id="CLOUD-001",
            severity="high",
            description="S3 bucket without encryption",
            resource_type="aws_s3_bucket",
            file_path="main.tf",
            line_number=5,
            regulations=["GDPR", "HIPAA"],
            remediation="Enable server-side encryption",
        )
        
        assert finding.rule_id == "CLOUD-001"
        assert finding.severity == "high"
        assert "GDPR" in finding.regulations

    def test_finding_to_dict(self):
        """Test converting finding to dict."""
        finding = CloudComplianceFinding(
            rule_id="CLOUD-001",
            severity="medium",
            description="Test finding",
            resource_type="test_resource",
            file_path="test.tf",
            line_number=1,
            regulations=["TEST"],
            remediation="Fix it",
        )
        
        finding_dict = finding.to_dict()
        
        assert finding_dict["rule_id"] == "CLOUD-001"
        assert finding_dict["severity"] == "medium"


class TestCloudComplianceReport:
    """Test CloudComplianceReport dataclass."""

    def test_report_creation(self):
        """Test creating a report."""
        finding = CloudComplianceFinding(
            rule_id="CLOUD-001",
            severity="high",
            description="Test",
            resource_type="test",
            file_path="test.tf",
            line_number=1,
            regulations=["TEST"],
            remediation="Fix",
        )
        
        report = CloudComplianceReport(
            total_files=5,
            findings=[finding],
            summary={
                "high": 1,
                "medium": 0,
                "low": 0,
            },
            regulations_checked=["TEST"],
        )
        
        assert report.total_files == 5
        assert len(report.findings) == 1
        assert report.summary["high"] == 1


class TestIaCType:
    """Test IaCType enum."""

    def test_iac_types(self):
        """Test IaC type values."""
        assert IaCType.TERRAFORM.value == "terraform"
        assert IaCType.CLOUDFORMATION.value == "cloudformation"
        assert IaCType.KUBERNETES.value == "kubernetes"
