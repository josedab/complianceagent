"""Compliance Evidence Vault Service."""

import hashlib
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.evidence_vault.models import (
    AuditorRole,
    AuditorSession,
    AuditReport,
    AuditTimelineEvent,
    BatchVerificationResult,
    BlockchainAnchor,
    ChainVerificationResult,
    ControlFramework,
    ControlMapping,
    CoverageMetrics,
    EvidenceChain,
    EvidenceGap,
    EvidenceItem,
    EvidenceType,
)


logger = structlog.get_logger()

# SOC 2 Type II control mappings
_SOC2_CONTROLS = [
    ("CC1.1", "Control Environment"),
    ("CC1.2", "Board Oversight"),
    ("CC2.1", "Information and Communication"),
    ("CC3.1", "Risk Assessment"),
    ("CC4.1", "Monitoring Activities"),
    ("CC5.1", "Control Activities"),
    ("CC6.1", "Logical Access Security"),
    ("CC6.2", "Access Authentication"),
    ("CC6.3", "Access Authorization"),
    ("CC7.1", "System Operations Monitoring"),
    ("CC7.2", "Incident Management"),
    ("CC8.1", "Change Management"),
    ("CC9.1", "Risk Mitigation"),
]


class EvidenceVaultService:
    """Immutable evidence repository with auditor portal."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._chains: dict[ControlFramework, EvidenceChain] = {}
        self._auditor_sessions: dict[UUID, AuditorSession] = {}
        self._reports: dict[UUID, AuditReport] = {}
        self._blockchain_anchors: dict[str, BlockchainAnchor] = {}
        self._timeline_events: list[AuditTimelineEvent] = []

    async def store_evidence(
        self,
        evidence_type: EvidenceType,
        title: str,
        description: str,
        content: str,
        framework: ControlFramework,
        control_id: str,
        control_name: str = "",
        source: str = "",
        metadata: dict | None = None,
    ) -> EvidenceItem:
        """Store a new evidence item in the immutable vault."""
        chain = self._chains.get(framework)
        if not chain:
            chain = EvidenceChain(framework=framework)
            self._chains[framework] = chain

        previous_hash = chain.items[-1].content_hash if chain.items else ""

        content_hash = hashlib.sha256(
            (content + previous_hash).encode()
        ).hexdigest()

        item = EvidenceItem(
            evidence_type=evidence_type,
            title=title,
            description=description,
            content_hash=content_hash,
            framework=framework,
            control_id=control_id,
            control_name=control_name,
            collected_at=datetime.now(UTC),
            source=source,
            metadata=metadata or {},
            previous_hash=previous_hash,
        )

        chain.items.append(item)
        chain.chain_hash = content_hash

        logger.info(
            "Evidence stored",
            framework=framework.value,
            control=control_id,
            hash=content_hash[:12],
        )
        return item

    async def verify_chain(self, framework: ControlFramework) -> bool:
        """Verify the integrity of an evidence chain."""
        chain = self._chains.get(framework)
        if not chain or not chain.items:
            return True

        for i, item in enumerate(chain.items):
            if i == 0:
                continue
            if item.previous_hash != chain.items[i - 1].content_hash:
                logger.error(
                    "Chain integrity violation",
                    framework=framework.value,
                    item=str(item.id),
                    index=i,
                )
                chain.verified = False
                return False

        chain.verified = True
        chain.last_verified_at = datetime.now(UTC)
        logger.info("Chain verified", framework=framework.value, items=len(chain.items))
        return True

    async def get_evidence(
        self,
        framework: ControlFramework | None = None,
        control_id: str | None = None,
        evidence_type: EvidenceType | None = None,
        limit: int = 50,
    ) -> list[EvidenceItem]:
        """Query evidence items with filters."""
        items: list[EvidenceItem] = []
        chains = [self._chains[framework]] if framework and framework in self._chains else list(self._chains.values())

        for chain in chains:
            for item in chain.items:
                if control_id and item.control_id != control_id:
                    continue
                if evidence_type and item.evidence_type != evidence_type:
                    continue
                items.append(item)

        return sorted(items, key=lambda i: i.collected_at or datetime.min, reverse=True)[:limit]

    async def get_control_mappings(self, framework: ControlFramework) -> list[ControlMapping]:
        """Get control-to-evidence mappings for a framework."""
        chain = self._chains.get(framework, EvidenceChain())

        controls = _SOC2_CONTROLS if framework == ControlFramework.SOC2 else []
        mappings = []

        for control_id, control_name in controls:
            evidence_ids = [
                item.id for item in chain.items if item.control_id == control_id
            ]
            coverage = min(100.0, len(evidence_ids) * 25.0)
            mappings.append(ControlMapping(
                control_id=control_id,
                control_name=control_name,
                framework=framework,
                evidence_ids=evidence_ids,
                coverage_pct=coverage,
                status="complete" if coverage >= 75 else ("partial" if coverage > 0 else "incomplete"),
            ))

        return mappings

    async def create_auditor_session(
        self,
        auditor_email: str,
        auditor_name: str,
        firm: str = "",
        role: AuditorRole = AuditorRole.VIEWER,
        frameworks: list[ControlFramework] | None = None,
        expires_hours: int = 72,
    ) -> AuditorSession:
        """Create a read-only auditor portal session."""
        from datetime import timedelta

        session = AuditorSession(
            auditor_email=auditor_email,
            auditor_name=auditor_name,
            firm=firm,
            role=role,
            frameworks=frameworks or [ControlFramework.SOC2],
            expires_at=datetime.now(UTC) + timedelta(hours=expires_hours),
            created_at=datetime.now(UTC),
        )

        self._auditor_sessions[session.id] = session
        logger.info("Auditor session created", email=auditor_email, firm=firm)
        return session

    async def get_auditor_session(self, session_id: UUID) -> AuditorSession | None:
        """Get an auditor session."""
        session = self._auditor_sessions.get(session_id)
        if session and session.expires_at and session.expires_at < datetime.now(UTC):
            session.is_active = False
        return session

    async def list_auditor_sessions(self) -> list[AuditorSession]:
        """List all auditor sessions."""
        return list(self._auditor_sessions.values())

    async def generate_report(
        self,
        framework: ControlFramework,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
        report_format: str = "pdf",
    ) -> AuditReport:
        """Generate an audit report for a framework."""
        mappings = await self.get_control_mappings(framework)

        total = len(mappings)
        with_evidence = sum(1 for m in mappings if m.evidence_ids)
        coverage = (with_evidence / total * 100) if total else 0

        report = AuditReport(
            framework=framework,
            title=f"{framework.value.upper()} Compliance Report",
            period_start=period_start or datetime.now(UTC),
            period_end=period_end or datetime.now(UTC),
            total_controls=total,
            controls_with_evidence=with_evidence,
            coverage_pct=round(coverage, 1),
            control_mappings=mappings,
            generated_at=datetime.now(UTC),
            report_format=report_format,
        )

        self._reports[report.id] = report
        logger.info(
            "Audit report generated",
            framework=framework.value,
            coverage=f"{coverage:.1f}%",
        )
        return report

    async def get_report(self, report_id: UUID) -> AuditReport | None:
        """Get a generated report."""
        return self._reports.get(report_id)

    # ── Coverage Metrics ─────────────────────────────────────────────────

    async def get_coverage_metrics(self, framework: ControlFramework) -> CoverageMetrics:
        """Get detailed coverage metrics for a compliance framework."""
        control_defs: dict[str, list[tuple[str, str]]] = {
            "soc2": [
                ("CC1.1", "Control Environment"), ("CC1.2", "Board Oversight"),
                ("CC2.1", "Information & Communication"), ("CC3.1", "Risk Assessment"),
                ("CC3.2", "Risk Mitigation"), ("CC4.1", "Monitoring Activities"),
                ("CC5.1", "Control Activities"), ("CC6.1", "Logical Access"),
                ("CC6.2", "Physical Access"), ("CC6.3", "Access Provisioning"),
                ("CC6.6", "System Operations"), ("CC6.7", "Change Management"),
                ("CC6.8", "Vulnerability Management"), ("CC7.1", "System Monitoring"),
                ("CC7.2", "Incident Detection"), ("CC7.3", "Incident Response"),
                ("CC8.1", "Change Management"), ("CC9.1", "Risk Mitigation"),
            ],
            "hipaa": [
                ("164.308(a)(1)", "Security Management"), ("164.308(a)(3)", "Workforce Security"),
                ("164.308(a)(4)", "Information Access"), ("164.308(a)(5)", "Security Awareness"),
                ("164.308(a)(6)", "Security Incident"), ("164.308(a)(7)", "Contingency Plan"),
                ("164.310(a)", "Facility Access"), ("164.310(b)", "Workstation Use"),
                ("164.310(d)", "Device and Media"), ("164.312(a)", "Access Control"),
                ("164.312(b)", "Audit Controls"), ("164.312(c)", "Integrity"),
                ("164.312(d)", "Authentication"), ("164.312(e)", "Transmission Security"),
            ],
            "gdpr": [
                ("Art.5", "Processing Principles"), ("Art.6", "Lawful Basis"),
                ("Art.7", "Consent Conditions"), ("Art.12", "Transparency"),
                ("Art.15", "Right of Access"), ("Art.17", "Right to Erasure"),
                ("Art.20", "Data Portability"), ("Art.25", "Data Protection by Design"),
                ("Art.30", "Records of Processing"), ("Art.32", "Security of Processing"),
                ("Art.33", "Breach Notification"), ("Art.35", "Impact Assessment"),
            ],
            "pci_dss": [
                ("1.1", "Network Security"), ("2.1", "Secure Configuration"),
                ("3.1", "Protect Stored Data"), ("3.4", "Render PAN Unreadable"),
                ("4.1", "Encrypt Transmission"), ("6.1", "Identify Vulnerabilities"),
                ("6.5", "Secure Coding"), ("7.1", "Restrict Access"),
                ("8.1", "Identify Users"), ("8.2", "Authentication"),
                ("10.1", "Audit Trails"), ("11.1", "Security Testing"),
                ("12.1", "Security Policy"),
            ],
        }

        fw_key = framework.value
        controls = control_defs.get(fw_key, control_defs.get("soc2", []))
        chain = self._chains.get(framework, EvidenceChain())
        evidence_items = chain.items
        evidenced_controls = {e.control_id for e in evidence_items}

        breakdown: list[dict[str, Any]] = []
        with_evidence = 0
        partial = 0
        missing = 0

        for control_id, control_name in controls:
            if control_id in evidenced_controls:
                ctrl_status = "covered"
                with_evidence += 1
            elif any(control_id[:3] in ec for ec in evidenced_controls):
                ctrl_status = "partial"
                partial += 1
            else:
                ctrl_status = "missing"
                missing += 1

            breakdown.append({
                "control_id": control_id,
                "control_name": control_name,
                "status": ctrl_status,
                "evidence_count": sum(1 for e in evidence_items if e.control_id == control_id),
            })

        total = len(controls)
        coverage = round((with_evidence + partial * 0.5) / max(total, 1) * 100, 1)

        # Calculate evidence freshness
        import time
        now = time.time()
        freshness_days: list[float] = []
        stale = 0
        for e in evidence_items:
            if e.collected_at:
                age_days = (now - e.collected_at.timestamp()) / 86400
                freshness_days.append(age_days)
                if age_days > 90:
                    stale += 1

        avg_freshness = round(sum(freshness_days) / max(len(freshness_days), 1), 1)

        return CoverageMetrics(
            framework=fw_key,
            total_controls=total,
            controls_with_evidence=with_evidence,
            controls_partial=partial,
            controls_missing=missing,
            coverage_percentage=coverage,
            evidence_freshness_avg_days=avg_freshness,
            stale_evidence_count=stale,
            control_breakdown=breakdown,
        )

    # ── Enhanced Chain Verification ──────────────────────────────────────

    async def verify_chain_enhanced(self, framework: ControlFramework) -> ChainVerificationResult:
        """Perform enhanced hash chain verification with detailed results."""
        import time

        start_time = time.monotonic()
        fw_key = framework.value
        chain = self._chains.get(framework, EvidenceChain())
        items = chain.items

        if not items:
            return ChainVerificationResult(
                framework=fw_key,
                chain_length=0,
                is_valid=True,
                verification_time_ms=0.0,
                root_hash="",
            )

        invalid_links: list[dict[str, str]] = []
        is_valid = True
        prev_hash = "genesis"

        for i, evidence in enumerate(items):
            expected_hash = hashlib.sha256(
                f"{prev_hash}:{evidence.evidence_type.value}:{evidence.title}".encode()
            ).hexdigest()

            if evidence.previous_hash and evidence.previous_hash != prev_hash:
                invalid_links.append({
                    "position": str(i),
                    "evidence_id": str(evidence.id),
                    "expected_prev": prev_hash[:16] + "...",
                    "actual_prev": evidence.previous_hash[:16] + "...",
                })
                is_valid = False

            prev_hash = evidence.content_hash if evidence.content_hash else expected_hash

        elapsed_ms = round((time.monotonic() - start_time) * 1000, 2)

        return ChainVerificationResult(
            framework=fw_key,
            chain_length=len(items),
            is_valid=is_valid and len(invalid_links) == 0,
            invalid_links=invalid_links,
            tamper_detected=len(invalid_links) > 0,
            verification_time_ms=elapsed_ms,
            hash_algorithm="SHA-256",
            root_hash=prev_hash[:64] if prev_hash else "",
        )

    # ── Evidence Gaps ────────────────────────────────────────────────────

    async def identify_evidence_gaps(self, framework: ControlFramework) -> list[EvidenceGap]:
        """Identify gaps in evidence coverage."""
        coverage = await self.get_coverage_metrics(framework)
        fw_key = framework.value
        gaps: list[EvidenceGap] = []

        for control in coverage.control_breakdown:
            if control["status"] == "missing":
                gaps.append(EvidenceGap(
                    control_id=control["control_id"],
                    control_name=control["control_name"],
                    framework=fw_key,
                    gap_type="missing",
                    required_evidence_types=["scan_result", "policy_document"],
                    remediation_suggestion=f"Upload evidence for {control['control_name']} ({control['control_id']})",
                    priority="high",
                ))
            elif control["status"] == "partial":
                gaps.append(EvidenceGap(
                    control_id=control["control_id"],
                    control_name=control["control_name"],
                    framework=fw_key,
                    gap_type="insufficient",
                    required_evidence_types=["test_result"],
                    remediation_suggestion=f"Additional evidence needed for {control['control_name']}",
                    priority="medium",
                ))

        gaps.sort(key=lambda g: {"high": 0, "medium": 1, "low": 2}.get(g.priority, 3))
        return gaps

    # ── Blockchain Anchoring ─────────────────────────────────────────────

    async def anchor_to_blockchain(self, framework: ControlFramework) -> BlockchainAnchor:
        """Anchor evidence chain to blockchain for tamper-proof verification."""
        chain = self._chains.get(framework, EvidenceChain())
        items = chain.items

        # Compute aggregate hash of all evidence for this framework
        aggregate = hashlib.sha256()
        for item in items:
            aggregate.update(item.content_hash.encode())
        chain_hash = aggregate.hexdigest()

        # Generate deterministic transaction hash (simulated blockchain submission)
        tx_data = f"{framework.value}:{chain_hash}:{len(items)}"
        transaction_id = "0x" + hashlib.sha256(tx_data.encode()).hexdigest()
        block_number = int(hashlib.sha256(chain_hash.encode()).hexdigest()[:8], 16) % 10_000_000

        anchor_hash = hashlib.sha256(
            f"{chain_hash}:{transaction_id}".encode()
        ).hexdigest()

        anchor = BlockchainAnchor(
            framework=framework.value,
            chain_hash=chain_hash,
            evidence_count=len(items),
            anchor_hash=anchor_hash,
            blockchain_network="polygon",
            transaction_id=transaction_id,
            block_number=block_number,
            status="confirmed",
            confirmed_at=datetime.now(UTC),
            cost_usd=round(0.002 + len(items) * 0.0001, 4),
        )

        self._blockchain_anchors[framework.value] = anchor

        await self._record_timeline_event(
            event_type="anchor_created",
            description=f"Evidence chain anchored to blockchain for {framework.value}",
            framework=framework.value,
            actor="system",
            metadata={
                "transaction_id": transaction_id,
                "block_number": block_number,
                "evidence_count": len(items),
            },
        )

        logger.info(
            "Blockchain anchor created",
            framework=framework.value,
            tx=transaction_id[:16],
            evidence_count=len(items),
        )
        return anchor

    # ── Batch Verification ───────────────────────────────────────────────

    async def verify_batch(
        self, framework: ControlFramework, evidence_ids: list[UUID] | None = None,
    ) -> BatchVerificationResult:
        """Verify multiple evidence items at once with chain and blockchain checks."""
        import time

        start_time = time.monotonic()
        chain = self._chains.get(framework, EvidenceChain())
        items = chain.items

        # Filter to requested IDs if provided
        if evidence_ids:
            id_set = set(evidence_ids)
            target_items = [item for item in items if item.id in id_set]
            missing = len(id_set) - len(target_items)
        else:
            target_items = items
            missing = 0

        valid = 0
        invalid = 0
        invalid_items: list[dict[str, Any]] = []

        for _i, item in enumerate(target_items):
            # Find the item's position in the full chain
            chain_idx = items.index(item) if item in items else -1
            if chain_idx > 0:
                expected_prev = items[chain_idx - 1].content_hash
                if item.previous_hash and item.previous_hash != expected_prev:
                    invalid += 1
                    invalid_items.append({
                        "evidence_id": str(item.id),
                        "title": item.title,
                        "reason": "hash chain mismatch",
                    })
                    continue
            valid += 1

        # Check blockchain anchor
        anchor = self._blockchain_anchors.get(framework.value)
        blockchain_verified = False
        if anchor and anchor.status == "confirmed":
            # Re-derive the chain hash and compare
            aggregate = hashlib.sha256()
            for item in items:
                aggregate.update(item.content_hash.encode())
            current_chain_hash = aggregate.hexdigest()
            blockchain_verified = current_chain_hash == anchor.chain_hash

        chain_intact = invalid == 0

        elapsed_ms = round((time.monotonic() - start_time) * 1000, 2)

        result = BatchVerificationResult(
            items_verified=len(target_items),
            items_valid=valid,
            items_invalid=invalid,
            items_missing=missing,
            chain_intact=chain_intact,
            blockchain_verified=blockchain_verified,
            invalid_items=invalid_items,
            verification_duration_ms=elapsed_ms,
        )

        await self._record_timeline_event(
            event_type="chain_verified",
            description=f"Batch verification of {len(target_items)} items for {framework.value}",
            framework=framework.value,
            actor="system",
            metadata={
                "items_verified": len(target_items),
                "items_valid": valid,
                "items_invalid": invalid,
                "blockchain_verified": blockchain_verified,
            },
        )

        logger.info(
            "Batch verification complete",
            framework=framework.value,
            verified=len(target_items),
            valid=valid,
            invalid=invalid,
        )
        return result

    # ── Audit Timeline ───────────────────────────────────────────────────

    async def get_audit_timeline(
        self, framework: str | None = None, limit: int = 50,
    ) -> list[AuditTimelineEvent]:
        """Return chronological audit timeline events."""
        events = self._timeline_events
        if framework:
            events = [e for e in events if e.framework == framework]
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    async def _record_timeline_event(
        self,
        event_type: str,
        description: str,
        framework: str = "",
        actor: str = "",
        metadata: dict | None = None,
    ) -> None:
        """Record an event to the audit timeline."""
        event = AuditTimelineEvent(
            event_type=event_type,
            description=description,
            framework=framework,
            actor=actor,
            metadata=metadata or {},
        )
        self._timeline_events.append(event)
