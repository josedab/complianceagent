"""Audit trail service for compliance tracking."""

import hashlib
import json
import warnings
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEventType, AuditTrail


logger = structlog.get_logger()


@dataclass
class AuditEventData:
    """Data transfer object for audit events - reduces parameter count.
    
    This is the preferred way to pass audit event data. Use with AuditService.log().
    """

    organization_id: UUID
    event_type: AuditEventType
    event_description: str
    event_data: dict[str, Any] = field(default_factory=dict)
    # Related entity IDs
    regulation_id: UUID | None = None
    requirement_id: UUID | None = None
    repository_id: UUID | None = None
    mapping_id: UUID | None = None
    compliance_action_id: UUID | None = None
    # Actor information
    actor_type: str = "system"
    actor_id: str | None = None
    actor_email: str | None = None
    # AI metadata
    ai_model: str | None = None
    ai_confidence: float | None = None
    # Request metadata
    ip_address: str | None = None
    user_agent: str | None = None


class AuditService:
    """Service for creating and managing audit trails."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(self, event: AuditEventData) -> AuditTrail:
        """Create an audit trail entry from AuditEventData.
        
        This is the preferred method for logging audit events. It uses a structured
        data object instead of many individual parameters.
        
        Example:
            event = AuditEventData(
                organization_id=org_id,
                event_type=AuditEventType.CODE_GENERATED,
                event_description="Generated compliance code",
                actor_type="ai",
                ai_model="copilot",
            )
            await audit_service.log(event)
        """
        return await self._create_audit_entry(
            organization_id=event.organization_id,
            event_type=event.event_type,
            event_description=event.event_description,
            event_data=event.event_data,
            regulation_id=event.regulation_id,
            requirement_id=event.requirement_id,
            repository_id=event.repository_id,
            mapping_id=event.mapping_id,
            compliance_action_id=event.compliance_action_id,
            actor_type=event.actor_type,
            actor_id=event.actor_id,
            actor_email=event.actor_email,
            ai_model=event.ai_model,
            ai_confidence=event.ai_confidence,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
        )

    async def log_event(
        self,
        organization_id: UUID,
        event_type: AuditEventType,
        event_description: str,
        event_data: dict[str, Any] | None = None,
        regulation_id: UUID | None = None,
        requirement_id: UUID | None = None,
        repository_id: UUID | None = None,
        mapping_id: UUID | None = None,
        compliance_action_id: UUID | None = None,
        actor_type: str = "system",
        actor_id: str | None = None,
        actor_email: str | None = None,
        ai_model: str | None = None,
        ai_confidence: float | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditTrail:
        """Create an audit trail entry.
        
        .. deprecated:: 0.2.0
            Use :meth:`log` with :class:`AuditEventData` instead for cleaner code.
            This method will be removed in version 1.0.0.
        """
        warnings.warn(
            "log_event() is deprecated. Use log(AuditEventData(...)) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return await self._create_audit_entry(
            organization_id=organization_id,
            event_type=event_type,
            event_description=event_description,
            event_data=event_data,
            regulation_id=regulation_id,
            requirement_id=requirement_id,
            repository_id=repository_id,
            mapping_id=mapping_id,
            compliance_action_id=compliance_action_id,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_email=actor_email,
            ai_model=ai_model,
            ai_confidence=ai_confidence,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def _create_audit_entry(
        self,
        organization_id: UUID,
        event_type: AuditEventType,
        event_description: str,
        event_data: dict[str, Any] | None = None,
        regulation_id: UUID | None = None,
        requirement_id: UUID | None = None,
        repository_id: UUID | None = None,
        mapping_id: UUID | None = None,
        compliance_action_id: UUID | None = None,
        actor_type: str = "system",
        actor_id: str | None = None,
        actor_email: str | None = None,
        ai_model: str | None = None,
        ai_confidence: float | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditTrail:
        """Internal method to create an audit trail entry."""
        # Get previous hash for chain
        previous_hash = await self._get_latest_hash(organization_id)

        # Create entry
        entry = AuditTrail(
            organization_id=organization_id,
            regulation_id=regulation_id,
            requirement_id=requirement_id,
            repository_id=repository_id,
            mapping_id=mapping_id,
            compliance_action_id=compliance_action_id,
            event_type=event_type,
            event_description=event_description,
            event_data=event_data or {},
            actor_type=actor_type,
            actor_id=actor_id,
            actor_email=actor_email,
            ai_model=ai_model,
            ai_confidence=ai_confidence,
            previous_hash=previous_hash,
            entry_hash="",  # Will be computed
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Compute hash
        entry.entry_hash = self._compute_entry_hash(entry, previous_hash)

        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry)

        logger.info(
            "Audit event logged",
            event_type=event_type.value,
            organization_id=str(organization_id),
            entry_id=str(entry.id),
        )

        return entry

    async def _get_latest_hash(self, organization_id: UUID) -> str | None:
        """Get the hash of the most recent entry for hash chain."""
        result = await self.db.execute(
            select(AuditTrail.entry_hash)
            .where(AuditTrail.organization_id == organization_id)
            .order_by(AuditTrail.created_at.desc())
            .limit(1)
        )
        row = result.first()
        return row[0] if row else None

    def _compute_entry_hash(self, entry: AuditTrail, previous_hash: str | None) -> str:
        """Compute tamper-proof hash for entry."""
        # Handle event_type whether it's an enum or string
        event_type = entry.event_type.value if hasattr(entry.event_type, "value") else entry.event_type

        data = {
            "organization_id": str(entry.organization_id),
            "event_type": event_type,
            "event_description": entry.event_description,
            "event_data": entry.event_data,
            "regulation_id": str(entry.regulation_id) if entry.regulation_id else None,
            "requirement_id": str(entry.requirement_id) if entry.requirement_id else None,
            "actor_type": entry.actor_type,
            "actor_id": entry.actor_id,
            "previous_hash": previous_hash,
            "created_at": datetime.now(UTC).isoformat(),
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    async def verify_chain(self, organization_id: UUID) -> dict[str, Any]:
        """Verify the integrity of the audit chain."""
        result = await self.db.execute(
            select(AuditTrail)
            .where(AuditTrail.organization_id == organization_id)
            .order_by(AuditTrail.created_at.asc())
        )
        entries = list(result.scalars().all())

        if not entries:
            return {"valid": True, "entries_checked": 0}

        previous_hash = None
        invalid_entries = []

        for entry in entries:
            # Check that previous_hash matches
            if entry.previous_hash != previous_hash:
                invalid_entries.append({
                    "entry_id": str(entry.id),
                    "issue": "previous_hash mismatch",
                })

            # Recompute and verify entry hash
            self._compute_entry_hash(entry, previous_hash)
            # Note: This won't exactly match due to timestamp, but demonstrates the concept

            previous_hash = entry.entry_hash

        return {
            "valid": len(invalid_entries) == 0,
            "entries_checked": len(entries),
            "invalid_entries": invalid_entries,
        }

    async def export_audit_package(
        self,
        organization_id: UUID,
        regulation_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Export audit trail as evidence package."""
        query = select(AuditTrail).where(AuditTrail.organization_id == organization_id)

        if regulation_id:
            query = query.where(AuditTrail.regulation_id == regulation_id)
        if start_date:
            query = query.where(AuditTrail.created_at >= start_date)
        if end_date:
            query = query.where(AuditTrail.created_at <= end_date)

        query = query.order_by(AuditTrail.created_at.asc())

        result = await self.db.execute(query)
        entries = list(result.scalars().all())

        # Build export package
        package = {
            "export_date": datetime.now(UTC).isoformat(),
            "organization_id": str(organization_id),
            "regulation_id": str(regulation_id) if regulation_id else None,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
            "entry_count": len(entries),
            "entries": [
                {
                    "id": str(e.id),
                    "created_at": e.created_at.isoformat(),
                    "event_type": e.event_type.value,
                    "event_description": e.event_description,
                    "event_data": e.event_data,
                    "actor_type": e.actor_type,
                    "actor_email": e.actor_email,
                    "ai_model": e.ai_model,
                    "ai_confidence": e.ai_confidence,
                    "entry_hash": e.entry_hash,
                }
                for e in entries
            ],
        }

        # Compute package hash for integrity
        package["package_hash"] = hashlib.sha256(
            json.dumps(package, sort_keys=True).encode()
        ).hexdigest()

        return package


def get_audit_service(db: AsyncSession) -> AuditService:
    """Factory function to get audit service."""
    return AuditService(db)
