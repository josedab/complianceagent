"""Audit logging templates for SOX, HIPAA, SOC 2 compliance."""

from app.services.templates.base import (
    ComplianceTemplate,
    TemplateCategory,
)


AUDIT_LOGGER_TEMPLATE = ComplianceTemplate(
    name="Compliance Audit Logger",
    description="Comprehensive audit logging for SOX, HIPAA, and security compliance",
    category=TemplateCategory.AUDIT_LOGGING,
    regulations=["SOX", "HIPAA", "SOC 2", "ISO 27001"],
    languages=["python", "typescript"],
    code={
        "python": '''"""Compliance audit logging module.

Implements comprehensive audit logging for SOX, HIPAA, and SOC 2.
"""

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4


class AuditAction(str, Enum):
    """Types of auditable actions."""
    
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    MFA_ENABLED = "mfa_enabled"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    ACCESS_DENIED = "access_denied"
    CONFIG_CHANGE = "config_change"
    BACKUP = "backup"
    RESTORE = "restore"


@dataclass
class AuditEntry:
    """An audit log entry with tamper-evident hash chain."""
    
    id: UUID
    timestamp: datetime
    action: AuditAction
    actor_id: str
    actor_type: str
    resource_type: str
    resource_id: str
    organization_id: str
    details: dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    result: str
    previous_hash: str
    entry_hash: str
    
    def compute_hash(self, previous_hash: str) -> str:
        """Compute hash for tamper detection."""
        content = json.dumps({
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "actor_id": self.actor_id,
            "resource_id": self.resource_id,
            "details": self.details,
            "previous_hash": previous_hash,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class AuditLogger:
    """Compliance audit logger with hash chain verification.
    
    Compliance:
    - SOX Section 802: Records retention and integrity
    - HIPAA 45 CFR 164.312(b): Audit controls
    - SOC 2: Change management and logging
    """
    
    def __init__(self, storage, organization_id: str):
        self.storage = storage
        self.organization_id = organization_id
        self._last_hash = "GENESIS"
    
    async def log(
        self,
        action: AuditAction,
        actor_id: str,
        resource_type: str,
        resource_id: str,
        details: dict[str, Any],
        actor_type: str = "user",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        result: str = "success",
    ) -> AuditEntry:
        """Log an auditable event."""
        entry = AuditEntry(
            id=uuid4(),
            timestamp=datetime.now(UTC),
            action=action,
            actor_id=actor_id,
            actor_type=actor_type,
            resource_type=resource_type,
            resource_id=resource_id,
            organization_id=self.organization_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            result=result,
            previous_hash=self._last_hash,
            entry_hash="",
        )
        
        entry.entry_hash = entry.compute_hash(self._last_hash)
        self._last_hash = entry.entry_hash
        
        await self.storage.save(entry)
        return entry
    
    async def verify_chain(
        self,
        start_id: Optional[UUID] = None,
        end_id: Optional[UUID] = None,
    ) -> tuple[bool, list[str]]:
        """Verify the integrity of the audit chain."""
        entries = await self.storage.get_range(start_id, end_id)
        errors = []
        
        previous_hash = "GENESIS"
        for entry in entries:
            expected_hash = entry.compute_hash(previous_hash)
            if entry.entry_hash != expected_hash:
                errors.append(
                    f"Hash mismatch at entry {entry.id}: "
                    f"expected {expected_hash}, got {entry.entry_hash}"
                )
            previous_hash = entry.entry_hash
        
        return len(errors) == 0, errors
    
    async def search(
        self,
        actor_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """Search audit logs with filters."""
        return await self.storage.search(
            actor_id=actor_id,
            resource_type=resource_type,
            action=action,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    
    async def export(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json",
    ) -> bytes:
        """Export audit logs for external review."""
        entries = await self.storage.get_range_by_date(start_date, end_date)
        
        if format == "json":
            data = [asdict(e) for e in entries]
            return json.dumps(data, default=str, indent=2).encode()
        
        raise ValueError(f"Unsupported format: {format}")
''',
    },
    documentation="""# Compliance Audit Logger

## Overview
Tamper-evident audit logging for SOX, HIPAA, and SOC 2 compliance.

## Features
- Hash chain for tamper detection
- Comprehensive action tracking
- Chain verification
- Exportable for external audits
""",
    parameters=[],
    tags=["audit", "sox", "hipaa", "soc2", "logging", "compliance"],
)


AUDIT_TEMPLATES = [AUDIT_LOGGER_TEMPLATE]
