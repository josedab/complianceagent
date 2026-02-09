"""Multi-Cloud IaC Compliance Scanner Service."""

import re
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.iac_scanner.models import (
    CloudProvider,
    ComplianceRule,
    IaCFixSuggestion,
    IaCPlatform,
    IaCScanResult,
    IaCViolation,
    ResourceType,
    ScanConfiguration,
    ScanSummary,
    ViolationSeverity,
)


logger = structlog.get_logger()

# Built-in compliance rules (20+ rules)
COMPLIANCE_RULES: list[ComplianceRule] = [
    # --- S3 / Storage ---
    ComplianceRule(
        id="IAC-001", name="S3 Public Access Blocked",
        description="S3 buckets must block public access to protect personal data",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AWS,
        resource_type=ResourceType.S3_BUCKET, severity=ViolationSeverity.CRITICAL,
        regulation="GDPR", article="Article 32",
        check_function="check_s3_public_access", fix_template="block_public_access = true",
    ),
    ComplianceRule(
        id="IAC-002", name="S3 Encryption at Rest",
        description="S3 buckets must have server-side encryption enabled",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AWS,
        resource_type=ResourceType.S3_BUCKET, severity=ViolationSeverity.HIGH,
        regulation="HIPAA", article="§164.312(a)(2)(iv)",
        check_function="check_s3_encryption", fix_template='server_side_encryption_configuration { rule { apply_server_side_encryption_by_default { sse_algorithm = "aws:kms" } } }',
    ),
    ComplianceRule(
        id="IAC-003", name="S3 Versioning Enabled",
        description="S3 buckets should have versioning enabled for data integrity",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AWS,
        resource_type=ResourceType.S3_BUCKET, severity=ViolationSeverity.MEDIUM,
        regulation="SOC 2", article="CC6.1",
        check_function="check_s3_versioning", fix_template="versioning { enabled = true }",
    ),
    ComplianceRule(
        id="IAC-004", name="S3 Access Logging",
        description="S3 buckets must have access logging enabled for audit trail",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AWS,
        resource_type=ResourceType.S3_BUCKET, severity=ViolationSeverity.MEDIUM,
        regulation="PCI-DSS", article="Requirement 10.2",
        check_function="check_s3_logging", fix_template='logging { target_bucket = "access-logs" }',
    ),
    # --- RDS ---
    ComplianceRule(
        id="IAC-005", name="RDS Encryption at Rest",
        description="RDS instances must have encryption at rest enabled for PHI protection",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AWS,
        resource_type=ResourceType.RDS_INSTANCE, severity=ViolationSeverity.CRITICAL,
        regulation="HIPAA", article="§164.312(a)(2)(iv)",
        check_function="check_rds_encryption", fix_template="storage_encrypted = true",
    ),
    ComplianceRule(
        id="IAC-006", name="RDS Multi-AZ Deployment",
        description="RDS instances should use Multi-AZ for high availability",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AWS,
        resource_type=ResourceType.RDS_INSTANCE, severity=ViolationSeverity.MEDIUM,
        regulation="SOC 2", article="A1.2",
        check_function="check_rds_multi_az", fix_template="multi_az = true",
    ),
    ComplianceRule(
        id="IAC-007", name="RDS Public Access Disabled",
        description="RDS instances must not be publicly accessible",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AWS,
        resource_type=ResourceType.RDS_INSTANCE, severity=ViolationSeverity.CRITICAL,
        regulation="GDPR", article="Article 25",
        check_function="check_rds_public_access", fix_template="publicly_accessible = false",
    ),
    # --- IAM ---
    ComplianceRule(
        id="IAC-008", name="IAM MFA Enforcement",
        description="IAM policies should enforce MFA for privileged actions",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AWS,
        resource_type=ResourceType.IAM_POLICY, severity=ViolationSeverity.HIGH,
        regulation="SOC 2", article="CC6.1",
        check_function="check_iam_mfa", fix_template='condition { test = "Bool" variable = "aws:MultiFactorAuthPresent" values = ["true"] }',
    ),
    ComplianceRule(
        id="IAC-009", name="IAM No Wildcard Actions",
        description="IAM policies must not use wildcard (*) actions",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AWS,
        resource_type=ResourceType.IAM_POLICY, severity=ViolationSeverity.HIGH,
        regulation="PCI-DSS", article="Requirement 7.1",
        check_function="check_iam_wildcard", fix_template="# Replace Action: ['*'] with specific actions",
    ),
    # --- Security Groups ---
    ComplianceRule(
        id="IAC-010", name="Security Group No Open Ingress",
        description="Security groups must not allow unrestricted ingress (0.0.0.0/0)",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AWS,
        resource_type=ResourceType.SECURITY_GROUP, severity=ViolationSeverity.CRITICAL,
        regulation="PCI-DSS", article="Requirement 1.3",
        check_function="check_sg_open_ingress", fix_template="# Restrict cidr_blocks to specific IP ranges",
    ),
    ComplianceRule(
        id="IAC-011", name="Security Group SSH Restricted",
        description="SSH access (port 22) must be restricted to specific IPs",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AWS,
        resource_type=ResourceType.SECURITY_GROUP, severity=ViolationSeverity.HIGH,
        regulation="SOC 2", article="CC6.6",
        check_function="check_sg_ssh_restricted", fix_template='cidr_blocks = ["10.0.0.0/8"]',
    ),
    # --- KMS ---
    ComplianceRule(
        id="IAC-012", name="KMS Key Rotation Enabled",
        description="KMS keys must have automatic rotation enabled",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AWS,
        resource_type=ResourceType.KMS_KEY, severity=ViolationSeverity.HIGH,
        regulation="PCI-DSS", article="Requirement 3.6",
        check_function="check_kms_rotation", fix_template="enable_key_rotation = true",
    ),
    # --- EC2 ---
    ComplianceRule(
        id="IAC-013", name="EC2 IMDSv2 Required",
        description="EC2 instances must use IMDSv2 to prevent SSRF attacks",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AWS,
        resource_type=ResourceType.EC2_INSTANCE, severity=ViolationSeverity.HIGH,
        regulation="SOC 2", article="CC6.1",
        check_function="check_ec2_imdsv2", fix_template='metadata_options { http_tokens = "required" }',
    ),
    # --- EKS ---
    ComplianceRule(
        id="IAC-014", name="EKS Secrets Encryption",
        description="EKS clusters must encrypt Kubernetes secrets at rest",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AWS,
        resource_type=ResourceType.EKS_CLUSTER, severity=ViolationSeverity.HIGH,
        regulation="HIPAA", article="§164.312(a)(2)(iv)",
        check_function="check_eks_secrets_encryption", fix_template='encryption_config { provider { key_arn = aws_kms_key.eks.arn } resources = ["secrets"] }',
    ),
    ComplianceRule(
        id="IAC-015", name="EKS Logging Enabled",
        description="EKS clusters must enable control plane logging",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AWS,
        resource_type=ResourceType.EKS_CLUSTER, severity=ViolationSeverity.MEDIUM,
        regulation="PCI-DSS", article="Requirement 10.2",
        check_function="check_eks_logging", fix_template='enabled_cluster_log_types = ["api", "audit", "authenticator"]',
    ),
    # --- Kubernetes ---
    ComplianceRule(
        id="IAC-016", name="K8s Network Policy Required",
        description="All namespaces must have a NetworkPolicy for network segmentation",
        platform=IaCPlatform.KUBERNETES, provider=CloudProvider.MULTI_CLOUD,
        resource_type=ResourceType.K8S_NETWORK_POLICY, severity=ViolationSeverity.HIGH,
        regulation="PCI-DSS", article="Requirement 1.2",
        check_function="check_k8s_network_policy", fix_template="# Add NetworkPolicy resource to namespace",
    ),
    ComplianceRule(
        id="IAC-017", name="K8s Pod Security Context",
        description="Pods must not run as root and must drop all capabilities",
        platform=IaCPlatform.KUBERNETES, provider=CloudProvider.MULTI_CLOUD,
        resource_type=ResourceType.K8S_POD, severity=ViolationSeverity.HIGH,
        regulation="SOC 2", article="CC6.3",
        check_function="check_k8s_pod_security", fix_template='securityContext: { runAsNonRoot: true, capabilities: { drop: ["ALL"] } }',
    ),
    ComplianceRule(
        id="IAC-018", name="K8s RBAC Least Privilege",
        description="RBAC roles must follow least privilege principle",
        platform=IaCPlatform.KUBERNETES, provider=CloudProvider.MULTI_CLOUD,
        resource_type=ResourceType.K8S_RBAC, severity=ViolationSeverity.CRITICAL,
        regulation="SOC 2", article="CC6.1",
        check_function="check_k8s_rbac_least_privilege", fix_template="# Replace wildcard verbs/resources with specific ones",
    ),
    ComplianceRule(
        id="IAC-019", name="K8s Secrets Not in Env",
        description="Kubernetes secrets should not be exposed as environment variables",
        platform=IaCPlatform.KUBERNETES, provider=CloudProvider.MULTI_CLOUD,
        resource_type=ResourceType.K8S_SECRET, severity=ViolationSeverity.MEDIUM,
        regulation="GDPR", article="Article 32",
        check_function="check_k8s_secrets_env", fix_template="# Use volume mounts instead of envFrom for secrets",
    ),
    ComplianceRule(
        id="IAC-020", name="K8s Resource Limits Required",
        description="Pods must define CPU and memory resource limits",
        platform=IaCPlatform.KUBERNETES, provider=CloudProvider.MULTI_CLOUD,
        resource_type=ResourceType.K8S_POD, severity=ViolationSeverity.MEDIUM,
        regulation="SOC 2", article="A1.1",
        check_function="check_k8s_resource_limits", fix_template='resources: { limits: { cpu: "500m", memory: "256Mi" } }',
    ),
    # --- CloudFormation ---
    ComplianceRule(
        id="IAC-021", name="CFN S3 Bucket Encryption",
        description="CloudFormation S3 buckets must have BucketEncryption configured",
        platform=IaCPlatform.CLOUDFORMATION, provider=CloudProvider.AWS,
        resource_type=ResourceType.S3_BUCKET, severity=ViolationSeverity.HIGH,
        regulation="HIPAA", article="§164.312(a)(2)(iv)",
        check_function="check_cfn_s3_encryption", fix_template="BucketEncryption: { ServerSideEncryptionConfiguration: [{ ServerSideEncryptionByDefault: { SSEAlgorithm: aws:kms } }] }",
    ),
    ComplianceRule(
        id="IAC-022", name="CFN RDS Storage Encrypted",
        description="CloudFormation RDS instances must have StorageEncrypted set to true",
        platform=IaCPlatform.CLOUDFORMATION, provider=CloudProvider.AWS,
        resource_type=ResourceType.RDS_INSTANCE, severity=ViolationSeverity.CRITICAL,
        regulation="HIPAA", article="§164.312(a)(2)(iv)",
        check_function="check_cfn_rds_encryption", fix_template="StorageEncrypted: true",
    ),
    # --- Lambda ---
    ComplianceRule(
        id="IAC-023", name="Lambda VPC Configuration",
        description="Lambda functions handling sensitive data must run inside a VPC",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AWS,
        resource_type=ResourceType.LAMBDA_FUNCTION, severity=ViolationSeverity.MEDIUM,
        regulation="HIPAA", article="§164.312(e)(1)",
        check_function="check_lambda_vpc", fix_template="vpc_config { subnet_ids = [...] security_group_ids = [...] }",
    ),
    # --- Azure Storage ---
    ComplianceRule(
        id="IAC-024", name="Azure Storage HTTPS Only",
        description="Azure Storage accounts must enforce HTTPS-only access",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AZURE,
        resource_type=ResourceType.AZURE_STORAGE, severity=ViolationSeverity.HIGH,
        regulation="GDPR", article="Article 32",
        check_function="check_azure_storage_https", fix_template="enable_https_traffic_only = true",
    ),
    ComplianceRule(
        id="IAC-025", name="Azure Storage Encryption",
        description="Azure Storage accounts must have blob encryption enabled",
        platform=IaCPlatform.TERRAFORM, provider=CloudProvider.AZURE,
        resource_type=ResourceType.AZURE_STORAGE, severity=ViolationSeverity.HIGH,
        regulation="HIPAA", article="§164.312(a)(2)(iv)",
        check_function="check_azure_storage_encryption", fix_template="blob_properties { delete_retention_policy { days = 7 } }",
    ),
]


