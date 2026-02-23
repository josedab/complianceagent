"""Multi-Cloud IaC Policy Engine Service."""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.iac_policy.extended_rules import (
    AWS_EXTENDED_RULES,
    AZURE_EXTENDED_RULES,
    GCP_EXTENDED_RULES,
    K8S_EXTENDED_RULES,
)
from app.services.iac_policy.models import (
    CloudProvider,
    IaCScanResult,
    IaCViolation,
    PolicyRule,
    PolicySeverity,
)


logger = structlog.get_logger()

_AWS_RULES = [
    PolicyRule(
        id="AWS-ENC-001",
        name="S3 Bucket Encryption",
        provider=CloudProvider.AWS,
        framework="SOC2",
        severity=PolicySeverity.HIGH,
        description="S3 buckets must have server-side encryption enabled",
        pattern="aws_s3_bucket",
    ),
    PolicyRule(
        id="AWS-ENC-002",
        name="RDS Encryption at Rest",
        provider=CloudProvider.AWS,
        framework="HIPAA",
        severity=PolicySeverity.CRITICAL,
        description="RDS instances must have encryption at rest enabled",
        pattern="aws_db_instance",
    ),
    PolicyRule(
        id="AWS-ENC-003",
        name="EBS Volume Encryption",
        provider=CloudProvider.AWS,
        framework="PCI-DSS",
        severity=PolicySeverity.HIGH,
        description="EBS volumes must be encrypted",
        pattern="aws_ebs_volume",
    ),
    PolicyRule(
        id="AWS-ACC-001",
        name="IAM Password Policy",
        provider=CloudProvider.AWS,
        framework="SOC2",
        severity=PolicySeverity.MEDIUM,
        description="IAM password policy must enforce complexity",
        pattern="aws_iam_account_password_policy",
    ),
    PolicyRule(
        id="AWS-ACC-002",
        name="S3 Public Access Block",
        provider=CloudProvider.AWS,
        framework="GDPR",
        severity=PolicySeverity.CRITICAL,
        description="S3 buckets must block public access",
        pattern="aws_s3_bucket_public_access_block",
    ),
    PolicyRule(
        id="AWS-LOG-001",
        name="CloudTrail Enabled",
        provider=CloudProvider.AWS,
        framework="SOC2",
        severity=PolicySeverity.HIGH,
        description="CloudTrail must be enabled in all regions",
        pattern="aws_cloudtrail",
    ),
    PolicyRule(
        id="AWS-LOG-002",
        name="VPC Flow Logs",
        provider=CloudProvider.AWS,
        framework="NIST",
        severity=PolicySeverity.MEDIUM,
        description="VPC flow logs must be enabled",
        pattern="aws_flow_log",
    ),
    PolicyRule(
        id="AWS-NET-001",
        name="Security Group Ingress",
        provider=CloudProvider.AWS,
        framework="PCI-DSS",
        severity=PolicySeverity.CRITICAL,
        description="Security groups must not allow unrestricted ingress",
        pattern="aws_security_group",
    ),
    PolicyRule(
        id="AWS-NET-002",
        name="RDS Public Access",
        provider=CloudProvider.AWS,
        framework="HIPAA",
        severity=PolicySeverity.CRITICAL,
        description="RDS instances must not be publicly accessible",
        pattern="aws_db_instance",
    ),
    PolicyRule(
        id="AWS-ACC-003",
        name="Root Account MFA",
        provider=CloudProvider.AWS,
        framework="SOC2",
        severity=PolicySeverity.CRITICAL,
        description="Root account must have MFA enabled",
        pattern="aws_iam_account_password_policy",
    ),
    PolicyRule(
        id="AWS-ENC-004",
        name="KMS Key Rotation",
        provider=CloudProvider.AWS,
        framework="PCI-DSS",
        severity=PolicySeverity.MEDIUM,
        description="KMS keys must have automatic rotation enabled",
        pattern="aws_kms_key",
    ),
    PolicyRule(
        id="AWS-LOG-003",
        name="S3 Access Logging",
        provider=CloudProvider.AWS,
        framework="SOC2",
        severity=PolicySeverity.LOW,
        description="S3 buckets should have access logging enabled",
        pattern="aws_s3_bucket",
    ),
    PolicyRule(
        id="AWS-NET-003",
        name="ALB HTTPS Only",
        provider=CloudProvider.AWS,
        framework="PCI-DSS",
        severity=PolicySeverity.HIGH,
        description="ALB listeners must use HTTPS",
        pattern="aws_lb_listener",
    ),
    PolicyRule(
        id="AWS-ACC-004",
        name="IAM Role Boundary",
        provider=CloudProvider.AWS,
        framework="NIST",
        severity=PolicySeverity.MEDIUM,
        description="IAM roles should have permission boundaries",
        pattern="aws_iam_role",
    ),
    PolicyRule(
        id="AWS-ENC-005",
        name="SNS Topic Encryption",
        provider=CloudProvider.AWS,
        framework="HIPAA",
        severity=PolicySeverity.MEDIUM,
        description="SNS topics must be encrypted with KMS",
        pattern="aws_sns_topic",
    ),
    PolicyRule(
        id="AWS-NET-004",
        name="ElastiCache In-Transit",
        provider=CloudProvider.AWS,
        framework="PCI-DSS",
        severity=PolicySeverity.HIGH,
        description="ElastiCache must encrypt data in transit",
        pattern="aws_elasticache_replication_group",
    ),
]

_AZURE_RULES = [
    PolicyRule(
        id="AZ-ENC-001",
        name="Storage Account Encryption",
        provider=CloudProvider.AZURE,
        framework="SOC2",
        severity=PolicySeverity.HIGH,
        description="Storage accounts must use customer-managed keys",
        pattern="azurerm_storage_account",
    ),
    PolicyRule(
        id="AZ-ENC-002",
        name="SQL Database TDE",
        provider=CloudProvider.AZURE,
        framework="HIPAA",
        severity=PolicySeverity.CRITICAL,
        description="SQL databases must have transparent data encryption",
        pattern="azurerm_mssql_database",
    ),
    PolicyRule(
        id="AZ-ACC-001",
        name="Key Vault Access Policy",
        provider=CloudProvider.AZURE,
        framework="SOC2",
        severity=PolicySeverity.HIGH,
        description="Key Vault must restrict access policies",
        pattern="azurerm_key_vault",
    ),
    PolicyRule(
        id="AZ-ACC-002",
        name="RBAC Enabled",
        provider=CloudProvider.AZURE,
        framework="NIST",
        severity=PolicySeverity.MEDIUM,
        description="RBAC must be enabled on AKS clusters",
        pattern="azurerm_kubernetes_cluster",
    ),
    PolicyRule(
        id="AZ-LOG-001",
        name="Activity Log Alerts",
        provider=CloudProvider.AZURE,
        framework="SOC2",
        severity=PolicySeverity.MEDIUM,
        description="Activity log alerts must be configured",
        pattern="azurerm_monitor_activity_log_alert",
    ),
    PolicyRule(
        id="AZ-LOG-002",
        name="Diagnostic Settings",
        provider=CloudProvider.AZURE,
        framework="PCI-DSS",
        severity=PolicySeverity.HIGH,
        description="Diagnostic settings must be enabled",
        pattern="azurerm_monitor_diagnostic_setting",
    ),
    PolicyRule(
        id="AZ-NET-001",
        name="NSG Rules",
        provider=CloudProvider.AZURE,
        framework="PCI-DSS",
        severity=PolicySeverity.CRITICAL,
        description="NSG rules must not allow unrestricted access",
        pattern="azurerm_network_security_rule",
    ),
    PolicyRule(
        id="AZ-NET-002",
        name="App Service HTTPS",
        provider=CloudProvider.AZURE,
        framework="GDPR",
        severity=PolicySeverity.HIGH,
        description="App Services must enforce HTTPS",
        pattern="azurerm_app_service",
    ),
    PolicyRule(
        id="AZ-ENC-003",
        name="Disk Encryption",
        provider=CloudProvider.AZURE,
        framework="HIPAA",
        severity=PolicySeverity.HIGH,
        description="Managed disks must be encrypted",
        pattern="azurerm_managed_disk",
    ),
    PolicyRule(
        id="AZ-ACC-003",
        name="SQL Firewall Rules",
        provider=CloudProvider.AZURE,
        framework="PCI-DSS",
        severity=PolicySeverity.HIGH,
        description="SQL Server firewall must not allow all Azure IPs",
        pattern="azurerm_sql_firewall_rule",
    ),
    PolicyRule(
        id="AZ-LOG-003",
        name="Security Center Enabled",
        provider=CloudProvider.AZURE,
        framework="NIST",
        severity=PolicySeverity.MEDIUM,
        description="Azure Security Center must be enabled",
        pattern="azurerm_security_center_subscription_pricing",
    ),
    PolicyRule(
        id="AZ-NET-003",
        name="Private Endpoints",
        provider=CloudProvider.AZURE,
        framework="HIPAA",
        severity=PolicySeverity.MEDIUM,
        description="Services should use private endpoints",
        pattern="azurerm_private_endpoint",
    ),
    PolicyRule(
        id="AZ-ENC-004",
        name="Key Vault Key Expiry",
        provider=CloudProvider.AZURE,
        framework="SOC2",
        severity=PolicySeverity.LOW,
        description="Key Vault keys should have expiration dates",
        pattern="azurerm_key_vault_key",
    ),
    PolicyRule(
        id="AZ-ACC-004",
        name="Managed Identity",
        provider=CloudProvider.AZURE,
        framework="SOC2",
        severity=PolicySeverity.MEDIUM,
        description="Resources should use managed identities",
        pattern="azurerm_user_assigned_identity",
    ),
    PolicyRule(
        id="AZ-NET-004",
        name="WAF Enabled",
        provider=CloudProvider.AZURE,
        framework="PCI-DSS",
        severity=PolicySeverity.HIGH,
        description="Web Application Firewall must be enabled",
        pattern="azurerm_web_application_firewall_policy",
    ),
    PolicyRule(
        id="AZ-LOG-004",
        name="Storage Logging",
        provider=CloudProvider.AZURE,
        framework="SOC2",
        severity=PolicySeverity.LOW,
        description="Storage account logging should be enabled",
        pattern="azurerm_storage_account",
    ),
]

_GCP_RULES = [
    PolicyRule(
        id="GCP-ENC-001",
        name="GCS Bucket Encryption",
        provider=CloudProvider.GCP,
        framework="SOC2",
        severity=PolicySeverity.HIGH,
        description="GCS buckets must use CMEK encryption",
        pattern="google_storage_bucket",
    ),
    PolicyRule(
        id="GCP-ENC-002",
        name="Cloud SQL Encryption",
        provider=CloudProvider.GCP,
        framework="HIPAA",
        severity=PolicySeverity.CRITICAL,
        description="Cloud SQL instances must have encryption enabled",
        pattern="google_sql_database_instance",
    ),
    PolicyRule(
        id="GCP-ACC-001",
        name="IAM Bindings",
        provider=CloudProvider.GCP,
        framework="SOC2",
        severity=PolicySeverity.HIGH,
        description="IAM bindings must follow least privilege",
        pattern="google_project_iam_binding",
    ),
    PolicyRule(
        id="GCP-ACC-002",
        name="Service Account Keys",
        provider=CloudProvider.GCP,
        framework="NIST",
        severity=PolicySeverity.MEDIUM,
        description="Service account keys should be managed",
        pattern="google_service_account_key",
    ),
    PolicyRule(
        id="GCP-LOG-001",
        name="Audit Logging",
        provider=CloudProvider.GCP,
        framework="SOC2",
        severity=PolicySeverity.HIGH,
        description="Audit logging must be enabled for all services",
        pattern="google_project_iam_audit_config",
    ),
    PolicyRule(
        id="GCP-LOG-002",
        name="VPC Flow Logs",
        provider=CloudProvider.GCP,
        framework="PCI-DSS",
        severity=PolicySeverity.MEDIUM,
        description="VPC flow logs must be enabled",
        pattern="google_compute_subnetwork",
    ),
    PolicyRule(
        id="GCP-NET-001",
        name="Firewall Rules",
        provider=CloudProvider.GCP,
        framework="PCI-DSS",
        severity=PolicySeverity.CRITICAL,
        description="Firewall rules must not allow unrestricted access",
        pattern="google_compute_firewall",
    ),
    PolicyRule(
        id="GCP-NET-002",
        name="Load Balancer SSL",
        provider=CloudProvider.GCP,
        framework="GDPR",
        severity=PolicySeverity.HIGH,
        description="Load balancers must use SSL certificates",
        pattern="google_compute_ssl_certificate",
    ),
    PolicyRule(
        id="GCP-ENC-003",
        name="Compute Disk Encryption",
        provider=CloudProvider.GCP,
        framework="HIPAA",
        severity=PolicySeverity.HIGH,
        description="Compute disks must be encrypted with CMEK",
        pattern="google_compute_disk",
    ),
    PolicyRule(
        id="GCP-ACC-003",
        name="OS Login Enabled",
        provider=CloudProvider.GCP,
        framework="SOC2",
        severity=PolicySeverity.MEDIUM,
        description="OS Login must be enabled on compute instances",
        pattern="google_compute_instance",
    ),
    PolicyRule(
        id="GCP-LOG-003",
        name="Sink Exports",
        provider=CloudProvider.GCP,
        framework="NIST",
        severity=PolicySeverity.LOW,
        description="Log sinks should export to external storage",
        pattern="google_logging_project_sink",
    ),
    PolicyRule(
        id="GCP-NET-003",
        name="Private Google Access",
        provider=CloudProvider.GCP,
        framework="HIPAA",
        severity=PolicySeverity.MEDIUM,
        description="Subnets should enable Private Google Access",
        pattern="google_compute_subnetwork",
    ),
    PolicyRule(
        id="GCP-ENC-004",
        name="KMS Key Rotation",
        provider=CloudProvider.GCP,
        framework="PCI-DSS",
        severity=PolicySeverity.MEDIUM,
        description="KMS keys must have rotation configured",
        pattern="google_kms_crypto_key",
    ),
    PolicyRule(
        id="GCP-ACC-004",
        name="Uniform Bucket Access",
        provider=CloudProvider.GCP,
        framework="SOC2",
        severity=PolicySeverity.MEDIUM,
        description="GCS buckets should use uniform bucket-level access",
        pattern="google_storage_bucket",
    ),
    PolicyRule(
        id="GCP-NET-004",
        name="Cloud Armor Policy",
        provider=CloudProvider.GCP,
        framework="PCI-DSS",
        severity=PolicySeverity.HIGH,
        description="Cloud Armor policies must be configured",
        pattern="google_compute_security_policy",
    ),
    PolicyRule(
        id="GCP-LOG-004",
        name="BigQuery Audit",
        provider=CloudProvider.GCP,
        framework="SOC2",
        severity=PolicySeverity.LOW,
        description="BigQuery datasets should have audit logging",
        pattern="google_bigquery_dataset",
    ),
]

