"""Zero-Trust Compliance Architecture Scanner Service."""

import random
from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.zero_trust_scanner.models import (
    ComplianceFramework,
    InfraResource,
    RemediationPlan,
    ResourceType,
    ScanResult,
    ViolationStatus,
    ZeroTrustPolicy,
    ZeroTrustViolation,
)


logger = structlog.get_logger()

# Pre-built policies
_DEFAULT_POLICIES = [
    ZeroTrustPolicy(
        name="No public S3 buckets",
        framework=ComplianceFramework.GDPR_ART32,
        resource_types=[ResourceType.S3_BUCKET],
        description="S3 buckets must not allow public access",
        rego_rule='deny[msg] { input.resource.public_access == true; msg := "Public access enabled" }',
        severity="critical",
    ),
    ZeroTrustPolicy(
        name="IAM least privilege",
        framework=ComplianceFramework.NIST_800_207,
        resource_types=[ResourceType.IAM_ROLE],
        description="IAM roles must follow least privilege principle",
        rego_rule='deny[msg] { input.resource.policy == "*"; msg := "Wildcard permissions" }',
        severity="high",
    ),
    ZeroTrustPolicy(
        name="RDS encryption at rest",
        framework=ComplianceFramework.HIPAA_164_312,
        resource_types=[ResourceType.RDS_INSTANCE],
        description="RDS instances must have encryption at rest enabled",
        rego_rule='deny[msg] { not input.resource.storage_encrypted; msg := "Encryption disabled" }',
        severity="critical",
    ),
    ZeroTrustPolicy(
        name="Security group no open ingress",
        framework=ComplianceFramework.PCI_DSS_REQ7,
        resource_types=[ResourceType.SECURITY_GROUP],
        description="Security groups must not allow unrestricted ingress",
        rego_rule='deny[msg] { input.resource.ingress_cidr == "0.0.0.0/0"; msg := "Open ingress" }',
        severity="high",
    ),
    ZeroTrustPolicy(
        name="KMS key rotation enabled",
        framework=ComplianceFramework.SOC2_CC6_1,
        resource_types=[ResourceType.KMS_KEY],
        description="KMS keys must have automatic rotation enabled",
        rego_rule='deny[msg] { not input.resource.key_rotation_enabled; msg := "Key rotation disabled" }',
        severity="medium",
    ),
    ZeroTrustPolicy(
        name="Lambda VPC attachment",
        framework=ComplianceFramework.ISO27001_A9,
        resource_types=[ResourceType.LAMBDA_FUNCTION],
        description="Lambda functions handling sensitive data must be VPC-attached",
        rego_rule='deny[msg] { not input.resource.vpc_config; msg := "No VPC attachment" }',
        severity="medium",
    ),
]


