"""Compliance Debt Tracker Service."""

from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.compliance_debt.models import (
    ComplianceDebtItem,
    DebtPriority,
    DebtStats,
    DebtStatus,
    SprintBurndown,
)


logger = structlog.get_logger()

_SEED_DEBT_ITEMS: list[dict] = [
    {
        "title": "Unencrypted PII in user_profiles table",
        "description": "Personal data stored without column-level encryption",
        "framework": "GDPR",
        "rule_id": "Art.32",
        "file_path": "src/models/user_profiles.py",
        "severity": "critical",
        "risk_cost_usd": 250000.0,
        "remediation_cost_usd": 15000.0,
        "days_open": 45,
        "repo": "backend-api",
    },
    {
        "title": "Missing audit trail for PHI access",
        "description": "No logging of read access to protected health information",
        "framework": "HIPAA",
        "rule_id": "§164.312(b)",
        "file_path": "src/services/health_records.py",
        "severity": "critical",
        "risk_cost_usd": 500000.0,
        "remediation_cost_usd": 20000.0,
        "days_open": 30,
        "repo": "health-platform",
    },
    {
        "title": "Card numbers in application logs",
        "description": "PAN data occasionally appears in debug log output",
        "framework": "PCI-DSS",
        "rule_id": "Req.3.4",
        "file_path": "src/payments/processor.py",
        "severity": "high",
        "risk_cost_usd": 100000.0,
        "remediation_cost_usd": 5000.0,
        "days_open": 21,
        "repo": "payment-service",
    },
    {
        "title": "Consent withdrawal not propagated to analytics",
        "description": "User consent revocation does not reach downstream analytics pipeline",
        "framework": "GDPR",
        "rule_id": "Art.7(3)",
        "file_path": "src/analytics/pipeline.py",
        "severity": "high",
        "risk_cost_usd": 150000.0,
        "remediation_cost_usd": 12000.0,
        "days_open": 60,
        "repo": "analytics-engine",
    },
    {
        "title": "Expired TLS certificate on internal API",
        "description": "Internal microservice communication using expired certificate",
        "framework": "PCI-DSS",
        "rule_id": "Req.4.1",
        "file_path": "infra/tls/internal-cert.pem",
        "severity": "medium",
        "risk_cost_usd": 50000.0,
        "remediation_cost_usd": 2000.0,
        "days_open": 7,
        "repo": "infrastructure",
    },
    {
        "title": "No data retention policy enforcement",
        "description": "Data older than retention period not being automatically purged",
        "framework": "GDPR",
        "rule_id": "Art.5(1)(e)",
        "file_path": "src/jobs/data_cleanup.py",
        "severity": "medium",
        "risk_cost_usd": 80000.0,
        "remediation_cost_usd": 10000.0,
        "days_open": 90,
        "repo": "backend-api",
    },
    {
        "title": "Backup encryption key not rotated",
        "description": "Encryption key for database backups has not been rotated in 18 months",
        "framework": "HIPAA",
        "rule_id": "§164.312(a)(2)(iv)",
        "file_path": "infra/backup/config.yaml",
        "severity": "low",
        "risk_cost_usd": 30000.0,
        "remediation_cost_usd": 3000.0,
        "days_open": 120,
        "repo": "infrastructure",
    },
    {
        "title": "Weak password policy on admin portal",
        "description": "Admin portal allows passwords shorter than 12 characters without MFA",
        "framework": "PCI-DSS",
        "rule_id": "Req.8.3",
        "file_path": "src/auth/password_policy.py",
        "severity": "high",
        "risk_cost_usd": 200000.0,
        "remediation_cost_usd": 8000.0,
        "days_open": 14,
        "repo": "admin-portal",
    },
]


