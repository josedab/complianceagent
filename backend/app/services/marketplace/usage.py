"""Usage Tracking - Analytics and billing for API usage."""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import structlog

from app.services.marketplace.models import (
    APIKey,
    PlanTier,
    PLAN_CONFIGS,
    Subscription,
    UsageRecord,
    UsageSummary,
    UsageType,
)


logger = structlog.get_logger()


class UsageTracker:
    """Tracks and analyzes API usage for billing and analytics."""

    def __init__(self):
        self._subscriptions: dict[UUID, Subscription] = {}
        self._usage_records: list[UsageRecord] = []

    def create_subscription(
        self,
        organization_id: UUID,
        plan_tier: PlanTier,
        products: list[UUID] | None = None,
    ) -> Subscription:
        """Create a new subscription."""
        plan_config = PLAN_CONFIGS.get(plan_tier, PLAN_CONFIGS[PlanTier.FREE])
        
        now = datetime.utcnow()
        period_end = (now.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        subscription = Subscription(
            organization_id=organization_id,
            plan_tier=plan_tier,
            subscribed_products=products or [],
            current_period_start=now,
            current_period_end=period_end,
            monthly_price=plan_config.get("price", 0),
        )
        
        self._subscriptions[organization_id] = subscription
        
        logger.info(
            "Created subscription",
            organization_id=str(organization_id),
            plan=plan_tier.value,
        )
        
        return subscription

    def get_subscription(self, organization_id: UUID) -> Subscription | None:
        """Get subscription for an organization."""
        return self._subscriptions.get(organization_id)

    def add_usage_record(self, record: UsageRecord) -> None:
        """Add a usage record."""
        self._usage_records.append(record)
        
        # Update subscription usage count
        if record.organization_id:
            sub = self._subscriptions.get(record.organization_id)
            if sub:
                sub.usage_this_period += 1

    def get_usage_summary(
        self,
        organization_id: UUID,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> UsageSummary:
        """Get usage summary for billing period."""
        now = datetime.utcnow()
        
        if not period_start:
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if not period_end:
            period_end = now
        
        # Filter records
        records = [
            r for r in self._usage_records
            if r.organization_id == organization_id
            and period_start <= r.timestamp <= period_end
        ]
        
        # Aggregate
        summary = UsageSummary(
            organization_id=organization_id,
            period_start=period_start,
            period_end=period_end,
        )
        
        for record in records:
            summary.total_requests += 1
            
            if record.usage_type == UsageType.ANALYSIS:
                summary.total_analyses += 1
            elif record.usage_type == UsageType.REPORT:
                summary.total_reports += 1
            
            # Track by product
            if record.product_id:
                pid = str(record.product_id)
                summary.by_product[pid] = summary.by_product.get(pid, 0) + 1
        
        # Calculate costs
        subscription = self._subscriptions.get(organization_id)
        if subscription:
            plan_config = PLAN_CONFIGS.get(subscription.plan_tier, PLAN_CONFIGS[PlanTier.FREE])
            included = plan_config.get("monthly_requests", 0)
            
            summary.included_requests = included if included > 0 else summary.total_requests
            summary.overage_requests = max(0, summary.total_requests - summary.included_requests)
            summary.estimated_cost = (
                subscription.monthly_price +
                summary.overage_requests * subscription.overage_rate
            )
        
        return summary

    def get_usage_analytics(
        self,
        organization_id: UUID,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get usage analytics and trends."""
        now = datetime.utcnow()
        start_date = now - timedelta(days=days)
        
        records = [
            r for r in self._usage_records
            if r.organization_id == organization_id
            and r.timestamp >= start_date
        ]
        
        # Daily breakdown
        daily_usage = {}
        for record in records:
            day = record.timestamp.strftime("%Y-%m-%d")
            if day not in daily_usage:
                daily_usage[day] = {"requests": 0, "avg_response_ms": []}
            daily_usage[day]["requests"] += 1
            daily_usage[day]["avg_response_ms"].append(record.response_time_ms)
        
        # Calculate averages
        for day, data in daily_usage.items():
            times = data["avg_response_ms"]
            data["avg_response_ms"] = sum(times) / len(times) if times else 0
        
        # By endpoint
        by_endpoint = {}
        for record in records:
            if record.endpoint not in by_endpoint:
                by_endpoint[record.endpoint] = {"count": 0, "errors": 0}
            by_endpoint[record.endpoint]["count"] += 1
            if record.status_code >= 400:
                by_endpoint[record.endpoint]["errors"] += 1
        
        # Top endpoints
        top_endpoints = sorted(
            by_endpoint.items(),
            key=lambda x: x[1]["count"],
            reverse=True,
        )[:10]
        
        # Error rate
        total_errors = sum(1 for r in records if r.status_code >= 400)
        error_rate = (total_errors / len(records) * 100) if records else 0
        
        return {
            "organization_id": str(organization_id),
            "period_days": days,
            "total_requests": len(records),
            "daily_usage": daily_usage,
            "top_endpoints": [
                {"endpoint": e, "count": d["count"], "errors": d["errors"]}
                for e, d in top_endpoints
            ],
            "error_rate_percent": round(error_rate, 2),
            "avg_response_time_ms": round(
                sum(r.response_time_ms for r in records) / len(records) if records else 0,
                2,
            ),
        }

    def get_billing_invoice(
        self,
        organization_id: UUID,
        month: int | None = None,
        year: int | None = None,
    ) -> dict[str, Any]:
        """Generate billing invoice for a month."""
        now = datetime.utcnow()
        month = month or now.month
        year = year or now.year
        
        period_start = datetime(year, month, 1)
        if month == 12:
            period_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            period_end = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        summary = self.get_usage_summary(
            organization_id=organization_id,
            period_start=period_start,
            period_end=period_end,
        )
        
        subscription = self._subscriptions.get(organization_id)
        
        line_items = []
        
        # Base subscription
        if subscription:
            line_items.append({
                "description": f"{subscription.plan_tier.value.title()} Plan",
                "quantity": 1,
                "unit_price": subscription.monthly_price,
                "total": subscription.monthly_price,
            })
        
        # Overage
        if summary.overage_requests > 0:
            overage_rate = subscription.overage_rate if subscription else 0.01
            overage_total = summary.overage_requests * overage_rate
            line_items.append({
                "description": f"API Overage ({summary.overage_requests:,} requests)",
                "quantity": summary.overage_requests,
                "unit_price": overage_rate,
                "total": overage_total,
            })
        
        total = sum(item["total"] for item in line_items)
        
        return {
            "organization_id": str(organization_id),
            "invoice_period": f"{year}-{month:02d}",
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "usage_summary": {
                "total_requests": summary.total_requests,
                "included_requests": summary.included_requests,
                "overage_requests": summary.overage_requests,
            },
            "line_items": line_items,
            "subtotal": total,
            "tax": 0,  # Would calculate based on location
            "total": total,
            "currency": "USD",
        }


# Global instance
_tracker: UsageTracker | None = None


def get_usage_tracker() -> UsageTracker:
    """Get or create usage tracker."""
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker
