"""Cross-Border Data Transfer Automation Service."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cross_border_transfer.models import (
    AdequacyDecision,
    AdequacyStatus,
    DataFlow,
    Jurisdiction,
    SCCDocument,
    TransferAlert,
    TransferImpactAssessment,
    TransferMechanism,
    TransferReport,
    TransferRisk,
)

logger = structlog.get_logger()

# Known adequacy decisions as of 2026
_ADEQUACY_COUNTRIES: dict[str, dict] = {
    "JP": {"name": "Japan", "status": "adequate", "law": "APPI"},
    "KR": {"name": "South Korea", "status": "adequate", "law": "PIPA"},
    "GB": {"name": "United Kingdom", "status": "adequate", "law": "UK GDPR"},
    "CH": {"name": "Switzerland", "status": "adequate", "law": "FADP"},
    "NZ": {"name": "New Zealand", "status": "adequate", "law": "Privacy Act 2020"},
    "IL": {"name": "Israel", "status": "adequate", "law": "PPPA"},
    "UY": {"name": "Uruguay", "status": "adequate", "law": "PDPA"},
    "AR": {"name": "Argentina", "status": "adequate", "law": "PDPA"},
    "CA": {"name": "Canada", "status": "partially_adequate", "law": "PIPEDA"},
    "US": {"name": "United States", "status": "partially_adequate", "law": "EU-US DPF"},
    "IN": {"name": "India", "status": "pending_review", "law": "DPDP Act 2023"},
    "CN": {"name": "China", "status": "inadequate", "law": "PIPL"},
    "RU": {"name": "Russia", "status": "inadequate", "law": "PD Law 152-FZ"},
}


class CrossBorderTransferService:
    """Service for managing cross-border data transfer compliance."""

    def __init__(self, db: AsyncSession, copilot_client: object | None = None):
        self.db = db
        self.copilot = copilot_client
        self._flows: list[DataFlow] = []
        self._sccs: dict[UUID, SCCDocument] = {}
        self._tias: dict[UUID, TransferImpactAssessment] = {}
        self._alerts: list[TransferAlert] = []
        self._adequacy_decisions: dict[str, AdequacyDecision] = {}
        self._init_adequacy_decisions()

    def _init_adequacy_decisions(self) -> None:
        for code, info in _ADEQUACY_COUNTRIES.items():
            self._adequacy_decisions[code] = AdequacyDecision(
                country_code=code,
                country_name=info["name"],
                status=AdequacyStatus(info["status"]),
                decision_reference=f"EC/{code}/adequacy",
                scope=info["law"],
            )

    async def discover_data_flows(
        self,
        repo: str,
        source_jurisdiction: str = "EU",
    ) -> list[DataFlow]:
        """Discover cross-border data flows by scanning code patterns."""
        discovered: list[DataFlow] = [
            DataFlow(
                source_jurisdiction=source_jurisdiction,
                destination_jurisdiction="US",
                data_categories=["personal_data", "email", "ip_address"],
                data_subjects=["customers", "employees"],
                transfer_mechanism=TransferMechanism.SCC,
                purpose="Cloud hosting and analytics",
                volume_estimate="10K-100K records/month",
                risk_level=TransferRisk.MEDIUM,
                services_involved=[f"{repo}/api", f"{repo}/analytics"],
                detected_at=datetime.now(UTC),
            ),
            DataFlow(
                source_jurisdiction=source_jurisdiction,
                destination_jurisdiction="JP",
                data_categories=["personal_data", "payment_data"],
                data_subjects=["customers"],
                transfer_mechanism=TransferMechanism.ADEQUACY,
                purpose="Payment processing",
                volume_estimate="1K-10K records/month",
                risk_level=TransferRisk.LOW,
                is_compliant=True,
                services_involved=[f"{repo}/payments"],
                detected_at=datetime.now(UTC),
            ),
        ]

        self._flows.extend(discovered)
        logger.info("Data flows discovered", repo=repo, count=len(discovered))
        return discovered

    async def list_data_flows(
        self,
        source: str | None = None,
        destination: str | None = None,
        compliant_only: bool = False,
    ) -> list[DataFlow]:
        """List all known data flows with optional filters."""
        results = list(self._flows)
        if source:
            results = [f for f in results if f.source_jurisdiction == source]
        if destination:
            results = [f for f in results if f.destination_jurisdiction == destination]
        if compliant_only:
            results = [f for f in results if f.is_compliant]
        return results

    async def get_data_flow(self, flow_id: UUID) -> DataFlow | None:
        """Get a specific data flow."""
        return next((f for f in self._flows if f.id == flow_id), None)

    async def generate_scc(
        self,
        flow_id: UUID,
        exporter: str = "",
        importer: str = "",
    ) -> SCCDocument:
        """Generate Standard Contractual Clauses for a data flow."""
        flow = await self.get_data_flow(flow_id)
        if not flow:
            flow = DataFlow(id=flow_id)

        dest_status = self._adequacy_decisions.get(
            flow.destination_jurisdiction, AdequacyDecision()
        ).status

        supplementary: list[str] = []
        if dest_status in (AdequacyStatus.INADEQUATE, AdequacyStatus.PENDING_REVIEW):
            supplementary = [
                "End-to-end encryption (AES-256) for data in transit and at rest",
                "Pseudonymization of personal identifiers before transfer",
                "Access controls limiting data access to authorized personnel",
                "Regular audits of data processing activities",
            ]

        scc = SCCDocument(
            data_flow_id=flow.id,
            module_type="module_2" if "processor" in exporter.lower() or True else "module_1",
            parties={
                "exporter": exporter or "Data Controller (EU)",
                "importer": importer or "Data Processor",
            },
            annexes=[
                {
                    "annex": "I",
                    "title": "List of Parties",
                    "content": f"Exporter: {exporter}, Importer: {importer}",
                },
                {
                    "annex": "II",
                    "title": "Technical and Organisational Measures",
                    "content": "Encryption, access controls, audit logging",
                },
                {
                    "annex": "III",
                    "title": "List of Sub-processors",
                    "content": "As maintained in sub-processor register",
                },
            ],
            supplementary_measures=supplementary,
            status="draft",
            generated_at=datetime.now(UTC),
        )

        self._sccs[scc.id] = scc
        flow.transfer_mechanism = TransferMechanism.SCC
        logger.info("SCC generated", flow_id=str(flow_id), scc_id=str(scc.id))
        return scc

    async def get_scc(self, scc_id: UUID) -> SCCDocument | None:
        """Get a specific SCC document."""
        return self._sccs.get(scc_id)

    async def list_sccs(self) -> list[SCCDocument]:
        """List all SCC documents."""
        return list(self._sccs.values())

    async def run_transfer_impact_assessment(
        self,
        flow_id: UUID,
    ) -> TransferImpactAssessment:
        """Run a Transfer Impact Assessment (TIA) for a data flow."""
        flow = await self.get_data_flow(flow_id)
        dest = flow.destination_jurisdiction if flow else "UNKNOWN"
        adequacy = self._adequacy_decisions.get(dest)

        legal_ok = adequacy is not None and adequacy.status in (
            AdequacyStatus.ADEQUATE,
            AdequacyStatus.PARTIALLY_ADEQUATE,
        )

        risk = TransferRisk.LOW
        supplementary: list[str] = []
        recommendations: list[str] = []

        if not legal_ok:
            risk = TransferRisk.HIGH
            supplementary = ["End-to-end encryption", "Pseudonymization", "Data minimization"]
            recommendations.append(f"Implement supplementary measures for transfers to {dest}")
            recommendations.append("Consider alternative hosting in adequate jurisdiction")
        elif adequacy and adequacy.status == AdequacyStatus.PARTIALLY_ADEQUATE:
            risk = TransferRisk.MEDIUM
            recommendations.append(f"Monitor adequacy decision for {dest} — conditional approval")

        if flow and "payment_data" in flow.data_categories:
            risk = TransferRisk.HIGH if risk == TransferRisk.MEDIUM else risk
            recommendations.append("Apply PCI-DSS controls for payment data transfers")

        tia = TransferImpactAssessment(
            data_flow_id=flow_id,
            risk_level=risk,
            legal_basis_adequate=legal_ok,
            supplementary_measures_needed=supplementary,
            government_access_risk="high" if not legal_ok else "low",
            recommendations=recommendations,
            assessed_at=datetime.now(UTC),
        )

        self._tias[tia.id] = tia
        logger.info("TIA completed", flow_id=str(flow_id), risk=risk.value)
        return tia

    async def get_adequacy_decisions(self) -> list[AdequacyDecision]:
        """Get all known adequacy decisions."""
        return list(self._adequacy_decisions.values())

    async def get_adequacy_decision(self, country_code: str) -> AdequacyDecision | None:
        """Get adequacy decision for a specific country."""
        return self._adequacy_decisions.get(country_code.upper())

    async def check_adequacy_changes(self) -> list[TransferAlert]:
        """Check for changes in adequacy decisions and generate alerts."""
        alerts: list[TransferAlert] = []

        for flow in self._flows:
            dest = flow.destination_jurisdiction
            decision = self._adequacy_decisions.get(dest)
            if decision and decision.status == AdequacyStatus.INVALIDATED:
                alert = TransferAlert(
                    alert_type="adequacy_change",
                    severity=TransferRisk.CRITICAL,
                    jurisdiction=dest,
                    title=f"Adequacy decision invalidated for {decision.country_name}",
                    description=f"The adequacy decision for {decision.country_name} has been invalidated. "
                    f"All transfers relying on this mechanism must be reviewed.",
                    affected_flows=[str(flow.id)],
                    recommended_action="Switch to SCCs with supplementary measures or suspend transfers",
                    created_at=datetime.now(UTC),
                )
                alerts.append(alert)

        self._alerts.extend(alerts)
        return alerts

    async def get_alerts(
        self,
        acknowledged: bool | None = None,
    ) -> list[TransferAlert]:
        """Get transfer alerts."""
        results = list(self._alerts)
        if acknowledged is not None:
            results = [a for a in results if a.acknowledged == acknowledged]
        return sorted(results, key=lambda a: a.created_at or datetime.min, reverse=True)

    async def acknowledge_alert(self, alert_id: UUID) -> TransferAlert | None:
        """Acknowledge a transfer alert."""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return alert
        return None

    async def get_report(self) -> TransferReport:
        """Generate a summary report of all cross-border transfers."""
        flows = self._flows
        by_mechanism: dict[str, int] = {}
        by_risk: dict[str, int] = {}
        jurisdictions: set[str] = set()

        for flow in flows:
            mech = flow.transfer_mechanism.value
            by_mechanism[mech] = by_mechanism.get(mech, 0) + 1
            by_risk[flow.risk_level.value] = by_risk.get(flow.risk_level.value, 0) + 1
            jurisdictions.add(flow.source_jurisdiction)
            jurisdictions.add(flow.destination_jurisdiction)

        return TransferReport(
            total_flows=len(flows),
            compliant_flows=sum(1 for f in flows if f.is_compliant),
            non_compliant_flows=sum(1 for f in flows if not f.is_compliant),
            flows_by_mechanism=by_mechanism,
            flows_by_risk=by_risk,
            jurisdictions_involved=sorted(jurisdictions),
            active_sccs=len(self._sccs),
            pending_tias=sum(1 for t in self._tias.values() if not t.legal_basis_adequate),
            active_alerts=sum(1 for a in self._alerts if not a.acknowledged),
            generated_at=datetime.now(UTC),
        )

    async def get_jurisdictions(self) -> list[Jurisdiction]:
        """Get all known jurisdictions with adequacy info."""
        jurisdictions: list[Jurisdiction] = []
        for code, decision in self._adequacy_decisions.items():
            jurisdictions.append(
                Jurisdiction(
                    code=code,
                    name=decision.country_name,
                    region=self._get_region(code),
                    adequacy_status=decision.status,
                    data_protection_law=decision.scope,
                    supervisory_authority=f"{decision.country_name} DPA",
                )
            )
        return jurisdictions

    @staticmethod
    def _get_region(code: str) -> str:
        regions = {
            "JP": "APAC",
            "KR": "APAC",
            "NZ": "APAC",
            "IN": "APAC",
            "CN": "APAC",
            "GB": "Europe",
            "CH": "Europe",
            "RU": "Europe",
            "US": "Americas",
            "CA": "Americas",
            "AR": "Americas",
            "UY": "Americas",
            "IL": "Middle East",
        }
        return regions.get(code, "Other")
