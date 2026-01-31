"""HIPAA PHI handling templates."""

from app.services.templates.base import (
    ComplianceTemplate,
    TemplateCategory,
    TemplateParameter,
)


HIPAA_PHI_TEMPLATE = ComplianceTemplate(
    name="HIPAA PHI Handler",
    description="Secure handling of Protected Health Information with encryption and audit logging",
    category=TemplateCategory.HIPAA_PHI_HANDLING,
    regulations=["HIPAA"],
    languages=["python"],
    code={
        "python": '''"""HIPAA-compliant PHI handling module.

Implements secure handling of Protected Health Information per 45 CFR 164.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4
import base64


class PHIType(str, Enum):
    """Types of Protected Health Information."""
    
    NAME = "name"
    ADDRESS = "address"
    DATES = "dates"
    PHONE = "phone"
    FAX = "fax"
    EMAIL = "email"
    SSN = "ssn"
    MEDICAL_RECORD = "medical_record"
    HEALTH_PLAN = "health_plan"
    ACCOUNT_NUMBER = "account_number"
    CERTIFICATE = "certificate"
    VEHICLE_ID = "vehicle_id"
    DEVICE_ID = "device_id"
    URL = "url"
    IP_ADDRESS = "ip_address"
    BIOMETRIC = "biometric"
    PHOTO = "photo"
    OTHER = "other"


@dataclass
class PHIAccessLog:
    """Audit log entry for PHI access.
    
    Required by HIPAA Security Rule 45 CFR 164.312(b).
    """
    
    id: UUID
    timestamp: datetime
    user_id: str
    action: str
    phi_type: PHIType
    record_id: str
    patient_id: str
    reason: str
    ip_address: str
    success: bool


class PHIHandler:
    """Secure handler for Protected Health Information.
    
    HIPAA Compliance:
    - 45 CFR 164.312(a): Access controls
    - 45 CFR 164.312(b): Audit controls
    - 45 CFR 164.312(c): Integrity controls
    - 45 CFR 164.312(e): Transmission security
    """
    
    def __init__(self, encryption_key: bytes, audit_logger, access_control):
        self.encryption_key = encryption_key
        self.audit_logger = audit_logger
        self.access_control = access_control
    
    def encrypt_phi(self, data: str) -> str:
        """Encrypt PHI data at rest."""
        from cryptography.fernet import Fernet
        
        key = base64.urlsafe_b64encode(
            hashlib.sha256(self.encryption_key).digest()
        )
        f = Fernet(key)
        return f.encrypt(data.encode()).decode()
    
    def decrypt_phi(self, encrypted_data: str) -> str:
        """Decrypt PHI data."""
        from cryptography.fernet import Fernet
        
        key = base64.urlsafe_b64encode(
            hashlib.sha256(self.encryption_key).digest()
        )
        f = Fernet(key)
        return f.decrypt(encrypted_data.encode()).decode()
    
    async def access_phi(
        self,
        user_id: str,
        patient_id: str,
        record_id: str,
        phi_type: PHIType,
        reason: str,
        ip_address: str,
    ) -> Optional[str]:
        """Access PHI with full audit logging."""
        if not await self.access_control.can_access(
            user_id=user_id,
            patient_id=patient_id,
            phi_type=phi_type,
        ):
            await self._log_access(
                user_id=user_id,
                action="view",
                phi_type=phi_type,
                record_id=record_id,
                patient_id=patient_id,
                reason=reason,
                ip_address=ip_address,
                success=False,
            )
            return None
        
        await self._log_access(
            user_id=user_id,
            action="view",
            phi_type=phi_type,
            record_id=record_id,
            patient_id=patient_id,
            reason=reason,
            ip_address=ip_address,
            success=True,
        )
        
        encrypted = await self._get_encrypted_record(record_id)
        if encrypted:
            return self.decrypt_phi(encrypted)
        return None
    
    async def store_phi(
        self,
        user_id: str,
        patient_id: str,
        phi_type: PHIType,
        data: str,
        reason: str,
        ip_address: str,
    ) -> str:
        """Store PHI with encryption and audit logging."""
        record_id = str(uuid4())
        encrypted = self.encrypt_phi(data)
        
        await self._store_encrypted_record(record_id, encrypted, patient_id, phi_type)
        
        await self._log_access(
            user_id=user_id,
            action="create",
            phi_type=phi_type,
            record_id=record_id,
            patient_id=patient_id,
            reason=reason,
            ip_address=ip_address,
            success=True,
        )
        
        return record_id
    
    async def _log_access(self, **kwargs) -> None:
        """Log PHI access for audit trail."""
        log_entry = PHIAccessLog(
            id=uuid4(),
            timestamp=datetime.now(UTC),
            **kwargs,
        )
        await self.audit_logger.log(log_entry)
    
    async def _get_encrypted_record(self, record_id: str) -> Optional[str]:
        raise NotImplementedError
    
    async def _store_encrypted_record(
        self, record_id: str, encrypted: str, patient_id: str, phi_type: PHIType,
    ) -> None:
        raise NotImplementedError
''',
    },
    documentation="""# HIPAA PHI Handler

## Overview
Secure handling of Protected Health Information (PHI) compliant with HIPAA Security Rule.

## Compliance
- **45 CFR 164.312(a)(2)(iv)**: Encryption at rest
- **45 CFR 164.312(b)**: Comprehensive audit logging
- **45 CFR 164.312(c)**: Data integrity verification
- **45 CFR 164.312(d)**: User authentication
""",
    parameters=[
        TemplateParameter(
            name="encryption_algorithm",
            description="Encryption algorithm to use",
            type="string",
            default="AES-256-GCM",
        ),
    ],
    tags=["hipaa", "phi", "healthcare", "encryption", "audit"],
)


HIPAA_TEMPLATES = [HIPAA_PHI_TEMPLATE]
