"""Automated Evidence Generation Service."""

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.evidence_generation.models import (
    ControlMapping,
    ControlStatus,
    EvidenceFramework,
    EvidenceFreshness,
    EvidenceItem,
    EvidencePackage,
    EvidenceStats,
)


logger = structlog.get_logger()

_SOC2_CONTROLS: list[dict] = [
    {"id": "CC1.1", "name": "COSO Principle 1: Integrity and Ethical Values", "category": "Control Environment"},
    {"id": "CC2.1", "name": "Information and Communication", "category": "Communication"},
    {"id": "CC3.1", "name": "Risk Assessment", "category": "Risk Assessment"},
    {"id": "CC5.1", "name": "Control Activities — Logical Access", "category": "Logical Access"},
    {"id": "CC5.2", "name": "Control Activities — System Operations", "category": "System Operations"},
    {"id": "CC6.1", "name": "Logical and Physical Access Controls", "category": "Access Control"},
    {"id": "CC6.2", "name": "System Account Management", "category": "Access Control"},
    {"id": "CC6.3", "name": "Role-Based Access", "category": "Access Control"},
    {"id": "CC7.1", "name": "System Monitoring", "category": "Monitoring"},
    {"id": "CC7.2", "name": "Incident Detection", "category": "Monitoring"},
    {"id": "CC7.3", "name": "Incident Response", "category": "Incident Response"},
    {"id": "CC8.1", "name": "Change Management", "category": "Change Management"},
    {"id": "CC9.1", "name": "Risk Mitigation", "category": "Risk Management"},
]

_ISO27001_CONTROLS: list[dict] = [
    {"id": "A.5.1", "name": "Policies for Information Security", "category": "Organizational"},
    {"id": "A.6.1", "name": "Internal Organization", "category": "Organizational"},
    {"id": "A.7.1", "name": "Human Resource Security", "category": "People"},
    {"id": "A.8.1", "name": "Asset Management", "category": "Asset"},
    {"id": "A.9.1", "name": "Access Control Policy", "category": "Access"},
    {"id": "A.10.1", "name": "Cryptographic Controls", "category": "Crypto"},
    {"id": "A.12.1", "name": "Operational Security", "category": "Operations"},
    {"id": "A.12.4", "name": "Logging and Monitoring", "category": "Operations"},
    {"id": "A.13.1", "name": "Network Security", "category": "Network"},
    {"id": "A.14.1", "name": "Secure Development", "category": "Development"},
    {"id": "A.16.1", "name": "Incident Management", "category": "Incident"},
    {"id": "A.18.1", "name": "Legal Compliance", "category": "Compliance"},
]


class EvidenceGenerationService:
    """Automated SOC 2 / ISO 27001 evidence generation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._items: list[EvidenceItem] = []
        self._packages: dict[str, EvidencePackage] = {}

    def _get_controls(self, framework: EvidenceFramework) -> list[dict]:
        if framework == EvidenceFramework.SOC2:
            return _SOC2_CONTROLS
        if framework == EvidenceFramework.ISO27001:
            return _ISO27001_CONTROLS
        return _SOC2_CONTROLS[:8]

    async def generate_evidence_package(self, framework: str) -> EvidencePackage:
        fw = EvidenceFramework(framework)
        controls = self._get_controls(fw)
        now = datetime.now(UTC)
        mappings = []
        items = []

        for i, ctrl in enumerate(controls):
            # Simulate evidence collection based on control type
            has_evidence = i < len(controls) * 0.8  # 80% coverage
            status = ControlStatus.MET if has_evidence else ControlStatus.PARTIALLY_MET
            freshness = EvidenceFreshness.FRESH if has_evidence else EvidenceFreshness.STALE

            mapping = ControlMapping(
                control_id=ctrl["id"],
                control_name=ctrl["name"],
                framework=fw,
                status=status,
                evidence_count=2 if has_evidence else 0,
                last_evidence_at=now if has_evidence else None,
                freshness=freshness,
                code_refs=[f"src/{ctrl['category'].lower().replace(' ', '_')}/"] if has_evidence else [],
            )
            mappings.append(mapping)

            if has_evidence:
                item = EvidenceItem(
                    control_id=ctrl["id"],
                    framework=fw,
                    title=f"Evidence for {ctrl['name']}",
                    description=f"Automated evidence collected for {ctrl['id']}: {ctrl['name']}",
                    content={"control": ctrl["id"], "category": ctrl["category"], "status": "verified", "collected_by": "automated_scan"},
                    collected_at=now,
                    expires_at=now + timedelta(days=90),
                    freshness=EvidenceFreshness.FRESH,
                )
                items.append(item)

        met = sum(1 for m in mappings if m.status == ControlStatus.MET)
        coverage = round(met / len(controls) * 100, 1) if controls else 0

        package = EvidencePackage(
            framework=fw,
            controls_total=len(controls),
            controls_met=met,
            coverage_pct=coverage,
            items=items,
            control_mappings=mappings,
            generated_at=now,
            valid_until=now + timedelta(days=90),
        )
        self._items.extend(items)
        self._packages[framework] = package
        logger.info("Evidence package generated", framework=framework, coverage=coverage)
        return package

    def get_package(self, framework: str) -> EvidencePackage | None:
        return self._packages.get(framework)

    def list_frameworks(self) -> list[dict]:
        return [
            {"framework": "soc2", "name": "SOC 2 Type II", "controls": len(_SOC2_CONTROLS)},
            {"framework": "iso27001", "name": "ISO 27001:2022", "controls": len(_ISO27001_CONTROLS)},
            {"framework": "hipaa", "name": "HIPAA Security Rule", "controls": 8},
            {"framework": "pci_dss", "name": "PCI-DSS v4.0", "controls": 8},
        ]

    def get_control_status(self, framework: str, control_id: str) -> ControlMapping | None:
        pkg = self._packages.get(framework)
        if not pkg:
            return None
        return next((m for m in pkg.control_mappings if m.control_id == control_id), None)

    def get_stats(self) -> EvidenceStats:
        by_fw: dict[str, int] = {}
        by_fresh: dict[str, int] = {}
        stale = 0
        for item in self._items:
            by_fw[item.framework.value] = by_fw.get(item.framework.value, 0) + 1
            by_fresh[item.freshness.value] = by_fresh.get(item.freshness.value, 0) + 1
            if item.freshness == EvidenceFreshness.STALE:
                stale += 1
        all_coverage = [p.coverage_pct for p in self._packages.values()]
        return EvidenceStats(
            total_items=len(self._items),
            by_framework=by_fw,
            by_freshness=by_fresh,
            overall_coverage_pct=round(sum(all_coverage) / len(all_coverage), 1) if all_coverage else 0.0,
            stale_items=stale,
        )
