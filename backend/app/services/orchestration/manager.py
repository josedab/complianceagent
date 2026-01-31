"""Orchestration Manager - Multi-repository compliance management."""

import time
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import structlog

from app.services.orchestration.models import (
    BatchScanResult,
    CompliancePolicy,
    DEFAULT_POLICY_TEMPLATES,
    InheritedPolicy,
    ManagedRepository,
    OrganizationDashboard,
    PolicyAction,
    PolicyType,
    PolicyViolation,
    RepositoryStatus,
)


logger = structlog.get_logger()


class OrchestrationManager:
    """Manages compliance across multiple repositories."""

    def __init__(self):
        self._policies: dict[UUID, CompliancePolicy] = {}
        self._repositories: dict[UUID, ManagedRepository] = {}
        self._by_org: dict[UUID, list[UUID]] = {}  # org_id -> repo_ids
        self._violations: dict[UUID, PolicyViolation] = {}
        self._inheritance: dict[UUID, InheritedPolicy] = {}  # child_org -> inheritance

    # Repository Management
    async def add_repository(
        self,
        organization_id: UUID,
        name: str,
        full_name: str,
        url: str = "",
        default_branch: str = "main",
        tracked_regulations: list[str] | None = None,
    ) -> ManagedRepository:
        """Add a repository for compliance management."""
        repo = ManagedRepository(
            organization_id=organization_id,
            name=name,
            full_name=full_name,
            url=url,
            default_branch=default_branch,
            tracked_regulations=tracked_regulations or [],
        )
        
        self._repositories[repo.id] = repo
        
        if organization_id not in self._by_org:
            self._by_org[organization_id] = []
        self._by_org[organization_id].append(repo.id)
        
        # Apply organization policies
        await self._apply_policies_to_repo(repo)
        
        logger.info(
            "Added repository for compliance tracking",
            repo_id=str(repo.id),
            full_name=full_name,
            organization_id=str(organization_id),
        )
        
        return repo

    async def get_repository(self, repo_id: UUID) -> ManagedRepository | None:
        """Get a managed repository."""
        return self._repositories.get(repo_id)

    async def list_repositories(
        self,
        organization_id: UUID,
        status: RepositoryStatus | None = None,
    ) -> list[ManagedRepository]:
        """List repositories for an organization."""
        repo_ids = self._by_org.get(organization_id, [])
        repos = [self._repositories[rid] for rid in repo_ids if rid in self._repositories]
        
        if status:
            repos = [r for r in repos if r.status == status]
        
        return repos

    async def update_repository_status(
        self,
        repo_id: UUID,
        compliance_score: float,
        open_issues: int = 0,
        critical_issues: int = 0,
    ) -> ManagedRepository | None:
        """Update repository compliance status."""
        repo = self._repositories.get(repo_id)
        if not repo:
            return None
        
        repo.compliance_score = compliance_score
        repo.open_issues = open_issues
        repo.critical_issues = critical_issues
        repo.last_scan_at = datetime.utcnow()
        repo.updated_at = datetime.utcnow()
        
        # Determine status
        if compliance_score >= 0.9 and critical_issues == 0:
            repo.status = RepositoryStatus.COMPLIANT
        elif compliance_score < 0.6 or critical_issues > 0:
            repo.status = RepositoryStatus.NON_COMPLIANT
        else:
            repo.status = RepositoryStatus.NEEDS_REVIEW
        
        # Check policy violations
        await self._check_policy_violations(repo)
        
        return repo

    # Policy Management
    async def create_policy(
        self,
        organization_id: UUID,
        name: str,
        policy_type: PolicyType,
        config: dict[str, Any],
        description: str = "",
        on_violation: PolicyAction = PolicyAction.WARN,
        applies_to: list[str] | None = None,
        created_by: str = "",
    ) -> CompliancePolicy:
        """Create a compliance policy."""
        policy = CompliancePolicy(
            organization_id=organization_id,
            name=name,
            description=description,
            policy_type=policy_type,
            config=config,
            on_violation=on_violation,
            applies_to=applies_to or ["*"],
            created_by=created_by,
        )
        
        self._policies[policy.id] = policy
        
        # Apply to existing repos
        repos = await self.list_repositories(organization_id)
        for repo in repos:
            if self._policy_applies_to_repo(policy, repo):
                repo.applied_policies.append(policy.id)
        
        logger.info(
            "Created compliance policy",
            policy_id=str(policy.id),
            name=name,
            type=policy_type.value,
        )
        
        return policy

    async def create_policy_from_template(
        self,
        organization_id: UUID,
        template_name: str,
        overrides: dict[str, Any] | None = None,
    ) -> CompliancePolicy:
        """Create a policy from a template."""
        template = DEFAULT_POLICY_TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")
        
        config = dict(template.get("config", {}))
        if overrides:
            config.update(overrides.get("config", {}))
        
        return await self.create_policy(
            organization_id=organization_id,
            name=overrides.get("name", template["name"]) if overrides else template["name"],
            policy_type=template["policy_type"],
            config=config,
            description=template.get("description", ""),
            on_violation=overrides.get("on_violation", template.get("on_violation", PolicyAction.WARN)) if overrides else template.get("on_violation", PolicyAction.WARN),
        )

    async def get_policy(self, policy_id: UUID) -> CompliancePolicy | None:
        """Get a policy by ID."""
        return self._policies.get(policy_id)

    async def list_policies(
        self,
        organization_id: UUID,
        policy_type: PolicyType | None = None,
    ) -> list[CompliancePolicy]:
        """List policies for an organization."""
        policies = [
            p for p in self._policies.values()
            if p.organization_id == organization_id and p.is_active
        ]
        
        if policy_type:
            policies = [p for p in policies if p.policy_type == policy_type]
        
        return policies

    async def _apply_policies_to_repo(self, repo: ManagedRepository) -> None:
        """Apply organization policies to a repository."""
        if not repo.organization_id:
            return
        
        policies = await self.list_policies(repo.organization_id)
        for policy in policies:
            if self._policy_applies_to_repo(policy, repo):
                repo.applied_policies.append(policy.id)

    def _policy_applies_to_repo(
        self,
        policy: CompliancePolicy,
        repo: ManagedRepository,
    ) -> bool:
        """Check if a policy applies to a repository."""
        # Check exclusions first
        for pattern in policy.excludes:
            if self._matches_pattern(repo.full_name, pattern):
                return False
        
        # Check applies_to
        for pattern in policy.applies_to:
            if pattern == "*" or pattern == "all":
                return True
            if self._matches_pattern(repo.full_name, pattern):
                return True
        
        return False

    def _matches_pattern(self, name: str, pattern: str) -> bool:
        """Check if name matches pattern (simple glob)."""
        if pattern == "*":
            return True
        if pattern.endswith("*"):
            return name.startswith(pattern[:-1])
        if pattern.startswith("*"):
            return name.endswith(pattern[1:])
        return name == pattern

    async def _check_policy_violations(self, repo: ManagedRepository) -> None:
        """Check for policy violations."""
        repo.policy_violations = []
        
        for policy_id in repo.applied_policies:
            policy = self._policies.get(policy_id)
            if not policy:
                continue
            
            violation = await self._evaluate_policy(policy, repo)
            if violation:
                self._violations[violation.id] = violation
                repo.policy_violations.append({
                    "violation_id": str(violation.id),
                    "policy_name": violation.policy_name,
                    "message": violation.message,
                    "severity": violation.severity,
                })

    async def _evaluate_policy(
        self,
        policy: CompliancePolicy,
        repo: ManagedRepository,
    ) -> PolicyViolation | None:
        """Evaluate a policy against a repository."""
        if policy.policy_type == PolicyType.MINIMUM_SCORE:
            threshold = policy.config.get("threshold", 0.7)
            if repo.compliance_score < threshold:
                return PolicyViolation(
                    policy_id=policy.id,
                    repository_id=repo.id,
                    policy_name=policy.name,
                    violation_type="minimum_score",
                    message=f"Compliance score {repo.compliance_score:.1%} below threshold {threshold:.1%}",
                    severity="high" if repo.compliance_score < threshold - 0.2 else "medium",
                    details={"score": repo.compliance_score, "threshold": threshold},
                )
        
        elif policy.policy_type == PolicyType.SCAN_FREQUENCY:
            interval_days = policy.config.get("interval_days", 7)
            if repo.last_scan_at:
                days_since_scan = (datetime.utcnow() - repo.last_scan_at).days
                if days_since_scan > interval_days:
                    return PolicyViolation(
                        policy_id=policy.id,
                        repository_id=repo.id,
                        policy_name=policy.name,
                        violation_type="scan_frequency",
                        message=f"Last scan was {days_since_scan} days ago (required: every {interval_days} days)",
                        severity="medium",
                    )
            else:
                return PolicyViolation(
                    policy_id=policy.id,
                    repository_id=repo.id,
                    policy_name=policy.name,
                    violation_type="scan_frequency",
                    message="Repository has never been scanned",
                    severity="high",
                )
        
        return None

    # Organization Dashboard
    async def get_dashboard(
        self,
        organization_id: UUID,
    ) -> OrganizationDashboard:
        """Get organization compliance dashboard."""
        repos = await self.list_repositories(organization_id)
        policies = await self.list_policies(organization_id)
        
        dashboard = OrganizationDashboard(organization_id=organization_id)
        
        # Repository stats
        dashboard.total_repositories = len(repos)
        dashboard.compliant_repositories = sum(
            1 for r in repos if r.status == RepositoryStatus.COMPLIANT
        )
        dashboard.non_compliant_repositories = sum(
            1 for r in repos if r.status == RepositoryStatus.NON_COMPLIANT
        )
        
        # Score stats
        if repos:
            scores = [r.compliance_score for r in repos]
            dashboard.average_score = sum(scores) / len(scores)
            dashboard.lowest_score = min(scores)
            dashboard.highest_score = max(scores)
        
        # Issue stats
        dashboard.total_issues = sum(r.open_issues for r in repos)
        dashboard.critical_issues = sum(r.critical_issues for r in repos)
        
        # Policy stats
        dashboard.active_policies = len(policies)
        dashboard.policy_violations = sum(len(r.policy_violations) for r in repos)
        
        # By regulation
        for repo in repos:
            for reg in repo.tracked_regulations:
                if reg not in dashboard.by_regulation:
                    dashboard.by_regulation[reg] = {
                        "repositories": 0,
                        "average_score": 0,
                        "total_score": 0,
                    }
                dashboard.by_regulation[reg]["repositories"] += 1
                dashboard.by_regulation[reg]["total_score"] += repo.compliance_score
        
        for reg, data in dashboard.by_regulation.items():
            if data["repositories"] > 0:
                data["average_score"] = data["total_score"] / data["repositories"]
        
        # Top repositories by risk
        dashboard.top_repositories_by_risk = sorted(
            [
                {
                    "name": r.full_name,
                    "score": r.compliance_score,
                    "critical_issues": r.critical_issues,
                    "status": r.status.value,
                }
                for r in repos
            ],
            key=lambda x: (x["critical_issues"], -x["score"]),
            reverse=True,
        )[:10]
        
        return dashboard

    # Batch Operations
    async def batch_scan(
        self,
        organization_id: UUID,
        repository_ids: list[UUID] | None = None,
    ) -> BatchScanResult:
        """Trigger compliance scans for multiple repositories."""
        start_time = time.perf_counter()
        
        result = BatchScanResult(organization_id=organization_id)
        
        repos = await self.list_repositories(organization_id)
        if repository_ids:
            repos = [r for r in repos if r.id in repository_ids]
        
        for repo in repos:
            try:
                # In production, would trigger actual scan
                # For now, simulate update
                repo.status = RepositoryStatus.SCANNING
                result.repositories_scanned += 1
                result.results.append({
                    "repository_id": str(repo.id),
                    "name": repo.full_name,
                    "status": "queued",
                })
            except Exception as e:
                result.repositories_failed += 1
                result.results.append({
                    "repository_id": str(repo.id),
                    "name": repo.full_name,
                    "status": "failed",
                    "error": str(e),
                })
        
        result.completed_at = datetime.utcnow()
        result.duration_seconds = time.perf_counter() - start_time
        
        return result

    # Policy Templates
    def list_policy_templates(self) -> list[dict[str, Any]]:
        """List available policy templates."""
        return [
            {
                "name": name,
                "display_name": template["name"],
                "description": template.get("description", ""),
                "policy_type": template["policy_type"].value,
                "default_action": template.get("on_violation", PolicyAction.WARN).value,
            }
            for name, template in DEFAULT_POLICY_TEMPLATES.items()
        ]


# Global instance
_manager: OrchestrationManager | None = None


def get_orchestration_manager() -> OrchestrationManager:
    """Get or create orchestration manager."""
    global _manager
    if _manager is None:
        _manager = OrchestrationManager()
    return _manager
