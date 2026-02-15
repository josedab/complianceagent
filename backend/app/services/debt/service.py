"""Compliance Debt Securitization service."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import structlog

from app.services.debt.models import (
    ComplianceBond,
    ComplianceDebtItem,
    CreditRating,
    DebtPortfolio,
    DebtPriority,
)

logger = structlog.get_logger()

_DEBT_ITEMS: list[ComplianceDebtItem] = [
    ComplianceDebtItem(
        id=uuid4(), title="Missing encryption for user PII at rest",
        description="User table stores email and phone in plaintext. Requires AES-256 encryption.",
        priority=DebtPriority.CRITICAL, framework="GDPR", control="Art. 32",
        risk_score=9.2, cost_of_delay_per_day=150.0, accrued_interest=4500.0,
        remediation_cost=2000.0, days_outstanding=30, assigned_team="Platform",
    ),
    ComplianceDebtItem(
        id=uuid4(), title="Incomplete audit logging on admin endpoints",
        description="15 admin endpoints lack structured audit logging for SOC 2 CC7.2.",
        priority=DebtPriority.HIGH, framework="SOC 2", control="CC7.2",
        risk_score=7.5, cost_of_delay_per_day=85.0, accrued_interest=1700.0,
        remediation_cost=1200.0, days_outstanding=20, assigned_team="Security",
    ),
    ComplianceDebtItem(
        id=uuid4(), title="Outdated dependency with known CVE",
        description="lodash@4.17.15 has CVE-2021-23337 (prototype pollution). Upgrade required.",
        priority=DebtPriority.HIGH, framework="PCI-DSS", control="Req. 6.2",
        risk_score=6.8, cost_of_delay_per_day=65.0, accrued_interest=975.0,
        remediation_cost=400.0, days_outstanding=15, assigned_team="Frontend",
    ),
    ComplianceDebtItem(
        id=uuid4(), title="Missing consent banner for analytics cookies",
        description="Analytics tracking runs before user consent on EU visitors.",
        priority=DebtPriority.MEDIUM, framework="GDPR", control="Art. 7",
        risk_score=5.5, cost_of_delay_per_day=40.0, accrued_interest=400.0,
        remediation_cost=800.0, days_outstanding=10, assigned_team="Frontend",
    ),
    ComplianceDebtItem(
        id=uuid4(), title="No data retention policy enforcement",
        description="User data retained indefinitely. GDPR Art. 5(1)(e) requires time-limited storage.",
        priority=DebtPriority.MEDIUM, framework="GDPR", control="Art. 5(1)(e)",
        risk_score=6.0, cost_of_delay_per_day=55.0, accrued_interest=1650.0,
        remediation_cost=1500.0, days_outstanding=30, assigned_team="Backend",
    ),
    ComplianceDebtItem(
        id=uuid4(), title="Password policy below NIST guidelines",
        description="Current: 8 chars min, no complexity. NIST SP 800-63B recommends 8+ with breach checks.",
        priority=DebtPriority.LOW, framework="SOC 2", control="CC6.1",
        risk_score=4.0, cost_of_delay_per_day=25.0, accrued_interest=250.0,
        remediation_cost=600.0, days_outstanding=10, assigned_team="Security",
    ),
]


class DebtSecuritizationService:
    """Service for compliance debt securitization."""

    async def list_debt_items(
        self, priority: DebtPriority | None = None, framework: str | None = None,
    ) -> list[ComplianceDebtItem]:
        result = list(_DEBT_ITEMS)
        if priority:
            result = [d for d in result if d.priority == priority]
        if framework:
            result = [d for d in result if d.framework.lower() == framework.lower()]
        return result

    async def get_portfolio(self) -> DebtPortfolio:
        total = sum(d.remediation_cost + d.accrued_interest for d in _DEBT_ITEMS)
        critical = sum(1 for d in _DEBT_ITEMS if d.priority == DebtPriority.CRITICAL)
        high = sum(1 for d in _DEBT_ITEMS if d.priority == DebtPriority.HIGH)
        medium = sum(1 for d in _DEBT_ITEMS if d.priority == DebtPriority.MEDIUM)
        low = sum(1 for d in _DEBT_ITEMS if d.priority == DebtPriority.LOW)
        avg_days = sum(d.days_outstanding for d in _DEBT_ITEMS) / max(len(_DEBT_ITEMS), 1)
        daily_rate = sum(d.cost_of_delay_per_day for d in _DEBT_ITEMS)

        rating = CreditRating.BBB
        if critical == 0 and high <= 1:
            rating = CreditRating.A
        elif critical >= 2:
            rating = CreditRating.BB

        by_framework: dict[str, float] = {}
        for d in _DEBT_ITEMS:
            by_framework[d.framework] = by_framework.get(d.framework, 0) + d.remediation_cost + d.accrued_interest

        return DebtPortfolio(
            total_debt_value=total, total_items=len(_DEBT_ITEMS),
            critical_items=critical, high_items=high, medium_items=medium, low_items=low,
            avg_days_outstanding=avg_days, daily_accrual_rate=daily_rate,
            credit_rating=rating, debt_by_framework=by_framework,
            remediation_velocity=2.5, projected_payoff_days=int(total / (daily_rate * 0.3)),
        )

    async def get_bonds(self) -> list[ComplianceBond]:
        bonds = []
        frameworks = set(d.framework for d in _DEBT_ITEMS)
        for fw in frameworks:
            items = [d for d in _DEBT_ITEMS if d.framework == fw]
            face = sum(d.remediation_cost + d.accrued_interest for d in items)
            bonds.append(ComplianceBond(
                id=uuid4(), name=f"{fw} Compliance Bond", face_value=face,
                current_value=face * 1.05, interest_rate=0.05, framework=fw,
                debt_items_count=len(items), yield_spread=0.02,
                maturity_date=datetime.utcnow() + timedelta(days=90),
            ))
        return bonds

    async def get_credit_rating(self) -> dict:
        portfolio = await self.get_portfolio()
        trend = "stable"
        if portfolio.critical_items > 0:
            trend = "negative"
        return {
            "rating": portfolio.credit_rating.value,
            "trend": trend,
            "total_debt": portfolio.total_debt_value,
            "daily_accrual": portfolio.daily_accrual_rate,
            "projected_payoff_days": portfolio.projected_payoff_days,
        }