_K8S_RULES = [
    PolicyRule(
        id="K8S-ACC-001",
        name="Pod Security Context",
        provider=CloudProvider.KUBERNETES,
        framework="SOC2",
        severity=PolicySeverity.HIGH,
        description="Pods must define a security context",
        pattern="securityContext",
    ),
    PolicyRule(
        id="K8S-ACC-002",
        name="Run As Non-Root",
        provider=CloudProvider.KUBERNETES,
        framework="PCI-DSS",
        severity=PolicySeverity.CRITICAL,
        description="Containers must not run as root",
        pattern="runAsNonRoot",
    ),
    PolicyRule(
        id="K8S-ACC-003",
        name="Read-Only Root FS",
        provider=CloudProvider.KUBERNETES,
        framework="NIST",
        severity=PolicySeverity.MEDIUM,
        description="Containers should use read-only root filesystem",
        pattern="readOnlyRootFilesystem",
    ),
    PolicyRule(
        id="K8S-NET-001",
        name="Network Policies",
        provider=CloudProvider.KUBERNETES,
        framework="PCI-DSS",
        severity=PolicySeverity.HIGH,
        description="Namespaces must have network policies defined",
        pattern="NetworkPolicy",
    ),
    PolicyRule(
        id="K8S-NET-002",
        name="Ingress TLS",
        provider=CloudProvider.KUBERNETES,
        framework="GDPR",
        severity=PolicySeverity.HIGH,
        description="Ingress resources must have TLS configured",
        pattern="tls",
    ),
    PolicyRule(
        id="K8S-ACC-004",
        name="Resource Limits",
        provider=CloudProvider.KUBERNETES,
        framework="SOC2",
        severity=PolicySeverity.MEDIUM,
        description="Containers must define resource limits",
        pattern="resources.limits",
    ),
    PolicyRule(
        id="K8S-ACC-005",
        name="Privilege Escalation",
        provider=CloudProvider.KUBERNETES,
        framework="PCI-DSS",
        severity=PolicySeverity.CRITICAL,
        description="Containers must not allow privilege escalation",
        pattern="allowPrivilegeEscalation",
    ),
    PolicyRule(
        id="K8S-LOG-001",
        name="Pod Logging",
        provider=CloudProvider.KUBERNETES,
        framework="SOC2",
        severity=PolicySeverity.MEDIUM,
        description="Pods should have logging sidecar or stdout logging",
        pattern="logging",
    ),
    PolicyRule(
        id="K8S-ENC-001",
        name="Secret Encryption",
        provider=CloudProvider.KUBERNETES,
        framework="HIPAA",
        severity=PolicySeverity.CRITICAL,
        description="Secrets must be encrypted at rest",
        pattern="EncryptionConfiguration",
    ),
    PolicyRule(
        id="K8S-ACC-006",
        name="Service Account Token",
        provider=CloudProvider.KUBERNETES,
        framework="SOC2",
        severity=PolicySeverity.MEDIUM,
        description="Pods should not auto-mount service account tokens",
        pattern="automountServiceAccountToken",
    ),
    PolicyRule(
        id="K8S-NET-003",
        name="Host Network Disabled",
        provider=CloudProvider.KUBERNETES,
        framework="NIST",
        severity=PolicySeverity.HIGH,
        description="Pods must not use host networking",
        pattern="hostNetwork",
    ),
    PolicyRule(
        id="K8S-ACC-007",
        name="Capabilities Dropped",
        provider=CloudProvider.KUBERNETES,
        framework="PCI-DSS",
        severity=PolicySeverity.HIGH,
        description="Containers should drop all capabilities",
        pattern="capabilities.drop",
    ),
    PolicyRule(
        id="K8S-ENC-002",
        name="TLS Certificates",
        provider=CloudProvider.KUBERNETES,
        framework="PCI-DSS",
        severity=PolicySeverity.HIGH,
        description="Services must use valid TLS certificates",
        pattern="cert-manager",
    ),
    PolicyRule(
        id="K8S-LOG-002",
        name="Audit Policy",
        provider=CloudProvider.KUBERNETES,
        framework="SOC2",
        severity=PolicySeverity.MEDIUM,
        description="Cluster must have audit policy configured",
        pattern="audit-policy",
    ),
    PolicyRule(
        id="K8S-NET-004",
        name="External Traffic Policy",
        provider=CloudProvider.KUBERNETES,
        framework="SOC2",
        severity=PolicySeverity.LOW,
        description="Services should define external traffic policy",
        pattern="externalTrafficPolicy",
    ),
    PolicyRule(
        id="K8S-ACC-008",
        name="Image Pull Policy",
        provider=CloudProvider.KUBERNETES,
        framework="SOC2",
        severity=PolicySeverity.LOW,
        description="Containers should use Always image pull policy",
        pattern="imagePullPolicy",
    ),
]