class IaCScannerService:
    """Service for scanning IaC files for compliance violations."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot_client = copilot_client
        self._scan_results: list[IaCScanResult] = []
        self._rules = list(COMPLIANCE_RULES)

    async def scan_repository(
        self, org_id: str, repo_url: str, config: ScanConfiguration | None = None,
    ) -> IaCScanResult:
        """Scan a repository's IaC files for compliance violations."""
        start = datetime.now(UTC)
        config = config or ScanConfiguration()

        all_violations: list[IaCViolation] = []
        files_scanned = 0

        # Simulate repository file discovery and scanning
        sample_files = {
            IaCPlatform.TERRAFORM: ["main.tf", "variables.tf", "modules/vpc/main.tf"],
            IaCPlatform.CLOUDFORMATION: ["template.yaml", "stack.json"],
            IaCPlatform.KUBERNETES: ["deployment.yaml", "service.yaml", "ingress.yaml"],
        }

        for platform in config.platforms:
            files = sample_files.get(platform, [])
            for filename in files:
                files_scanned += 1
                violations = await self.scan_file("", platform, filename)
                filtered = self._apply_config_filters(violations, config)
                all_violations.extend(filtered)

        duration_ms = int((datetime.now(UTC) - start).total_seconds() * 1000)
        summary = self._build_summary(all_violations, files_scanned)

        result = IaCScanResult(
            org_id=org_id,
            platform=config.platforms[0] if config.platforms else IaCPlatform.TERRAFORM,
            provider=config.providers[0] if config.providers else CloudProvider.AWS,
            files_scanned=files_scanned,
            violations=all_violations,
            summary=summary,
            scanned_at=datetime.now(UTC),
            duration_ms=duration_ms,
        )

        self._scan_results.append(result)
        logger.info(
            "Repository scan complete",
            org_id=org_id, repo_url=repo_url,
            files_scanned=files_scanned, violations=len(all_violations),
        )
        return result

    async def scan_file(
        self, content: str, platform: IaCPlatform, filename: str,
    ) -> list[IaCViolation]:
        """Scan a single IaC file for compliance violations."""
        scanners = {
            IaCPlatform.TERRAFORM: self.scan_terraform,
            IaCPlatform.CLOUDFORMATION: self.scan_cloudformation,
            IaCPlatform.KUBERNETES: self.scan_kubernetes,
        }

        scanner = scanners.get(platform)
        if not scanner:
            logger.warning("Unsupported platform for scanning", platform=platform.value)
            return []

        return await scanner(content, filename)

    async def scan_terraform(self, content: str, filename: str) -> list[IaCViolation]:
        """Scan Terraform HCL content for compliance violations."""
        violations: list[IaCViolation] = []
        tf_rules = [r for r in self._rules if r.platform == IaCPlatform.TERRAFORM and r.enabled]
        content_lower = content.lower()

        for rule in tf_rules:
            violation = self._check_terraform_rule(rule, content, content_lower, filename)
            if violation:
                violations.append(violation)

        logger.info("Terraform scan complete", file=filename, violations=len(violations))
        return violations

    async def scan_cloudformation(self, content: str, filename: str) -> list[IaCViolation]:
        """Scan CloudFormation template for compliance violations."""
        violations: list[IaCViolation] = []
        cfn_rules = [r for r in self._rules if r.platform == IaCPlatform.CLOUDFORMATION and r.enabled]
        content_lower = content.lower()

        for rule in cfn_rules:
            violation = self._check_cloudformation_rule(rule, content, content_lower, filename)
            if violation:
                violations.append(violation)

        logger.info("CloudFormation scan complete", file=filename, violations=len(violations))
        return violations

    async def scan_kubernetes(self, content: str, filename: str) -> list[IaCViolation]:
        """Scan Kubernetes YAML for compliance violations."""
        violations: list[IaCViolation] = []
        k8s_rules = [r for r in self._rules if r.platform == IaCPlatform.KUBERNETES and r.enabled]
        content_lower = content.lower()

        for rule in k8s_rules:
            violation = self._check_kubernetes_rule(rule, content, content_lower, filename)
            if violation:
                violations.append(violation)

        logger.info("Kubernetes scan complete", file=filename, violations=len(violations))
        return violations

    async def get_scan_results(
        self, org_id: str, limit: int = 20,
    ) -> list[IaCScanResult]:
        """Get scan results for an organization."""
        results = [r for r in self._scan_results if r.org_id == org_id]
        return sorted(
            results, key=lambda r: r.scanned_at or datetime.min, reverse=True,
        )[:limit]

    async def get_fix_suggestion(self, violation_id: UUID) -> IaCFixSuggestion:
        """Get an auto-fix suggestion for a violation."""
        for result in self._scan_results:
            for v in result.violations:
                if v.id == violation_id:
                    rule = self._find_rule(v.rule_id)
                    return IaCFixSuggestion(
                        violation_id=violation_id,
                        original_code=f"# Violation: {v.description}",
                        fixed_code=rule.fix_template if rule else v.fix_suggestion,
                        explanation=f"Apply fix for {v.rule_id}: {v.description}",
                        confidence=0.85 if v.auto_fixable else 0.6,
                    )

        return IaCFixSuggestion(
            violation_id=violation_id,
            explanation="Violation not found",
            confidence=0.0,
        )

    async def list_rules(
        self,
        platform: IaCPlatform | None = None,
        regulation: str | None = None,
    ) -> list[ComplianceRule]:
        """List available compliance rules with optional filters."""
        rules = list(self._rules)
        if platform:
            rules = [r for r in rules if r.platform == platform]
        if regulation:
            rules = [r for r in rules if r.regulation.lower() == regulation.lower()]
        return rules

    async def generate_sarif_report(self, scan_result: IaCScanResult) -> dict:
        """Generate a SARIF-format report from scan results."""
        severity_map = {
            ViolationSeverity.CRITICAL: "error",
            ViolationSeverity.HIGH: "error",
            ViolationSeverity.MEDIUM: "warning",
            ViolationSeverity.LOW: "note",
            ViolationSeverity.INFO: "note",
        }

        rules = []
        results = []
        seen_rule_ids: set[str] = set()

        for v in scan_result.violations:
            if v.rule_id not in seen_rule_ids:
                seen_rule_ids.add(v.rule_id)
                rules.append({
                    "id": v.rule_id,
                    "shortDescription": {"text": v.description},
                    "helpUri": f"https://docs.complianceagent.io/rules/{v.rule_id}",
                    "properties": {
                        "regulation": v.regulation,
                        "article": v.article,
                    },
                })

            results.append({
                "ruleId": v.rule_id,
                "level": severity_map.get(v.severity, "warning"),
                "message": {"text": v.description},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": v.file_path},
                        "region": {"startLine": v.line_number},
                    },
                }],
            })

        return {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/sarif-2.1/schema/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "ComplianceAgent IaC Scanner",
                        "version": "1.0.0",
                        "rules": rules,
                    },
                },
                "results": results,
            }],
        }

    async def get_pre_commit_config(self, platforms: list[IaCPlatform]) -> str:
        """Generate pre-commit hook configuration for IaC scanning."""
        hooks = []

        if IaCPlatform.TERRAFORM in platforms:
            hooks.append(
                "  - repo: https://github.com/complianceagent/iac-scanner\n"
                "    rev: v1.0.0\n"
                "    hooks:\n"
                "      - id: iac-scan-terraform\n"
                "        name: IaC Compliance Scan (Terraform)\n"
                "        files: \\.tf$\n"
                "        language: python\n"
                "        entry: complianceagent-iac scan --platform terraform"
            )

        if IaCPlatform.CLOUDFORMATION in platforms:
            hooks.append(
                "  - repo: https://github.com/complianceagent/iac-scanner\n"
                "    rev: v1.0.0\n"
                "    hooks:\n"
                "      - id: iac-scan-cloudformation\n"
                "        name: IaC Compliance Scan (CloudFormation)\n"
                "        files: (template|stack)\\.(yaml|json)$\n"
                "        language: python\n"
                "        entry: complianceagent-iac scan --platform cloudformation"
            )

        if IaCPlatform.KUBERNETES in platforms:
            hooks.append(
                "  - repo: https://github.com/complianceagent/iac-scanner\n"
                "    rev: v1.0.0\n"
                "    hooks:\n"
                "      - id: iac-scan-kubernetes\n"
                "        name: IaC Compliance Scan (Kubernetes)\n"
                "        files: (deployment|service|ingress|pod)\\.yaml$\n"
                "        language: python\n"
                "        entry: complianceagent-iac scan --platform kubernetes"
            )

        config = "repos:\n" + "\n".join(hooks) if hooks else "repos: []"
        return config

    # --- Private helpers ---

    def _check_terraform_rule(
        self, rule: ComplianceRule, content: str, content_lower: str, filename: str,
    ) -> IaCViolation | None:
        """Check a single Terraform compliance rule against content."""
        checks = {
            "check_s3_public_access": (
                'resource "aws_s3_bucket"' in content_lower
                and "block_public_access" not in content_lower
                and "aws_s3_bucket_public_access_block" not in content_lower
            ),
            "check_s3_encryption": (
                'resource "aws_s3_bucket"' in content_lower
                and "server_side_encryption_configuration" not in content_lower
                and "aws_s3_bucket_server_side_encryption" not in content_lower
            ),
            "check_s3_versioning": (
                'resource "aws_s3_bucket"' in content_lower
                and "versioning" not in content_lower
            ),
            "check_s3_logging": (
                'resource "aws_s3_bucket"' in content_lower
                and "logging" not in content_lower
                and "aws_s3_bucket_logging" not in content_lower
            ),
            "check_rds_encryption": (
                'resource "aws_db_instance"' in content_lower
                and "storage_encrypted" not in content_lower
            ),
            "check_rds_multi_az": (
                'resource "aws_db_instance"' in content_lower
                and "multi_az" not in content_lower
            ),
            "check_rds_public_access": (
                'resource "aws_db_instance"' in content_lower
                and "publicly_accessible = true" in content_lower
            ),
            "check_iam_mfa": (
                'resource "aws_iam_policy"' in content_lower
                and "multifactorauthpresent" not in content_lower
            ),
            "check_iam_wildcard": (
                'resource "aws_iam_policy"' in content_lower
                and ('"*"' in content or "'*'" in content)
                and "action" in content_lower
            ),
            "check_sg_open_ingress": (
                'resource "aws_security_group"' in content_lower
                and "0.0.0.0/0" in content
                and "ingress" in content_lower
            ),
            "check_sg_ssh_restricted": (
                'resource "aws_security_group"' in content_lower
                and "22" in content
                and "0.0.0.0/0" in content
            ),
            "check_kms_rotation": (
                'resource "aws_kms_key"' in content_lower
                and "enable_key_rotation" not in content_lower
            ),
            "check_ec2_imdsv2": (
                'resource "aws_instance"' in content_lower
                and "metadata_options" not in content_lower
            ),
            "check_eks_secrets_encryption": (
                'resource "aws_eks_cluster"' in content_lower
                and "encryption_config" not in content_lower
            ),
            "check_eks_logging": (
                'resource "aws_eks_cluster"' in content_lower
                and "enabled_cluster_log_types" not in content_lower
            ),
            "check_lambda_vpc": (
                'resource "aws_lambda_function"' in content_lower
                and "vpc_config" not in content_lower
            ),
            "check_azure_storage_https": (
                'resource "azurerm_storage_account"' in content_lower
                and "enable_https_traffic_only" not in content_lower
            ),
            "check_azure_storage_encryption": (
                'resource "azurerm_storage_account"' in content_lower
                and "blob_properties" not in content_lower
            ),
        }

        is_violated = checks.get(rule.check_function, False)
        if not is_violated:
            return None

        line_number = self._find_resource_line(content, rule.resource_type)
        return IaCViolation(
            rule_id=rule.id,
            severity=rule.severity,
            resource_type=rule.resource_type,
            resource_name=self._extract_resource_name(content, rule.resource_type),
            file_path=filename,
            line_number=line_number,
            description=rule.description,
            regulation=rule.regulation,
            article=rule.article,
            fix_suggestion=rule.fix_template,
            auto_fixable=bool(rule.fix_template),
        )

    def _check_cloudformation_rule(
        self, rule: ComplianceRule, content: str, content_lower: str, filename: str,
    ) -> IaCViolation | None:
        """Check a single CloudFormation compliance rule against content."""
        checks = {
            "check_cfn_s3_encryption": (
                "aws::s3::bucket" in content_lower
                and "bucketencryption" not in content_lower
            ),
            "check_cfn_rds_encryption": (
                "aws::rds::dbinstance" in content_lower
                and "storageencrypted" not in content_lower
            ),
        }

        is_violated = checks.get(rule.check_function, False)
        if not is_violated:
            return None

        return IaCViolation(
            rule_id=rule.id,
            severity=rule.severity,
            resource_type=rule.resource_type,
            resource_name=self._extract_cfn_resource_name(content, rule.resource_type),
            file_path=filename,
            line_number=self._find_cfn_resource_line(content, rule.resource_type),
            description=rule.description,
            regulation=rule.regulation,
            article=rule.article,
            fix_suggestion=rule.fix_template,
            auto_fixable=bool(rule.fix_template),
        )

    def _check_kubernetes_rule(
        self, rule: ComplianceRule, content: str, content_lower: str, filename: str,
    ) -> IaCViolation | None:
        """Check a single Kubernetes compliance rule against content."""
        checks = {
            "check_k8s_network_policy": (
                ("kind: deployment" in content_lower or "kind: pod" in content_lower)
                and "kind: networkpolicy" not in content_lower
            ),
            "check_k8s_pod_security": (
                ("kind: deployment" in content_lower or "kind: pod" in content_lower)
                and "runasnonroot" not in content_lower
            ),
            "check_k8s_rbac_least_privilege": (
                ("kind: clusterrole" in content_lower or "kind: role" in content_lower)
                and '"*"' in content
            ),
            "check_k8s_secrets_env": (
                "kind: deployment" in content_lower
                and "secretref" in content_lower
                and "envfrom" in content_lower
            ),
            "check_k8s_resource_limits": (
                ("kind: deployment" in content_lower or "kind: pod" in content_lower)
                and "resources:" not in content_lower
            ),
        }

        is_violated = checks.get(rule.check_function, False)
        if not is_violated:
            return None

        return IaCViolation(
            rule_id=rule.id,
            severity=rule.severity,
            resource_type=rule.resource_type,
            resource_name=self._extract_k8s_resource_name(content),
            file_path=filename,
            line_number=self._find_k8s_resource_line(content, rule.resource_type),
            description=rule.description,
            regulation=rule.regulation,
            article=rule.article,
            fix_suggestion=rule.fix_template,
            auto_fixable=bool(rule.fix_template),
        )

    def _apply_config_filters(
        self, violations: list[IaCViolation], config: ScanConfiguration,
    ) -> list[IaCViolation]:
        """Filter violations based on scan configuration."""
        severity_order = {
            ViolationSeverity.INFO: 0, ViolationSeverity.LOW: 1,
            ViolationSeverity.MEDIUM: 2, ViolationSeverity.HIGH: 3,
            ViolationSeverity.CRITICAL: 4,
        }
        threshold = severity_order.get(config.severity_threshold, 0)

        filtered = []
        for v in violations:
            if v.rule_id in config.ignore_rules:
                continue
            if severity_order.get(v.severity, 0) < threshold:
                continue
            if config.regulations and v.regulation not in config.regulations:
                continue
            filtered.append(v)
        return filtered

    def _build_summary(
        self, violations: list[IaCViolation], files_scanned: int,
    ) -> ScanSummary:
        """Build a scan summary from violations."""
        critical = sum(1 for v in violations if v.severity == ViolationSeverity.CRITICAL)
        high = sum(1 for v in violations if v.severity == ViolationSeverity.HIGH)
        medium = sum(1 for v in violations if v.severity == ViolationSeverity.MEDIUM)
        low = sum(1 for v in violations if v.severity == ViolationSeverity.LOW)
        total = len(violations)

        # Score: start at 100, deduct per violation by severity
        score = max(0.0, 100.0 - (critical * 15) - (high * 8) - (medium * 3) - (low * 1))

        # Top violations by frequency
        rule_counts: dict[str, int] = {}
        for v in violations:
            rule_counts[v.rule_id] = rule_counts.get(v.rule_id, 0) + 1
        top = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return ScanSummary(
            total_resources=files_scanned,
            total_violations=total,
            critical=critical,
            high=high,
            medium=medium,
            low=low,
            compliance_score=round(score, 1),
            top_violations=[rule_id for rule_id, _ in top],
        )

    def _find_rule(self, rule_id: str) -> ComplianceRule | None:
        """Find a rule by ID."""
        for rule in self._rules:
            if rule.id == rule_id:
                return rule
        return None

    def _find_resource_line(self, content: str, resource_type: ResourceType) -> int:
        """Find the line number of a Terraform resource declaration."""
        resource_patterns = {
            ResourceType.S3_BUCKET: r'resource\s+"aws_s3_bucket"',
            ResourceType.RDS_INSTANCE: r'resource\s+"aws_db_instance"',
            ResourceType.EC2_INSTANCE: r'resource\s+"aws_instance"',
            ResourceType.IAM_POLICY: r'resource\s+"aws_iam_policy"',
            ResourceType.SECURITY_GROUP: r'resource\s+"aws_security_group"',
            ResourceType.KMS_KEY: r'resource\s+"aws_kms_key"',
            ResourceType.LAMBDA_FUNCTION: r'resource\s+"aws_lambda_function"',
            ResourceType.EKS_CLUSTER: r'resource\s+"aws_eks_cluster"',
            ResourceType.AZURE_STORAGE: r'resource\s+"azurerm_storage_account"',
        }
        pattern = resource_patterns.get(resource_type)
        if not pattern:
            return 1
        for i, line in enumerate(content.splitlines(), 1):
            if re.search(pattern, line, re.IGNORECASE):
                return i
        return 1

    def _extract_resource_name(self, content: str, resource_type: ResourceType) -> str:
        """Extract Terraform resource name from content."""
        resource_type_map = {
            ResourceType.S3_BUCKET: "aws_s3_bucket",
            ResourceType.RDS_INSTANCE: "aws_db_instance",
            ResourceType.EC2_INSTANCE: "aws_instance",
            ResourceType.IAM_POLICY: "aws_iam_policy",
            ResourceType.SECURITY_GROUP: "aws_security_group",
            ResourceType.KMS_KEY: "aws_kms_key",
            ResourceType.LAMBDA_FUNCTION: "aws_lambda_function",
            ResourceType.EKS_CLUSTER: "aws_eks_cluster",
            ResourceType.AZURE_STORAGE: "azurerm_storage_account",
        }
        tf_type = resource_type_map.get(resource_type, "")
        match = re.search(rf'resource\s+"{tf_type}"\s+"([^"]+)"', content)
        return match.group(1) if match else "unknown"

    def _find_cfn_resource_line(self, content: str, resource_type: ResourceType) -> int:
        """Find line number of a CloudFormation resource."""
        type_map = {
            ResourceType.S3_BUCKET: "AWS::S3::Bucket",
            ResourceType.RDS_INSTANCE: "AWS::RDS::DBInstance",
        }
        cfn_type = type_map.get(resource_type, "")
        for i, line in enumerate(content.splitlines(), 1):
            if cfn_type.lower() in line.lower():
                return i
        return 1

    def _extract_cfn_resource_name(self, content: str, resource_type: ResourceType) -> str:
        """Extract CloudFormation logical resource name."""
        type_map = {
            ResourceType.S3_BUCKET: "AWS::S3::Bucket",
            ResourceType.RDS_INSTANCE: "AWS::RDS::DBInstance",
        }
        cfn_type = type_map.get(resource_type, "")
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if cfn_type.lower() in line.lower() and i > 0:
                prev = lines[i - 1].strip().rstrip(":")
                if prev:
                    return prev
        return "unknown"

    def _find_k8s_resource_line(self, content: str, resource_type: ResourceType) -> int:
        """Find line number of a Kubernetes resource kind."""
        kind_map = {
            ResourceType.K8S_POD: "Deployment",
            ResourceType.K8S_NETWORK_POLICY: "Deployment",
            ResourceType.K8S_RBAC: "ClusterRole",
            ResourceType.K8S_SECRET: "Deployment",
        }
        kind = kind_map.get(resource_type, "")
        for i, line in enumerate(content.splitlines(), 1):
            if f"kind: {kind}" in line or f"kind:{kind}" in line.replace(" ", ""):
                return i
        return 1

    def _extract_k8s_resource_name(self, content: str) -> str:
        """Extract Kubernetes resource name from metadata."""
        match = re.search(r"name:\s*(\S+)", content)
        return match.group(1) if match else "unknown"
