"""Audit logging for compliance tracking."""

import hashlib
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class AuditAction(str, Enum):
    """Standard audit actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    ACCESS = "access"
    EXPORT = "export"
    CONSENT_GRANTED = "consent_granted"
    CONSENT_REVOKED = "consent_revoked"
    LOGIN = "login"
    LOGOUT = "logout"
    FAILED_LOGIN = "failed_login"
    PERMISSION_DENIED = "permission_denied"
    DATA_BREACH = "data_breach"
    ENCRYPTION = "encryption"
    DECRYPTION = "decryption"


class AuditSeverity(str, Enum):
    """Audit event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEntry:
    """An audit log entry."""
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Action details
    action: str = ""
    resource_type: str = ""
    resource_id: str | None = None
    
    # Actor information
    user_id: str | None = None
    user_email: str | None = None
    user_role: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    
    # Compliance context
    regulation: str | None = None
    requirement: str | None = None
    data_types: list[str] = field(default_factory=list)
    
    # Event details
    severity: AuditSeverity = AuditSeverity.INFO
    outcome: str = "success"  # success, failure, blocked
    details: dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    service_name: str = ""
    function_name: str = ""
    module_name: str = ""
    
    # Chain integrity
    previous_hash: str | None = None
    entry_hash: str | None = None
    
    def compute_hash(self, previous_hash: str | None = None) -> str:
        """Compute tamper-evident hash for this entry."""
        self.previous_hash = previous_hash
        
        # Create canonical representation
        canonical = {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "outcome": self.outcome,
            "previous_hash": previous_hash,
        }
        
        content = json.dumps(canonical, sort_keys=True)
        self.entry_hash = hashlib.sha256(content.encode()).hexdigest()
        return self.entry_hash
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "user_role": self.user_role,
            "ip_address": self.ip_address,
            "regulation": self.regulation,
            "requirement": self.requirement,
            "data_types": self.data_types,
            "severity": self.severity.value,
            "outcome": self.outcome,
            "details": self.details,
            "service_name": self.service_name,
            "function_name": self.function_name,
            "entry_hash": self.entry_hash,
        }


