"""Compliance Data Residency Map service.

Maps data flows across jurisdictions and flags cross-border transfer
violations (Schrems II, PIPL, PDPA).
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession


logger = structlog.get_logger()


class TransferStatus(str, Enum):
    COMPLIANT = "compliant"
    VIOLATION = "violation"
    REVIEW_NEEDED = "review_needed"
    UNKNOWN = "unknown"


@dataclass
class Jurisdiction:
    code: str = ""
    name: str = ""
    region: str = ""
    applicable_laws: list[str] = field(default_factory=list)
    adequacy_decisions: list[str] = field(default_factory=list)
    requires_local_storage: bool = False


@dataclass
class DataFlow:
    id: UUID = field(default_factory=uuid4)
    source_jurisdiction: str = ""
    destination_jurisdiction: str = ""
    data_types: list[str] = field(default_factory=list)
    service_name: str = ""
    transfer_mechanism: str = ""  # SCCs, adequacy, BCRs, consent
    status: TransferStatus = TransferStatus.UNKNOWN
    violations: list[str] = field(default_factory=list)


@dataclass
class ResidencyReport:
    total_flows: int = 0
    compliant: int = 0
    violations: int = 0
    review_needed: int = 0
    flows: list[DataFlow] = field(default_factory=list)
    jurisdictions_involved: list[str] = field(default_factory=list)
    generated_at: datetime | None = None


# Jurisdiction database
_JURISDICTIONS: dict[str, Jurisdiction] = {
    "EU": Jurisdiction(
        "EU", "European Union", "Europe", ["GDPR"], ["JP", "KR", "UK", "CA", "NZ"], False
    ),
    "US": Jurisdiction(
        "US", "United States", "North America", ["CCPA", "HIPAA", "GLBA"], [], False
    ),
    "UK": Jurisdiction("UK", "United Kingdom", "Europe", ["UK GDPR", "DPA 2018"], ["EU"], False),
    "CN": Jurisdiction("CN", "China", "Asia", ["PIPL"], [], True),
    "IN": Jurisdiction("IN", "India", "Asia", ["DPDP"], [], False),
    "SG": Jurisdiction("SG", "Singapore", "Asia", ["PDPA"], [], False),
    "JP": Jurisdiction("JP", "Japan", "Asia", ["APPI"], ["EU"], False),
    "KR": Jurisdiction("KR", "South Korea", "Asia", ["PIPA"], ["EU"], False),
    "BR": Jurisdiction("BR", "Brazil", "South America", ["LGPD"], [], False),
    "AU": Jurisdiction("AU", "Australia", "Oceania", ["Privacy Act"], [], False),
    "CA": Jurisdiction("CA", "Canada", "North America", ["PIPEDA"], ["EU"], False),
}

# AWS region to jurisdiction mapping
_CLOUD_REGION_MAP: dict[str, str] = {
    "us-east-1": "US",
    "us-west-2": "US",
    "us-gov-west-1": "US",
    "eu-west-1": "EU",
    "eu-central-1": "EU",
    "eu-north-1": "EU",
    "ap-southeast-1": "SG",
    "ap-northeast-1": "JP",
    "ap-south-1": "IN",
    "ap-northeast-2": "KR",
    "sa-east-1": "BR",
    "ca-central-1": "CA",
    "cn-north-1": "CN",
    "cn-northwest-1": "CN",
    "ap-southeast-2": "AU",
    "eu-west-2": "UK",
}


class ResidencyMapService:
    """Maps data flows across jurisdictions and detects violations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._flows: list[DataFlow] = []
        self._init_demo_flows()

    def _init_demo_flows(self) -> None:
        demo = [
            (
                "EU",
                "US",
                ["personal_data", "email"],
                "AWS S3",
                "SCCs",
                TransferStatus.COMPLIANT,
                [],
            ),
            (
                "EU",
                "CN",
                ["personal_data"],
                "Analytics API",
                "",
                TransferStatus.VIOLATION,
                ["GDPR Chapter V: No adequacy decision for China, no SCCs in place"],
            ),
            (
                "US",
                "IN",
                ["health_data"],
                "Support System",
                "consent",
                TransferStatus.REVIEW_NEEDED,
                ["HIPAA: Verify BAA with Indian processor"],
            ),
            (
                "EU",
                "UK",
                ["personal_data", "financial"],
                "Payment Gateway",
                "adequacy",
                TransferStatus.COMPLIANT,
                [],
            ),
            ("EU", "JP", ["personal_data"], "CRM", "adequacy", TransferStatus.COMPLIANT, []),
            (
                "SG",
                "US",
                ["personal_data"],
                "Cloud Hosting",
                "contractual",
                TransferStatus.COMPLIANT,
                [],
            ),
            (
                "CN",
                "US",
                ["personal_data"],
                "SaaS Platform",
                "",
                TransferStatus.VIOLATION,
                ["PIPL Art.38: Cross-border transfer requires security assessment"],
            ),
        ]
        for src, dst, types, svc, mech, status, violations in demo:
            self._flows.append(
                DataFlow(
                    source_jurisdiction=src,
                    destination_jurisdiction=dst,
                    data_types=types,
                    service_name=svc,
                    transfer_mechanism=mech,
                    status=status,
                    violations=violations,
                )
            )

    async def get_residency_report(self) -> ResidencyReport:
        """Generate a data residency report with all flows and their status."""
        jurisdictions = set()
        for f in self._flows:
            jurisdictions.add(f.source_jurisdiction)
            jurisdictions.add(f.destination_jurisdiction)

        return ResidencyReport(
            total_flows=len(self._flows),
            compliant=sum(1 for f in self._flows if f.status == TransferStatus.COMPLIANT),
            violations=sum(1 for f in self._flows if f.status == TransferStatus.VIOLATION),
            review_needed=sum(1 for f in self._flows if f.status == TransferStatus.REVIEW_NEEDED),
            flows=self._flows,
            jurisdictions_involved=sorted(jurisdictions),
            generated_at=datetime.now(UTC),
        )

    async def check_transfer(
        self, source: str, destination: str, data_types: list[str]
    ) -> DataFlow:
        """Check if a specific cross-border transfer is compliant."""
        src_j = _JURISDICTIONS.get(source.upper())
        dst_j = _JURISDICTIONS.get(destination.upper())

        violations: list[str] = []
        status = TransferStatus.COMPLIANT

        if not src_j or not dst_j:
            return DataFlow(
                source_jurisdiction=source,
                destination_jurisdiction=destination,
                data_types=data_types,
                status=TransferStatus.UNKNOWN,
                violations=["Unknown jurisdiction"],
            )

        # Check adequacy
        has_adequacy = destination.upper() in src_j.adequacy_decisions

        # Check local storage requirements
        if src_j.requires_local_storage:
            violations.append(
                f"{src_j.name} requires local data storage — cross-border transfer restricted"
            )
            status = TransferStatus.VIOLATION

        # GDPR specific
        if "GDPR" in src_j.applicable_laws and not has_adequacy:
            violations.append(
                f"No EU adequacy decision for {dst_j.name}. Requires SCCs, BCRs, or derogation."
            )
            status = TransferStatus.REVIEW_NEEDED

        # Health data
        if "health_data" in data_types or "phi" in data_types:
            if "HIPAA" in src_j.applicable_laws:
                violations.append("HIPAA: Verify Business Associate Agreement with data processor")
                if status == TransferStatus.COMPLIANT:
                    status = TransferStatus.REVIEW_NEEDED

        if violations and status == TransferStatus.COMPLIANT:
            status = TransferStatus.REVIEW_NEEDED

        return DataFlow(
            source_jurisdiction=source,
            destination_jurisdiction=destination,
            data_types=data_types,
            status=status,
            violations=violations,
        )

    async def resolve_cloud_region(self, region: str) -> str:
        """Map a cloud region to its jurisdiction."""
        return _CLOUD_REGION_MAP.get(region, "UNKNOWN")

    async def get_jurisdictions(self) -> list[Jurisdiction]:
        """List all known jurisdictions and their laws."""
        return list(_JURISDICTIONS.values())