_ALL_RULES: dict[CloudProvider, list[PolicyRule]] = {
    CloudProvider.AWS: _AWS_RULES,
    CloudProvider.AZURE: _AZURE_RULES,
    CloudProvider.GCP: _GCP_RULES,
    CloudProvider.KUBERNETES: _K8S_RULES,
}

# Merge extended rules

_ALL_RULES[CloudProvider.AWS].extend(AWS_EXTENDED_RULES)
_ALL_RULES[CloudProvider.AZURE].extend(AZURE_EXTENDED_RULES)
_ALL_RULES[CloudProvider.GCP].extend(GCP_EXTENDED_RULES)
_ALL_RULES[CloudProvider.KUBERNETES].extend(K8S_EXTENDED_RULES)


class IaCPolicyEngine:
    """Service for scanning Infrastructure as Code against compliance policies."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._custom_rules: list[PolicyRule] = []
        self._scan_history: list[IaCScanResult] = []

    def _get_rules(self, provider: CloudProvider | None = None) -> list[PolicyRule]:
        """Get all rules, optionally filtered by provider."""
        rules: list[PolicyRule] = []
        if provider:
            rules = list(_ALL_RULES.get(provider, []))
        else:
            for provider_rules in _ALL_RULES.values():
                rules.extend(provider_rules)
        rules.extend(r for r in self._custom_rules if provider is None or r.provider == provider)
        return rules

    def _simulate_scan(self, provider: CloudProvider, file_count: int) -> IaCScanResult:
        """Simulate a scan with deterministic violations."""
        rules = self._get_rules(provider)
        violations: list[IaCViolation] = []

        # Deterministic: every 3rd rule produces a violation
        for i, rule in enumerate(rules):
            if i % 3 == 0:
                violations.append(
                    IaCViolation(
                        rule_id=rule.id,
                        resource_type=rule.pattern,
                        resource_name=f"resource_{rule.id.lower().replace('-', '_')}",
                        provider=provider,
                        severity=rule.severity,
                        framework=rule.framework,
                        description=rule.description,
                        remediation=f"Update {rule.pattern} configuration to comply with {rule.name}",
                        file_path=f"infra/{provider.value}/main.tf",
                        line_number=(i + 1) * 10,
                    )
                )

        result = IaCScanResult(
            provider=provider,
            files_scanned=file_count,
            violations=violations,
            pass_count=len(rules) - len(violations),
            fail_count=len(violations),
            scan_duration_ms=len(rules) * 45,
        )
        self._scan_history.append(result)
        return result

    async def scan_terraform(self, provider: CloudProvider, file_count: int = 10) -> IaCScanResult:
        """Scan Terraform files for policy violations."""
        result = self._simulate_scan(provider, file_count)
        logger.info(
            "Terraform scan complete", provider=provider.value, violations=result.fail_count
        )
        return result

    async def scan_kubernetes(self, file_count: int = 5) -> IaCScanResult:
        """Scan Kubernetes manifests for policy violations."""
        result = self._simulate_scan(CloudProvider.KUBERNETES, file_count)
        logger.info("Kubernetes scan complete", violations=result.fail_count)
        return result

    async def scan_cloudformation(self, file_count: int = 8) -> IaCScanResult:
        """Scan CloudFormation templates for policy violations."""
        result = self._simulate_scan(CloudProvider.AWS, file_count)
        logger.info("CloudFormation scan complete", violations=result.fail_count)
        return result

    async def list_rules(
        self,
        provider: CloudProvider | None = None,
        framework: str | None = None,
        severity: PolicySeverity | None = None,
    ) -> list[PolicyRule]:
        """List policy rules with optional filters."""
        rules = self._get_rules(provider)
        if framework:
            rules = [r for r in rules if r.framework.lower() == framework.lower()]
        if severity:
            rules = [r for r in rules if r.severity == severity]
        return rules

    async def get_rule(self, rule_id: str) -> PolicyRule | None:
        """Get a specific rule by ID."""
        all_rules = self._get_rules()
        return next((r for r in all_rules if r.id == rule_id), None)

    async def add_custom_rule(self, rule: PolicyRule) -> PolicyRule:
        """Add a custom policy rule."""
        self._custom_rules.append(rule)
        logger.info("Custom rule added", rule_id=rule.id, provider=rule.provider.value)
        return rule

    async def get_scan_history(self, provider: CloudProvider | None = None) -> list[IaCScanResult]:
        """Get scan history with optional provider filter."""
        results = list(self._scan_history)
        if provider:
            results = [r for r in results if r.provider == provider]
        return results
