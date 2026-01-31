"""Multi-cloud compliance posture analysis for IaC."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

import structlog


logger = structlog.get_logger()


class CloudProvider(str, Enum):
    """Supported cloud providers."""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    KUBERNETES = "kubernetes"


class IaCType(str, Enum):
    """Infrastructure as Code types."""

    TERRAFORM = "terraform"
    CLOUDFORMATION = "cloudformation"
    ARM = "arm"
    KUBERNETES = "kubernetes"
    PULUMI = "pulumi"


class ComplianceRuleCategory(str, Enum):
    """Categories of cloud compliance rules."""

    DATA_RESIDENCY = "data_residency"
    ENCRYPTION = "encryption"
    ACCESS_CONTROL = "access_control"
    NETWORK_SECURITY = "network_security"
    LOGGING = "logging"
    BACKUP = "backup"
    KEY_MANAGEMENT = "key_management"


@dataclass
class ComplianceRule:
    """A cloud compliance rule."""

    id: str
    name: str
    description: str
    category: ComplianceRuleCategory
    regulations: list[str]
    severity: str  # critical, high, medium, low
    resource_types: list[str]  # aws_s3_bucket, azurerm_storage_account, etc.
    check_pattern: str  # regex or HCL query
    remediation: str
    references: list[str] = field(default_factory=list)


@dataclass
class IaCFinding:
    """A compliance finding in IaC code."""

    id: UUID = field(default_factory=uuid4)
    rule_id: str = ""
    file_path: str = ""
    line_number: int = 0
    resource_name: str = ""
    resource_type: str = ""
    severity: str = "medium"
    message: str = ""
    regulation: str = ""
    remediation: str = ""
    fix_suggestion: str | None = None


# Cloud compliance rules
CLOUD_COMPLIANCE_RULES: list[ComplianceRule] = [
    # AWS Rules
    ComplianceRule(
        id="AWS-S3-001",
        name="S3 Bucket Encryption",
        description="S3 buckets must have server-side encryption enabled",
        category=ComplianceRuleCategory.ENCRYPTION,
        regulations=["GDPR", "HIPAA", "PCI-DSS", "SOC 2"],
        severity="critical",
        resource_types=["aws_s3_bucket", "aws_s3_bucket_server_side_encryption_configuration"],
        check_pattern=r"server_side_encryption_configuration",
        remediation="Enable SSE-S3, SSE-KMS, or SSE-C encryption",
        references=["GDPR Article 32", "HIPAA 45 CFR 164.312(a)(2)(iv)"],
    ),
    ComplianceRule(
        id="AWS-S3-002",
        name="S3 Bucket Public Access",
        description="S3 buckets should block public access",
        category=ComplianceRuleCategory.ACCESS_CONTROL,
        regulations=["GDPR", "HIPAA", "SOC 2"],
        severity="critical",
        resource_types=["aws_s3_bucket_public_access_block"],
        check_pattern=r"block_public_acls\s*=\s*true",
        remediation="Enable block_public_acls, block_public_policy, ignore_public_acls, restrict_public_buckets",
    ),
    ComplianceRule(
        id="AWS-RDS-001",
        name="RDS Encryption at Rest",
        description="RDS instances must have encryption at rest enabled",
        category=ComplianceRuleCategory.ENCRYPTION,
        regulations=["GDPR", "HIPAA", "PCI-DSS"],
        severity="critical",
        resource_types=["aws_db_instance", "aws_rds_cluster"],
        check_pattern=r"storage_encrypted\s*=\s*true",
        remediation="Set storage_encrypted = true",
    ),
    ComplianceRule(
        id="AWS-LOG-001",
        name="CloudTrail Enabled",
        description="CloudTrail logging must be enabled for all regions",
        category=ComplianceRuleCategory.LOGGING,
        regulations=["SOX", "HIPAA", "SOC 2", "PCI-DSS"],
        severity="high",
        resource_types=["aws_cloudtrail"],
        check_pattern=r"is_multi_region_trail\s*=\s*true",
        remediation="Enable multi-region CloudTrail with S3 logging",
    ),
    # Azure Rules
    ComplianceRule(
        id="AZURE-STORAGE-001",
        name="Azure Storage Encryption",
        description="Azure Storage accounts must use encryption",
        category=ComplianceRuleCategory.ENCRYPTION,
        regulations=["GDPR", "HIPAA"],
        severity="critical",
        resource_types=["azurerm_storage_account"],
        check_pattern=r"enable_blob_encryption\s*=\s*true|infrastructure_encryption_enabled\s*=\s*true",
        remediation="Enable blob encryption and infrastructure encryption",
    ),
    ComplianceRule(
        id="AZURE-SQL-001",
        name="Azure SQL TDE",
        description="Azure SQL databases must have Transparent Data Encryption",
        category=ComplianceRuleCategory.ENCRYPTION,
        regulations=["GDPR", "HIPAA", "PCI-DSS"],
        severity="critical",
        resource_types=["azurerm_mssql_database"],
        check_pattern=r"transparent_data_encryption_enabled\s*=\s*true",
        remediation="Enable transparent_data_encryption_enabled",
    ),
    # GCP Rules
    ComplianceRule(
        id="GCP-GCS-001",
        name="GCS Bucket Encryption",
        description="GCS buckets must use customer-managed encryption keys for sensitive data",
        category=ComplianceRuleCategory.ENCRYPTION,
        regulations=["GDPR", "HIPAA"],
        severity="high",
        resource_types=["google_storage_bucket"],
        check_pattern=r"encryption\s*{",
        remediation="Configure encryption block with default_kms_key_name",
    ),
    # Kubernetes Rules
    ComplianceRule(
        id="K8S-SEC-001",
        name="Pod Security Context",
        description="Pods must define security context with non-root user",
        category=ComplianceRuleCategory.ACCESS_CONTROL,
        regulations=["SOC 2", "ISO 27001"],
        severity="high",
        resource_types=["kubernetes_pod", "kubernetes_deployment"],
        check_pattern=r"security_context\s*{.*run_as_non_root\s*=\s*true",
        remediation="Set securityContext.runAsNonRoot: true",
    ),
    ComplianceRule(
        id="K8S-NET-001",
        name="Network Policy",
        description="Namespaces should have default deny network policies",
        category=ComplianceRuleCategory.NETWORK_SECURITY,
        regulations=["PCI-DSS", "SOC 2"],
        severity="medium",
        resource_types=["kubernetes_network_policy"],
        check_pattern=r"policy_types.*Ingress.*Egress",
        remediation="Create default deny NetworkPolicy for namespace",
    ),
    # Data Residency Rules
    ComplianceRule(
        id="DR-001",
        name="EU Data Residency",
        description="Resources handling EU personal data must be in EU regions",
        category=ComplianceRuleCategory.DATA_RESIDENCY,
        regulations=["GDPR"],
        severity="critical",
        resource_types=["aws_s3_bucket", "aws_db_instance", "azurerm_storage_account", "google_storage_bucket"],
        check_pattern=r'region\s*=\s*"(eu-|europe-|EU)',
        remediation="Deploy resources in EU regions (eu-west-1, europe-west1, etc.)",
    ),
]


class CloudComplianceAnalyzer:
    """Analyzer for IaC compliance issues."""

    def __init__(self, rules: list[ComplianceRule] | None = None):
        self.rules = rules or CLOUD_COMPLIANCE_RULES

    def analyze_terraform(
        self,
        content: str,
        file_path: str,
        regulations: list[str] | None = None,
    ) -> list[IaCFinding]:
        """Analyze Terraform code for compliance issues."""
        import re

        findings = []
        lines = content.split("\n")

        # Filter rules by regulation
        active_rules = self.rules
        if regulations:
            active_rules = [r for r in self.rules if any(reg in r.regulations for reg in regulations)]

        # Find all resource blocks
        resource_pattern = re.compile(r'resource\s+"([^"]+)"\s+"([^"]+)"', re.MULTILINE)

        for match in resource_pattern.finditer(content):
            resource_type = match.group(1)
            resource_name = match.group(2)
            start_pos = match.start()
            line_number = content[:start_pos].count("\n") + 1

            # Find the resource block content
            block_start = content.find("{", start_pos)
            if block_start == -1:
                continue

            # Simple bracket matching for block end
            depth = 1
            block_end = block_start + 1
            while depth > 0 and block_end < len(content):
                if content[block_end] == "{":
                    depth += 1
                elif content[block_end] == "}":
                    depth -= 1
                block_end += 1

            resource_content = content[block_start:block_end]

            # Check applicable rules
            for rule in active_rules:
                if resource_type not in rule.resource_types:
                    continue

                # Check if rule pattern is present
                if not re.search(rule.check_pattern, resource_content, re.IGNORECASE | re.DOTALL):
                    findings.append(IaCFinding(
                        rule_id=rule.id,
                        file_path=file_path,
                        line_number=line_number,
                        resource_name=resource_name,
                        resource_type=resource_type,
                        severity=rule.severity,
                        message=f"{rule.name}: {rule.description}",
                        regulation=", ".join(rule.regulations),
                        remediation=rule.remediation,
                    ))

        return findings

    def analyze_cloudformation(
        self,
        content: str,
        file_path: str,
        regulations: list[str] | None = None,
    ) -> list[IaCFinding]:
        """Analyze CloudFormation template for compliance issues."""
        import json
        import yaml

        findings = []

        # Parse template (JSON or YAML)
        try:
            if content.strip().startswith("{"):
                template = json.loads(content)
            else:
                template = yaml.safe_load(content)
        except Exception as e:
            logger.warning(f"Failed to parse CloudFormation template: {e}")
            return findings

        resources = template.get("Resources", {})

        for name, resource in resources.items():
            resource_type = resource.get("Type", "")
            properties = resource.get("Properties", {})

            # Map CFN types to our rule resource types
            type_mapping = {
                "AWS::S3::Bucket": "aws_s3_bucket",
                "AWS::RDS::DBInstance": "aws_db_instance",
                "AWS::CloudTrail::Trail": "aws_cloudtrail",
            }

            mapped_type = type_mapping.get(resource_type)
            if not mapped_type:
                continue

            for rule in self.rules:
                if mapped_type not in rule.resource_types:
                    continue

                # Check specific properties
                issue_found = False

                if rule.id == "AWS-S3-001":
                    # Check for encryption configuration
                    if "BucketEncryption" not in properties:
                        issue_found = True

                elif rule.id == "AWS-RDS-001":
                    if not properties.get("StorageEncrypted", False):
                        issue_found = True

                if issue_found:
                    findings.append(IaCFinding(
                        rule_id=rule.id,
                        file_path=file_path,
                        line_number=0,  # Line numbers harder to track in YAML/JSON
                        resource_name=name,
                        resource_type=resource_type,
                        severity=rule.severity,
                        message=f"{rule.name}: {rule.description}",
                        regulation=", ".join(rule.regulations),
                        remediation=rule.remediation,
                    ))

        return findings

    def analyze_kubernetes(
        self,
        content: str,
        file_path: str,
        regulations: list[str] | None = None,
    ) -> list[IaCFinding]:
        """Analyze Kubernetes manifests for compliance issues."""
        import yaml

        findings = []

        # Parse all documents in the YAML
        try:
            docs = list(yaml.safe_load_all(content))
        except Exception as e:
            logger.warning(f"Failed to parse Kubernetes manifest: {e}")
            return findings

        for doc in docs:
            if not doc:
                continue

            kind = doc.get("kind", "")
            name = doc.get("metadata", {}).get("name", "unknown")

            # Check Pod/Deployment security context
            if kind in ("Pod", "Deployment", "StatefulSet", "DaemonSet"):
                spec = doc.get("spec", {})
                if kind != "Pod":
                    spec = spec.get("template", {}).get("spec", {})

                security_context = spec.get("securityContext", {})

                if not security_context.get("runAsNonRoot"):
                    findings.append(IaCFinding(
                        rule_id="K8S-SEC-001",
                        file_path=file_path,
                        resource_name=name,
                        resource_type=f"kubernetes_{kind.lower()}",
                        severity="high",
                        message="Pod Security Context: Pods must run as non-root user",
                        regulation="SOC 2, ISO 27001",
                        remediation="Set securityContext.runAsNonRoot: true",
                    ))

            # Check NetworkPolicy
            if kind == "NetworkPolicy":
                policy_types = doc.get("spec", {}).get("policyTypes", [])
                if "Ingress" not in policy_types or "Egress" not in policy_types:
                    findings.append(IaCFinding(
                        rule_id="K8S-NET-001",
                        file_path=file_path,
                        resource_name=name,
                        resource_type="kubernetes_network_policy",
                        severity="medium",
                        message="Network Policy should include both Ingress and Egress",
                        regulation="PCI-DSS, SOC 2",
                        remediation="Add both Ingress and Egress to policyTypes",
                    ))

        return findings

    def get_rules_by_regulation(self, regulation: str) -> list[ComplianceRule]:
        """Get all rules for a specific regulation."""
        return [r for r in self.rules if regulation in r.regulations]

    def get_rules_by_provider(self, provider: CloudProvider) -> list[ComplianceRule]:
        """Get all rules for a specific cloud provider."""
        provider_prefixes = {
            CloudProvider.AWS: "aws_",
            CloudProvider.AZURE: "azurerm_",
            CloudProvider.GCP: "google_",
            CloudProvider.KUBERNETES: "kubernetes_",
        }
        prefix = provider_prefixes.get(provider, "")
        return [
            r for r in self.rules
            if any(rt.startswith(prefix) for rt in r.resource_types)
        ]
