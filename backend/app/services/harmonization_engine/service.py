"""Harmonization engine service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    ControlCategory,
    ControlOverlap,
    FrameworkControl,
    HarmonizationResult,
    HarmonizationStats,
    OverlapStrength,
)


logger = structlog.get_logger(__name__)


class HarmonizationEngineService:
    """Service for harmonizing controls across compliance frameworks."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._controls: dict[str, list[FrameworkControl]] = {}
        self._results: list[HarmonizationResult] = []
        self._seed_controls()

    def _seed_controls(self) -> None:
        """Seed control mappings for major frameworks."""
        self._controls["GDPR"] = [
            FrameworkControl("GDPR", "GDPR-AC-1", "Access Management", ControlCategory.access_control, "Manage access to personal data"),
            FrameworkControl("GDPR", "GDPR-AC-2", "Authentication Controls", ControlCategory.access_control, "Strong authentication for data access"),
            FrameworkControl("GDPR", "GDPR-EN-1", "Data Encryption at Rest", ControlCategory.encryption, "Encrypt personal data at rest"),
            FrameworkControl("GDPR", "GDPR-EN-2", "Data Encryption in Transit", ControlCategory.encryption, "Encrypt personal data in transit"),
            FrameworkControl("GDPR", "GDPR-LG-1", "Processing Activity Logs", ControlCategory.logging, "Log all processing activities"),
            FrameworkControl("GDPR", "GDPR-LG-2", "Consent Tracking", ControlCategory.logging, "Track and log consent records"),
            FrameworkControl("GDPR", "GDPR-IR-1", "Breach Notification", ControlCategory.incident_response, "72-hour breach notification"),
            FrameworkControl("GDPR", "GDPR-DP-1", "Data Minimization", ControlCategory.data_protection, "Collect only necessary data"),
        ]

        self._controls["HIPAA"] = [
            FrameworkControl("HIPAA", "HIPAA-AC-1", "Access Controls", ControlCategory.access_control, "Control access to ePHI"),
            FrameworkControl("HIPAA", "HIPAA-AC-2", "Unique User Identification", ControlCategory.access_control, "Assign unique user IDs"),
            FrameworkControl("HIPAA", "HIPAA-EN-1", "Encryption Standard", ControlCategory.encryption, "Encrypt ePHI at rest and in transit"),
            FrameworkControl("HIPAA", "HIPAA-LG-1", "Audit Logging", ControlCategory.logging, "Log access to ePHI"),
            FrameworkControl("HIPAA", "HIPAA-IR-1", "Security Incident Response", ControlCategory.incident_response, "Respond to security incidents"),
            FrameworkControl("HIPAA", "HIPAA-DP-1", "Data Integrity Controls", ControlCategory.data_protection, "Ensure ePHI integrity"),
        ]

        self._controls["PCI-DSS"] = [
            FrameworkControl("PCI-DSS", "PCI-AC-1", "Restrict Access", ControlCategory.access_control, "Restrict access to cardholder data"),
            FrameworkControl("PCI-DSS", "PCI-AC-2", "Identify and Authenticate", ControlCategory.access_control, "Identify and authenticate system access"),
            FrameworkControl("PCI-DSS", "PCI-EN-1", "Encrypt Transmission", ControlCategory.encryption, "Encrypt cardholder data transmission"),
            FrameworkControl("PCI-DSS", "PCI-LG-1", "Track and Monitor Access", ControlCategory.logging, "Track and monitor all network access"),
            FrameworkControl("PCI-DSS", "PCI-IR-1", "Incident Response Plan", ControlCategory.incident_response, "Maintain an incident response plan"),
            FrameworkControl("PCI-DSS", "PCI-DP-1", "Protect Stored Data", ControlCategory.data_protection, "Protect stored cardholder data"),
        ]

        self._controls["SOC2"] = [
            FrameworkControl("SOC2", "SOC2-AC-1", "Logical Access", ControlCategory.access_control, "Logical and physical access controls"),
            FrameworkControl("SOC2", "SOC2-AC-2", "User Access Reviews", ControlCategory.access_control, "Periodic user access reviews"),
            FrameworkControl("SOC2", "SOC2-EN-1", "Encryption Controls", ControlCategory.encryption, "Data encryption controls"),
            FrameworkControl("SOC2", "SOC2-LG-1", "System Monitoring", ControlCategory.logging, "Monitor system operations"),
            FrameworkControl("SOC2", "SOC2-IR-1", "Incident Management", ControlCategory.incident_response, "Incident management procedures"),
            FrameworkControl("SOC2", "SOC2-GV-1", "Risk Assessment", ControlCategory.governance, "Perform risk assessments"),
        ]

        self._controls["ISO27001"] = [
            FrameworkControl("ISO27001", "ISO-AC-1", "Access Control Policy", ControlCategory.access_control, "Establish access control policy"),
            FrameworkControl("ISO27001", "ISO-AC-2", "User Access Management", ControlCategory.access_control, "Formal user access management"),
            FrameworkControl("ISO27001", "ISO-EN-1", "Cryptographic Controls", ControlCategory.encryption, "Policy on use of cryptographic controls"),
            FrameworkControl("ISO27001", "ISO-LG-1", "Event Logging", ControlCategory.logging, "Log user activities and events"),
            FrameworkControl("ISO27001", "ISO-IR-1", "Information Security Incidents", ControlCategory.incident_response, "Manage information security incidents"),
            FrameworkControl("ISO27001", "ISO-GV-1", "Information Security Policy", ControlCategory.governance, "Information security policy document"),
        ]

    def _find_overlaps(
        self,
        framework_a: str,
        framework_b: str,
    ) -> list[ControlOverlap]:
        """Find overlapping controls between two frameworks."""
        overlaps: list[ControlOverlap] = []
        controls_a = self._controls.get(framework_a, [])
        controls_b = self._controls.get(framework_b, [])

        overlap_categories = [
            ControlCategory.access_control,
            ControlCategory.encryption,
            ControlCategory.logging,
            ControlCategory.incident_response,
        ]

        strength_map = {
            ControlCategory.access_control: OverlapStrength.strong,
            ControlCategory.encryption: OverlapStrength.exact,
            ControlCategory.logging: OverlapStrength.moderate,
            ControlCategory.incident_response: OverlapStrength.strong,
        }

        savings_map = {
            OverlapStrength.exact: 90.0,
            OverlapStrength.strong: 70.0,
            OverlapStrength.moderate: 45.0,
            OverlapStrength.weak: 20.0,
        }

        for ctrl_a in controls_a:
            if ctrl_a.category not in overlap_categories:
                continue
            for ctrl_b in controls_b:
                if ctrl_a.category == ctrl_b.category:
                    strength = strength_map.get(
                        ctrl_a.category, OverlapStrength.weak
                    )
                    overlaps.append(
                        ControlOverlap(
                            id=uuid.uuid4(),
                            control_a=ctrl_a,
                            control_b=ctrl_b,
                            overlap_strength=strength,
                            description=(
                                f"{ctrl_a.control_name} overlaps with "
                                f"{ctrl_b.control_name}"
                            ),
                            effort_savings_pct=savings_map[strength],
                        )
                    )
        return overlaps

    async def analyze_overlap(
        self,
        frameworks: list[str],
    ) -> HarmonizationResult:
        """Analyze control overlaps across specified frameworks."""
        all_overlaps: list[ControlOverlap] = []
        total_controls = 0

        for fw in frameworks:
            total_controls += len(self._controls.get(fw, []))

        for i, fw_a in enumerate(frameworks):
            for fw_b in frameworks[i + 1 :]:
                all_overlaps.extend(self._find_overlaps(fw_a, fw_b))

        overlapping_count = len(all_overlaps)
        unique_controls = max(total_controls - overlapping_count, 0)
        dedup_pct = (
            (overlapping_count / total_controls * 100.0)
            if total_controls
            else 0.0
        )

        recommendations: list[str] = []
        if dedup_pct > 50.0:
            recommendations.append(
                "High overlap detected — implement unified control framework"
            )
        if dedup_pct > 30.0:
            recommendations.append(
                "Consider consolidated audit approach across frameworks"
            )
        recommendations.append(
            f"Map {overlapping_count} overlapping controls to reduce effort"
        )

        result = HarmonizationResult(
            id=uuid.uuid4(),
            frameworks=frameworks,
            total_controls=total_controls,
            unique_controls=unique_controls,
            overlapping_controls=overlapping_count,
            deduplication_pct=dedup_pct,
            overlaps=all_overlaps,
            recommendations=recommendations,
            generated_at=datetime.now(UTC),
        )
        self._results.append(result)

        await logger.ainfo(
            "overlap_analyzed",
            frameworks=frameworks,
            deduplication_pct=dedup_pct,
        )
        return result

    async def list_controls(
        self,
        framework: str,
    ) -> list[FrameworkControl]:
        """List all controls for a given framework."""
        return list(self._controls.get(framework, []))

    async def get_stats(self) -> HarmonizationStats:
        """Get aggregate harmonization statistics."""
        all_frameworks: set[str] = set()
        total_overlaps = 0
        dedup_pcts: list[float] = []
        pair_counts: dict[str, int] = {}

        for result in self._results:
            all_frameworks.update(result.frameworks)
            total_overlaps += result.overlapping_controls
            dedup_pcts.append(result.deduplication_pct)

            for overlap in result.overlaps:
                pair_key = (
                    f"{overlap.control_a.framework}-"
                    f"{overlap.control_b.framework}"
                )
                pair_counts[pair_key] = pair_counts.get(pair_key, 0) + 1

        avg_dedup = sum(dedup_pcts) / len(dedup_pcts) if dedup_pcts else 0.0

        top_pairs = sorted(
            pair_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        return HarmonizationStats(
            analyses_run=len(self._results),
            frameworks_analyzed=len(all_frameworks),
            total_overlaps_found=total_overlaps,
            avg_deduplication_pct=avg_dedup,
            top_overlap_pairs=[
                {"pair": k, "count": v} for k, v in top_pairs
            ],
        )