class AuditLogger:
    """Logger for compliance audit trail.
    
    Provides tamper-evident logging with hash chains for compliance audits.
    
    Example:
        logger = AuditLogger(service_name="user-service")
        
        logger.log(
            action=AuditAction.READ,
            resource_type="user",
            resource_id="123",
            user_id="admin@example.com",
            regulation="GDPR",
        )
    """
    
    def __init__(
        self,
        service_name: str = "default",
        output_file: str | None = None,
        log_to_stdout: bool = True,
        api_endpoint: str | None = None,
        api_key: str | None = None,
    ):
        self.service_name = service_name
        self.output_file = output_file
        self.log_to_stdout = log_to_stdout
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        
        self._last_hash: str | None = None
        self._entries: list[AuditEntry] = []
        
        # Set up Python logger
        self._logger = logging.getLogger(f"complianceagent.audit.{service_name}")
        self._logger.setLevel(logging.INFO)
        
        if log_to_stdout:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - AUDIT - %(message)s'
            ))
            self._logger.addHandler(handler)
        
        if output_file:
            file_handler = logging.FileHandler(output_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(message)s'
            ))
            self._logger.addHandler(file_handler)
    
    def log(
        self,
        action: AuditAction | str,
        resource_type: str,
        resource_id: str | None = None,
        user_id: str | None = None,
        user_email: str | None = None,
        user_role: str | None = None,
        ip_address: str | None = None,
        regulation: str | None = None,
        requirement: str | None = None,
        data_types: list[str] | None = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        outcome: str = "success",
        details: dict[str, Any] | None = None,
        function_name: str | None = None,
        module_name: str | None = None,
    ) -> AuditEntry:
        """Log an audit entry.
        
        Args:
            action: The action being audited
            resource_type: Type of resource (user, file, record, etc.)
            resource_id: ID of the specific resource
            user_id: ID of the user performing the action
            user_email: Email of the user
            user_role: Role of the user
            ip_address: IP address of the request
            regulation: Relevant regulation (GDPR, HIPAA, etc.)
            requirement: Specific requirement being addressed
            data_types: Types of data involved (PII, PHI, etc.)
            severity: Severity level of the event
            outcome: Outcome of the action
            details: Additional details
            function_name: Name of the function being audited
            module_name: Name of the module
        
        Returns:
            The created AuditEntry
        """
        if isinstance(action, str):
            action_str = action
        else:
            action_str = action.value
        
        entry = AuditEntry(
            action=action_str,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            user_email=user_email,
            user_role=user_role,
            ip_address=ip_address,
            regulation=regulation,
            requirement=requirement,
            data_types=data_types or [],
            severity=severity,
            outcome=outcome,
            details=details or {},
            service_name=self.service_name,
            function_name=function_name or "",
            module_name=module_name or "",
        )
        
        # Compute hash for chain integrity
        entry.compute_hash(self._last_hash)
        self._last_hash = entry.entry_hash
        
        # Store entry
        self._entries.append(entry)
        
        # Log to configured outputs
        log_message = self._format_log_message(entry)
        
        if severity == AuditSeverity.CRITICAL:
            self._logger.critical(log_message)
        elif severity == AuditSeverity.ERROR:
            self._logger.error(log_message)
        elif severity == AuditSeverity.WARNING:
            self._logger.warning(log_message)
        else:
            self._logger.info(log_message)
        
        # Send to API if configured
        if self.api_endpoint:
            self._send_to_api(entry)
        
        return entry
    
    def _format_log_message(self, entry: AuditEntry) -> str:
        """Format audit entry as log message."""
        parts = [
            f"action={entry.action}",
            f"resource={entry.resource_type}:{entry.resource_id or 'N/A'}",
            f"user={entry.user_id or 'anonymous'}",
            f"outcome={entry.outcome}",
        ]
        
        if entry.regulation:
            parts.append(f"regulation={entry.regulation}")
        
        if entry.data_types:
            parts.append(f"data_types={','.join(entry.data_types)}")
        
        return " | ".join(parts)
    
    def _send_to_api(self, entry: AuditEntry) -> None:
        """Send audit entry to ComplianceAgent API."""
        if not self.api_endpoint:
            return
        
        try:
            import httpx
            
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            httpx.post(
                f"{self.api_endpoint}/audit",
                json=entry.to_dict(),
                headers=headers,
                timeout=5.0,
            )
        except Exception as e:
            self._logger.error(f"Failed to send audit entry to API: {e}")
    
    def log_consent(
        self,
        user_id: str,
        consent_type: str,
        granted: bool,
        **kwargs: Any,
    ) -> AuditEntry:
        """Log a consent event."""
        action = AuditAction.CONSENT_GRANTED if granted else AuditAction.CONSENT_REVOKED
        return self.log(
            action=action,
            resource_type="consent",
            resource_id=consent_type,
            user_id=user_id,
            regulation="GDPR",
            requirement="Article 7 - Consent",
            details={"consent_type": consent_type, "granted": granted, **kwargs},
        )
    
    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        data_types: list[str],
        **kwargs: Any,
    ) -> AuditEntry:
        """Log a data access event."""
        return self.log(
            action=AuditAction.ACCESS,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            data_types=data_types,
            **kwargs,
        )
    
    def log_phi_access(
        self,
        user_id: str,
        patient_id: str,
        purpose: str,
        **kwargs: Any,
    ) -> AuditEntry:
        """Log PHI access for HIPAA compliance."""
        return self.log(
            action=AuditAction.ACCESS,
            resource_type="phi",
            resource_id=patient_id,
            user_id=user_id,
            regulation="HIPAA",
            requirement="164.312(b) - Audit Controls",
            data_types=["PHI"],
            details={"purpose": purpose, **kwargs},
        )
    
    def log_security_event(
        self,
        event_type: str,
        severity: AuditSeverity,
        details: dict[str, Any],
        **kwargs: Any,
    ) -> AuditEntry:
        """Log a security event."""
        return self.log(
            action=event_type,
            resource_type="security",
            severity=severity,
            details=details,
            **kwargs,
        )
    
    def verify_chain(self) -> tuple[bool, list[str]]:
        """Verify the integrity of the audit chain.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        previous_hash = None
        
        for i, entry in enumerate(self._entries):
            # Recompute hash
            expected_hash = entry.compute_hash(previous_hash)
            
            if entry.entry_hash != expected_hash:
                errors.append(f"Entry {i} ({entry.id}): Hash mismatch")
            
            if entry.previous_hash != previous_hash:
                errors.append(f"Entry {i} ({entry.id}): Previous hash mismatch")
            
            previous_hash = entry.entry_hash
        
        return len(errors) == 0, errors
    
    def export(
        self,
        format: str = "json",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> str:
        """Export audit log entries.
        
        Args:
            format: Export format (json, csv)
            start_date: Filter entries after this date
            end_date: Filter entries before this date
        
        Returns:
            Exported audit log as string
        """
        entries = self._entries
        
        if start_date:
            entries = [e for e in entries if e.timestamp >= start_date]
        if end_date:
            entries = [e for e in entries if e.timestamp <= end_date]
        
        if format == "json":
            return json.dumps([e.to_dict() for e in entries], indent=2)
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if entries:
                writer = csv.DictWriter(output, fieldnames=entries[0].to_dict().keys())
                writer.writeheader()
                for entry in entries:
                    writer.writerow(entry.to_dict())
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        from complianceagent.config import get_config
        
        config = get_config()
        _audit_logger = AuditLogger(
            service_name="default",
            output_file=config.audit.log_file_path if config.audit.log_to_file else None,
            log_to_stdout=config.audit.log_to_stdout,
            api_endpoint=config.audit.audit_service_url,
            api_key=config.audit.audit_service_api_key,
        )
    return _audit_logger


def set_audit_logger(logger: AuditLogger) -> None:
    """Set the global audit logger instance."""
    global _audit_logger
    _audit_logger = logger