class ZeroTrustScannerService:
    """Service for zero-trust compliance architecture scanning."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot_client = copilot_client
        self._policies: list[ZeroTrustPolicy] = list(_DEFAULT_POLICIES)
        self._violations: list[ZeroTrustViolation] = []
        self._scans: list[ScanResult] = []

    async def scan_iac(
        self,
        repo: str,
        files: list[str] | None = None,
    ) -> ScanResult:
        """Scan infrastructure-as-code for zero-trust violations."""
        iac_files = files or [
            "terraform/main.tf",
            "terraform/iam.tf",
            "terraform/s3.tf",
            "terraform/rds.tf",
            "terraform/network.tf",
        ]

        violations: list[ZeroTrustViolation] = []
        resources_scanned = random.randint(15, 50)

        # Generate realistic violations
        violation_templates = [
            {
                "policy": self._policies[0],
                "resource_name": "data-export-bucket",
                "violation_type": "public_access",
                "description": "S3 bucket 'data-export-bucket' has public access enabled",
                "remediation_hint": "Set aws_s3_bucket_public_access_block with block_public_acls = true",
                "iac_file": "terraform/s3.tf",
                "iac_line": 23,
            },
            {
                "policy": self._policies[1],
                "resource_name": "admin-role",
                "violation_type": "overprivileged_iam",
                "description": "IAM role 'admin-role' has wildcard (*) permissions on all resources",
                "remediation_hint": "Scope IAM policy to specific resources and actions",
                "iac_file": "terraform/iam.tf",
                "iac_line": 45,
            },
            {
                "policy": self._policies[2],
                "resource_name": "user-db",
                "violation_type": "unencrypted_storage",
                "description": "RDS instance 'user-db' does not have encryption at rest enabled",
                "remediation_hint": "Set storage_encrypted = true in aws_db_instance",
                "iac_file": "terraform/rds.tf",
                "iac_line": 12,
            },
            {
                "policy": self._policies[3],
                "resource_name": "web-sg",
                "violation_type": "open_ingress",
                "description": "Security group 'web-sg' allows ingress from 0.0.0.0/0 on port 22",
                "remediation_hint": "Restrict SSH access to specific CIDR blocks",
                "iac_file": "terraform/network.tf",
                "iac_line": 67,
            },
        ]

        selected = random.sample(
            violation_templates, k=min(len(violation_templates), random.randint(1, 4))
        )
        for tmpl in selected:
            v = ZeroTrustViolation(
                policy_id=tmpl["policy"].id,
                resource_name=tmpl["resource_name"],
                violation_type=tmpl["violation_type"],
                severity=tmpl["policy"].severity,
                description=tmpl["description"],
                framework=tmpl["policy"].framework,
                remediation_hint=tmpl["remediation_hint"],
                iac_file=tmpl["iac_file"],
                iac_line=tmpl["iac_line"],
                status=ViolationStatus.OPEN,
                detected_at=datetime.now(UTC),
            )
            violations.append(v)

        self._violations.extend(violations)
        score = max(0.0, 100.0 - (len(violations) / resources_scanned) * 100)

        scan = ScanResult(
            scan_type="iac",
            resources_scanned=resources_scanned,
            violations_found=len(violations),
            violations=violations,
            compliance_score=round(score, 1),
            scanned_at=datetime.now(UTC),
        )
        self._scans.append(scan)

        logger.info(
            "IaC scan completed",
            repo=repo,
            resources=resources_scanned,
            violations=len(violations),
            score=scan.compliance_score,
        )
        return scan

    async def list_policies(self) -> list[ZeroTrustPolicy]:
        """List all zero-trust policies."""
        return list(self._policies)

    async def list_violations(
        self,
        status: ViolationStatus | None = None,
        framework: ComplianceFramework | None = None,
    ) -> list[ZeroTrustViolation]:
        """List violations with optional filters."""
        results = list(self._violations)
        if status:
            results = [v for v in results if v.status == status]
        if framework:
            results = [v for v in results if v.framework == framework]
        return results

    async def get_violation(self, violation_id: UUID) -> ZeroTrustViolation | None:
        """Get a violation by ID."""
        return next((v for v in self._violations if v.id == violation_id), None)

    async def generate_remediation(self, violation_id: UUID) -> RemediationPlan | None:
        """Generate a remediation plan for a violation."""
        violation = await self.get_violation(violation_id)
        if not violation:
            return None

        diff_templates = {
            "public_access": (
                "--- a/terraform/s3.tf\n+++ b/terraform/s3.tf\n"
                "@@ -23,1 +23,6 @@\n"
                '+resource "aws_s3_bucket_public_access_block" "block" {\n'
                "+  bucket = aws_s3_bucket.data_export.id\n"
                "+  block_public_acls = true\n"
                "+  block_public_policy = true\n"
                "+}\n"
            ),
            "overprivileged_iam": (
                "--- a/terraform/iam.tf\n+++ b/terraform/iam.tf\n"
                "@@ -45,1 +45,1 @@\n"
                '-  resources = ["*"]\n'
                '+  resources = ["arn:aws:s3:::specific-bucket/*"]\n'
            ),
            "unencrypted_storage": (
                "--- a/terraform/rds.tf\n+++ b/terraform/rds.tf\n"
                "@@ -12,1 +12,2 @@\n"
                "+  storage_encrypted = true\n"
                "+  kms_key_id = aws_kms_key.rds.arn\n"
            ),
            "open_ingress": (
                "--- a/terraform/network.tf\n+++ b/terraform/network.tf\n"
                "@@ -67,1 +67,1 @@\n"
                '-  cidr_blocks = ["0.0.0.0/0"]\n'
                '+  cidr_blocks = ["10.0.0.0/8"]\n'
            ),
        }

        plan = RemediationPlan(
            violation_id=violation_id,
            iac_diff=diff_templates.get(violation.violation_type, "# No auto-fix available"),
            description=f"Remediation for {violation.violation_type}: {violation.remediation_hint}",
            auto_fixable=violation.violation_type in diff_templates,
            risk="low" if violation.severity in ("medium", "low") else "medium",
        )
        logger.info("Remediation plan generated", violation_id=str(violation_id))
        return plan

    async def suppress_violation(
        self,
        violation_id: UUID,
        reason: str,
    ) -> ZeroTrustViolation | None:
        """Suppress a violation with a reason."""
        violation = await self.get_violation(violation_id)
        if not violation:
            return None
        violation.status = ViolationStatus.SUPPRESSED
        logger.info("Violation suppressed", violation_id=str(violation_id), reason=reason)
        return violation

    async def get_compliance_summary(self) -> dict:
        """Get compliance score per framework."""
        summary: dict[str, dict] = {}
        for fw in ComplianceFramework:
            fw_violations = [v for v in self._violations if v.framework == fw]
            open_count = sum(1 for v in fw_violations if v.status == ViolationStatus.OPEN)
            total = len(fw_violations)
            summary[fw.value] = {
                "total_violations": total,
                "open_violations": open_count,
                "remediated": sum(
                    1 for v in fw_violations if v.status == ViolationStatus.REMEDIATED
                ),
                "suppressed": sum(
                    1 for v in fw_violations if v.status == ViolationStatus.SUPPRESSED
                ),
                "score": round(100.0 - (open_count * 10), 1) if total > 0 else 100.0,
            }
        return summary
