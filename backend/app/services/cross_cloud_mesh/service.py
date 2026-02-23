"""Cross-Cloud Mesh Service."""

from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cross_cloud_mesh.models import (
    CloudAccount,
    CloudProvider,
    CloudResource,
    ComplianceStatus,
    CrossCloudPosture,
    CrossCloudStats,
    ResourceType,
)


logger = structlog.get_logger()

# Deterministic resource definitions per provider
_PROVIDER_RESOURCES: dict[str, list[dict]] = {
    "aws": [
        {"type": ResourceType.COMPUTE, "name": "prod-api-cluster", "region": "us-east-1", "status": ComplianceStatus.COMPLIANT, "controls": ["SOC2-CC6.1", "CIS-AWS-2.1"]},
        {"type": ResourceType.STORAGE, "name": "data-lake-s3", "region": "us-east-1", "status": ComplianceStatus.COMPLIANT, "controls": ["SOC2-CC6.3", "GDPR-Art32"]},
        {"type": ResourceType.DATABASE, "name": "rds-primary", "region": "us-east-1", "status": ComplianceStatus.COMPLIANT, "controls": ["SOC2-CC6.1", "PCI-DSS-3.4"]},
        {"type": ResourceType.NETWORK, "name": "vpc-production", "region": "us-east-1", "status": ComplianceStatus.NON_COMPLIANT, "controls": ["SOC2-CC6.6"], "findings": [{"severity": "high", "title": "VPC flow logs not enabled", "resource": "vpc-production"}]},
        {"type": ResourceType.IDENTITY, "name": "iam-admin-role", "region": "global", "status": ComplianceStatus.NON_COMPLIANT, "controls": ["SOC2-CC6.2", "CIS-AWS-1.16"], "findings": [{"severity": "critical", "title": "MFA not enforced for admin role", "resource": "iam-admin-role"}]},
        {"type": ResourceType.ENCRYPTION, "name": "kms-master-key", "region": "us-east-1", "status": ComplianceStatus.COMPLIANT, "controls": ["SOC2-CC6.7", "PCI-DSS-3.5"]},
    ],
    "azure": [
        {"type": ResourceType.COMPUTE, "name": "aks-prod-cluster", "region": "westeurope", "status": ComplianceStatus.COMPLIANT, "controls": ["SOC2-CC6.1", "CIS-Azure-7.1"]},
        {"type": ResourceType.STORAGE, "name": "blob-compliance-docs", "region": "westeurope", "status": ComplianceStatus.COMPLIANT, "controls": ["SOC2-CC6.3", "GDPR-Art32"]},
        {"type": ResourceType.DATABASE, "name": "cosmosdb-main", "region": "westeurope", "status": ComplianceStatus.NON_COMPLIANT, "controls": ["SOC2-CC6.1"], "findings": [{"severity": "medium", "title": "Database audit logging not enabled", "resource": "cosmosdb-main"}]},
        {"type": ResourceType.NETWORK, "name": "vnet-production", "region": "westeurope", "status": ComplianceStatus.COMPLIANT, "controls": ["SOC2-CC6.6", "CIS-Azure-6.1"]},
        {"type": ResourceType.IDENTITY, "name": "aad-privileged-group", "region": "global", "status": ComplianceStatus.COMPLIANT, "controls": ["SOC2-CC6.2", "CIS-Azure-1.23"]},
    ],
    "gcp": [
        {"type": ResourceType.COMPUTE, "name": "gke-prod", "region": "europe-west1", "status": ComplianceStatus.COMPLIANT, "controls": ["SOC2-CC6.1", "CIS-GCP-7.1"]},
        {"type": ResourceType.STORAGE, "name": "gcs-data-archive", "region": "europe-west1", "status": ComplianceStatus.NON_COMPLIANT, "controls": ["SOC2-CC6.3"], "findings": [{"severity": "medium", "title": "Bucket uniform access not enabled", "resource": "gcs-data-archive"}]},
        {"type": ResourceType.DATABASE, "name": "cloudsql-analytics", "region": "europe-west1", "status": ComplianceStatus.COMPLIANT, "controls": ["SOC2-CC6.1", "PCI-DSS-3.4"]},
        {"type": ResourceType.IDENTITY, "name": "sa-deployment-admin", "region": "global", "status": ComplianceStatus.NON_COMPLIANT, "controls": ["SOC2-CC6.2", "CIS-GCP-1.15"], "findings": [{"severity": "high", "title": "Service account key not rotated in 90+ days", "resource": "sa-deployment-admin"}]},
    ],
}