class ComplianceDebtService:
    """Track and prioritize compliance technical debt."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._items: dict[str, ComplianceDebtItem] = {}
        self._sprints: list[SprintBurndown] = []
        self._seed_data()

    def _seed_data(self) -> None:
        for item_def in _SEED_DEBT_ITEMS:
            item = ComplianceDebtItem(
                title=item_def["title"],
                description=item_def["description"],
                framework=item_def["framework"],
                rule_id=item_def["rule_id"],
                file_path=item_def["file_path"],
                severity=DebtPriority(item_def["severity"]),
                status=DebtStatus.OPEN,
                risk_cost_usd=item_def["risk_cost_usd"],
                remediation_cost_usd=item_def["remediation_cost_usd"],
                roi=self._calculate_roi(item_def["risk_cost_usd"], item_def["remediation_cost_usd"]),
                days_open=item_def["days_open"],
                repo=item_def["repo"],
                created_at=datetime.now(UTC),
            )
            self._items[str(item.id)] = item

    @staticmethod
    def _calculate_roi(risk_cost: float, remediation_cost: float) -> float:
        if remediation_cost <= 0:
            return 0.0
        return round((risk_cost - remediation_cost) / remediation_cost, 2)

    async def add_debt_item(
        self,
        title: str,
        description: str,
        framework: str,
        rule_id: str,
        file_path: str,
        severity: str,
        risk_cost_usd: float,
        remediation_cost_usd: float,
        repo: str = "",
    ) -> ComplianceDebtItem:
        item = ComplianceDebtItem(
            title=title,
            description=description,
            framework=framework,
            rule_id=rule_id,
            file_path=file_path,
            severity=DebtPriority(severity),
            status=DebtStatus.OPEN,
            risk_cost_usd=risk_cost_usd,
            remediation_cost_usd=remediation_cost_usd,
            roi=self._calculate_roi(risk_cost_usd, remediation_cost_usd),
            days_open=0,
            repo=repo,
            created_at=datetime.now(UTC),
        )
        self._items[str(item.id)] = item
        logger.info("Debt item added", item_id=str(item.id), framework=framework, roi=item.roi)
        return item

    async def resolve_debt(self, item_id: str) -> ComplianceDebtItem:
        item = self._items.get(item_id)
        if not item:
            raise ValueError(f"Debt item not found: {item_id}")
        item.status = DebtStatus.RESOLVED
        logger.info("Debt item resolved", item_id=item_id, title=item.title)
        return item

    async def acknowledge_debt(self, item_id: str) -> ComplianceDebtItem:
        item = self._items.get(item_id)
        if not item:
            raise ValueError(f"Debt item not found: {item_id}")
        item.status = DebtStatus.ACKNOWLEDGED
        logger.info("Debt item acknowledged", item_id=item_id, title=item.title)
        return item

    async def list_debt(self, sort_by_roi: bool = True, framework: str | None = None) -> list[ComplianceDebtItem]:
        items = list(self._items.values())
        if framework:
            items = [i for i in items if i.framework == framework]
        if sort_by_roi:
            items.sort(key=lambda x: x.roi, reverse=True)
        return items

    def get_burndown(self) -> list[SprintBurndown]:
        total = len(self._items)
        resolved = sum(1 for i in self._items.values() if i.status == DebtStatus.RESOLVED)
        remaining = total - resolved
        self._sprints.append(
            SprintBurndown(
                sprint_name=f"Sprint {len(self._sprints) + 1}",
                start_items=total,
                resolved=resolved,
                remaining=remaining,
                velocity=round(resolved / max(len(self._sprints) + 1, 1), 1),
            )
        )
        return self._sprints

    def get_stats(self) -> DebtStats:
        items = list(self._items.values())
        by_priority: dict[str, int] = {}
        by_status: dict[str, int] = {}
        by_framework: dict[str, int] = {}
        rois: list[float] = []

        for item in items:
            by_priority[item.severity.value] = by_priority.get(item.severity.value, 0) + 1
            by_status[item.status.value] = by_status.get(item.status.value, 0) + 1
            by_framework[item.framework] = by_framework.get(item.framework, 0) + 1
            rois.append(item.roi)

        return DebtStats(
            total_items=len(items),
            by_priority=by_priority,
            by_status=by_status,
            by_framework=by_framework,
            total_risk_usd=sum(i.risk_cost_usd for i in items),
            total_remediation_usd=sum(i.remediation_cost_usd for i in items),
            avg_roi=round(sum(rois) / len(rois), 2) if rois else 0.0,
        )
