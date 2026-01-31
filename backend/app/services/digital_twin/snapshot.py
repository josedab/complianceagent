"""Snapshot Manager - Creates and manages compliance snapshots."""

import hashlib
import time
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import structlog

from app.services.digital_twin.models import (
    ComplianceIssue,
    ComplianceSnapshot,
    ComplianceStatus,
    RegulationCompliance,
)


logger = structlog.get_logger()


class SnapshotManager:
    """Manages compliance snapshots for digital twin functionality."""

    def __init__(self):
        self._snapshots: dict[UUID, ComplianceSnapshot] = {}
        self._by_org: dict[UUID, list[UUID]] = {}

    async def create_snapshot(
        self,
        organization_id: UUID,
        repository_id: UUID | None = None,
        name: str | None = None,
        commit_sha: str | None = None,
        branch: str | None = None,
        compliance_data: dict[str, Any] | None = None,
    ) -> ComplianceSnapshot:
        """Create a new compliance snapshot.
        
        Args:
            organization_id: Organization ID
            repository_id: Repository ID (optional)
            name: Snapshot name
            commit_sha: Git commit SHA
            branch: Git branch
            compliance_data: Pre-computed compliance data
            
        Returns:
            ComplianceSnapshot
        """
        start_time = time.perf_counter()
        
        snapshot = ComplianceSnapshot(
            organization_id=organization_id,
            repository_id=repository_id,
            name=name or f"Snapshot {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            commit_sha=commit_sha,
            branch=branch,
        )
        
        if compliance_data:
            snapshot = self._populate_from_data(snapshot, compliance_data)
        else:
            # Compute compliance state (in production, would analyze codebase)
            snapshot = await self._analyze_compliance(snapshot)
        
        # Calculate overall score
        snapshot.overall_score = self._calculate_overall_score(snapshot)
        snapshot.overall_status = self._determine_status(snapshot.overall_score)
        
        # Store snapshot
        self._snapshots[snapshot.id] = snapshot
        if organization_id not in self._by_org:
            self._by_org[organization_id] = []
        self._by_org[organization_id].append(snapshot.id)
        
        logger.info(
            "Created compliance snapshot",
            snapshot_id=str(snapshot.id),
            score=snapshot.overall_score,
            issues=len(snapshot.issues),
            duration_ms=(time.perf_counter() - start_time) * 1000,
        )
        
        return snapshot

    async def get_snapshot(self, snapshot_id: UUID) -> ComplianceSnapshot | None:
        """Get a snapshot by ID."""
        return self._snapshots.get(snapshot_id)

    async def get_latest_snapshot(
        self,
        organization_id: UUID,
        repository_id: UUID | None = None,
    ) -> ComplianceSnapshot | None:
        """Get the most recent snapshot for an organization."""
        org_snapshots = self._by_org.get(organization_id, [])
        if not org_snapshots:
            return None
        
        snapshots = [self._snapshots[sid] for sid in org_snapshots if sid in self._snapshots]
        
        if repository_id:
            snapshots = [s for s in snapshots if s.repository_id == repository_id]
        
        if not snapshots:
            return None
        
        return max(snapshots, key=lambda s: s.created_at)

    async def list_snapshots(
        self,
        organization_id: UUID,
        limit: int = 50,
    ) -> list[ComplianceSnapshot]:
        """List snapshots for an organization."""
        org_snapshots = self._by_org.get(organization_id, [])
        snapshots = [self._snapshots[sid] for sid in org_snapshots if sid in self._snapshots]
        snapshots.sort(key=lambda s: s.created_at, reverse=True)
        return snapshots[:limit]

    async def compare_snapshots(
        self,
        snapshot1_id: UUID,
        snapshot2_id: UUID,
    ) -> dict[str, Any]:
        """Compare two snapshots."""
        s1 = await self.get_snapshot(snapshot1_id)
        s2 = await self.get_snapshot(snapshot2_id)
        
        if not s1 or not s2:
            raise ValueError("One or both snapshots not found")
        
        # Compare scores
        score_delta = s2.overall_score - s1.overall_score
        
        # Compare issues
        s1_issue_codes = {i.code for i in s1.issues}
        s2_issue_codes = {i.code for i in s2.issues}
        
        new_issues = [i for i in s2.issues if i.code not in s1_issue_codes]
        resolved_issues = [i for i in s1.issues if i.code not in s2_issue_codes]
        
        # Compare by regulation
        regulation_changes = []
        s1_regs = {r.regulation: r for r in s1.regulations}
        s2_regs = {r.regulation: r for r in s2.regulations}
        
        all_regs = set(s1_regs.keys()) | set(s2_regs.keys())
        for reg in all_regs:
            r1 = s1_regs.get(reg)
            r2 = s2_regs.get(reg)
            
            if r1 and r2:
                regulation_changes.append({
                    "regulation": reg,
                    "score_before": r1.score,
                    "score_after": r2.score,
                    "delta": r2.score - r1.score,
                    "status_before": r1.status.value,
                    "status_after": r2.status.value,
                })
            elif r2:
                regulation_changes.append({
                    "regulation": reg,
                    "score_before": None,
                    "score_after": r2.score,
                    "delta": None,
                    "status_before": None,
                    "status_after": r2.status.value,
                })
        
        return {
            "snapshot1": {
                "id": str(s1.id),
                "created_at": s1.created_at.isoformat(),
                "score": s1.overall_score,
                "issues_count": len(s1.issues),
            },
            "snapshot2": {
                "id": str(s2.id),
                "created_at": s2.created_at.isoformat(),
                "score": s2.overall_score,
                "issues_count": len(s2.issues),
            },
            "score_delta": score_delta,
            "improved": score_delta > 0,
            "new_issues": len(new_issues),
            "resolved_issues": len(resolved_issues),
            "new_issues_details": [
                {"code": i.code, "message": i.message, "severity": i.severity}
                for i in new_issues[:10]
            ],
            "resolved_issues_details": [
                {"code": i.code, "message": i.message, "severity": i.severity}
                for i in resolved_issues[:10]
            ],
            "regulation_changes": regulation_changes,
        }

    def _populate_from_data(
        self,
        snapshot: ComplianceSnapshot,
        data: dict[str, Any],
    ) -> ComplianceSnapshot:
        """Populate snapshot from provided data."""
        snapshot.overall_score = data.get("score", 0.0)
        snapshot.files_analyzed = data.get("files_analyzed", 0)
        snapshot.total_lines = data.get("total_lines", 0)
        snapshot.languages = data.get("languages", [])
        
        # Regulations
        for reg_data in data.get("regulations", []):
            snapshot.regulations.append(RegulationCompliance(
                regulation=reg_data.get("regulation", ""),
                status=ComplianceStatus(reg_data.get("status", "unknown")),
                score=reg_data.get("score", 0.0),
                issues_count=reg_data.get("issues_count", 0),
                requirements_met=reg_data.get("requirements_met", 0),
                requirements_total=reg_data.get("requirements_total", 0),
            ))
        
        # Issues
        for issue_data in data.get("issues", []):
            snapshot.issues.append(ComplianceIssue(
                code=issue_data.get("code", ""),
                message=issue_data.get("message", ""),
                severity=issue_data.get("severity", "medium"),
                regulation=issue_data.get("regulation"),
                file_path=issue_data.get("file_path"),
                line_number=issue_data.get("line_number"),
                category=issue_data.get("category"),
            ))
        
        return snapshot

    async def _analyze_compliance(
        self,
        snapshot: ComplianceSnapshot,
    ) -> ComplianceSnapshot:
        """Analyze codebase for compliance state.
        
        In production, this would run full compliance analysis.
        """
        # Default regulations to check
        regulations = ["GDPR", "CCPA", "HIPAA", "PCI-DSS", "SOX", "EU AI Act"]
        
        for reg in regulations:
            # Simulated compliance scores
            import random
            score = random.uniform(0.6, 1.0)
            issues_count = random.randint(0, 10)
            
            snapshot.regulations.append(RegulationCompliance(
                regulation=reg,
                status=self._determine_status(score),
                score=score,
                issues_count=issues_count,
                requirements_met=int(score * 20),
                requirements_total=20,
            ))
        
        snapshot.files_analyzed = 100
        snapshot.languages = ["python", "typescript"]
        
        return snapshot

    def _calculate_overall_score(self, snapshot: ComplianceSnapshot) -> float:
        """Calculate overall compliance score."""
        if not snapshot.regulations:
            return 0.0
        
        total_score = sum(r.score for r in snapshot.regulations)
        return total_score / len(snapshot.regulations)

    def _determine_status(self, score: float) -> ComplianceStatus:
        """Determine compliance status from score."""
        if score >= 0.9:
            return ComplianceStatus.COMPLIANT
        elif score >= 0.6:
            return ComplianceStatus.PARTIAL
        elif score > 0:
            return ComplianceStatus.NON_COMPLIANT
        return ComplianceStatus.UNKNOWN

    def delete_snapshot(self, snapshot_id: UUID) -> bool:
        """Delete a snapshot."""
        if snapshot_id in self._snapshots:
            snapshot = self._snapshots.pop(snapshot_id)
            if snapshot.organization_id and snapshot.organization_id in self._by_org:
                self._by_org[snapshot.organization_id] = [
                    sid for sid in self._by_org[snapshot.organization_id]
                    if sid != snapshot_id
                ]
            return True
        return False


# Global instance
_snapshot_manager: SnapshotManager | None = None


def get_snapshot_manager() -> SnapshotManager:
    """Get or create snapshot manager."""
    global _snapshot_manager
    if _snapshot_manager is None:
        _snapshot_manager = SnapshotManager()
    return _snapshot_manager