class CrossCloudMeshService:
    """Cross-cloud compliance posture management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._accounts: dict[UUID, CloudAccount] = {}
        self._resources: dict[UUID, CloudResource] = {}
        self._account_resources: dict[UUID, list[UUID]] = {}
        self._seed_data()

    def _seed_data(self) -> None:
        """Seed cloud accounts for AWS, Azure, and GCP."""
        accounts = [
            CloudAccount(
                provider=CloudProvider.AWS,
                account_id="123456789012",
                name="Production AWS",
                regions=["us-east-1", "us-west-2", "eu-west-1"],
                compliance_score=0.0,
                last_scan_at=datetime(2025, 3, 15, 8, 0, tzinfo=UTC),
            ),
            CloudAccount(
                provider=CloudProvider.AZURE,
                account_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                name="Production Azure",
                regions=["westeurope", "northeurope", "eastus"],
                compliance_score=0.0,
                last_scan_at=datetime(2025, 3, 15, 8, 30, tzinfo=UTC),
            ),
            CloudAccount(
                provider=CloudProvider.GCP,
                account_id="compliance-prod-384712",
                name="Production GCP",
                regions=["europe-west1", "us-central1"],
                compliance_score=0.0,
                last_scan_at=datetime(2025, 3, 15, 9, 0, tzinfo=UTC),
            ),
        ]

        for account in accounts:
            self._accounts[account.id] = account
            resources = self._generate_resources(account)
            self._account_resources[account.id] = [r.id for r in resources]
            account.resources_discovered = len(resources)
            account.compliance_score = self._compute_account_score(resources)

        logger.info(
            "Cross-cloud mesh seeded",
            account_count=len(self._accounts),
            resource_count=len(self._resources),
        )

    def _generate_resources(self, account: CloudAccount) -> list[CloudResource]:
        """Generate deterministic resources for an account based on provider."""
        provider_key = account.provider.value
        resource_defs = _PROVIDER_RESOURCES.get(provider_key, [])
        resources: list[CloudResource] = []

        for rdef in resource_defs:
            resource = CloudResource(
                provider=account.provider,
                resource_type=rdef["type"],
                name=rdef["name"],
                region=rdef["region"],
                compliance_status=rdef["status"],
                controls_mapped=rdef["controls"],
                findings=rdef.get("findings", []),
            )
            self._resources[resource.id] = resource
            resources.append(resource)

        return resources

    def _compute_account_score(self, resources: list[CloudResource]) -> float:
        """Compute compliance score for a set of resources."""
        if not resources:
            return 0.0
        compliant = sum(1 for r in resources if r.compliance_status == ComplianceStatus.COMPLIANT)
        return round((compliant / len(resources)) * 100, 1)

    async def connect_account(
        self,
        provider: str,
        account_id: str,
        name: str,
        regions: list[str],
    ) -> CloudAccount:
        """Connect a new cloud account."""
        account = CloudAccount(
            provider=CloudProvider(provider),
            account_id=account_id,
            name=name,
            regions=regions,
            last_scan_at=datetime.now(UTC),
        )
        self._accounts[account.id] = account
        self._account_resources[account.id] = []

        logger.info("Cloud account connected", account_id=account_id, provider=provider)
        return account

    async def discover_resources(self, account_id: UUID) -> list[CloudResource]:
        """Discover resources for an account, generating deterministic results per provider."""
        account = self._accounts.get(account_id)
        if not account:
            msg = f"Account {account_id} not found"
            raise ValueError(msg)

        existing_ids = self._account_resources.get(account_id, [])
        if existing_ids:
            return [self._resources[rid] for rid in existing_ids if rid in self._resources]

        resources = self._generate_resources(account)
        self._account_resources[account_id] = [r.id for r in resources]
        account.resources_discovered = len(resources)
        account.compliance_score = self._compute_account_score(resources)
        account.last_scan_at = datetime.now(UTC)

        logger.info(
            "Resources discovered",
            account_id=str(account_id),
            count=len(resources),
        )
        return resources

    async def get_posture(self) -> CrossCloudPosture:
        """Get aggregated cross-cloud compliance posture."""
        all_resources = list(self._resources.values())
        total = len(all_resources)

        if total == 0:
            return CrossCloudPosture()

        compliant = sum(1 for r in all_resources if r.compliance_status == ComplianceStatus.COMPLIANT)
        non_compliant = sum(1 for r in all_resources if r.compliance_status == ComplianceStatus.NON_COMPLIANT)

        by_provider: dict[str, float] = {}
        provider_resources: dict[str, list[CloudResource]] = {}
        for r in all_resources:
            provider_resources.setdefault(r.provider.value, []).append(r)
        for prov, resources in provider_resources.items():
            c = sum(1 for r in resources if r.compliance_status == ComplianceStatus.COMPLIANT)
            by_provider[prov] = round((c / len(resources)) * 100, 1)

        by_resource_type: dict[str, int] = {}
        for r in all_resources:
            by_resource_type[r.resource_type.value] = by_resource_type.get(r.resource_type.value, 0) + 1

        all_findings = []
        for r in all_resources:
            all_findings.extend(r.findings)

        overall_score = round((compliant / total) * 100, 1)

        return CrossCloudPosture(
            overall_score=overall_score,
            by_provider=by_provider,
            by_resource_type=by_resource_type,
            total_resources=total,
            non_compliant=non_compliant,
            findings=all_findings,
        )

    async def scan_account(self, account_id: UUID) -> CloudAccount:
        """Re-scan an account for compliance."""
        account = self._accounts.get(account_id)
        if not account:
            msg = f"Account {account_id} not found"
            raise ValueError(msg)

        resource_ids = self._account_resources.get(account_id, [])
        resources = [self._resources[rid] for rid in resource_ids if rid in self._resources]
        account.compliance_score = self._compute_account_score(resources)
        account.last_scan_at = datetime.now(UTC)

        logger.info("Account scanned", account_id=str(account_id), score=account.compliance_score)
        return account

    async def list_accounts(
        self,
        provider: CloudProvider | None = None,
    ) -> list[CloudAccount]:
        """List cloud accounts with optional provider filter."""
        accounts = list(self._accounts.values())

        if provider is not None:
            accounts = [a for a in accounts if a.provider == provider]

        return accounts

    async def get_stats(self) -> CrossCloudStats:
        """Get cross-cloud mesh statistics."""
        accounts = list(self._accounts.values())
        all_resources = list(self._resources.values())

        by_provider: dict[str, int] = {}
        for a in accounts:
            by_provider[a.provider.value] = by_provider.get(a.provider.value, 0) + 1

        total = len(all_resources)
        compliant = sum(1 for r in all_resources if r.compliance_status == ComplianceStatus.COMPLIANT)
        overall_pct = round((compliant / total) * 100, 1) if total > 0 else 0.0

        findings_count = sum(len(r.findings) for r in all_resources)

        return CrossCloudStats(
            total_accounts=len(accounts),
            total_resources=total,
            by_provider=by_provider,
            overall_compliance_pct=overall_pct,
            findings_count=findings_count,
        )
