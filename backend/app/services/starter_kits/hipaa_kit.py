"""HIPAA starter kit definition."""

from app.services.starter_kits.models import (
    CodeTemplate,
    ConfigTemplate,
    DocumentTemplate,
    StarterKit,
    TemplateCategory,
    TemplateLanguage,
)


def create_hipaa_kit() -> StarterKit:
    """Create HIPAA starter kit."""
    kit = StarterKit(
        name="HIPAA Compliance Starter Kit",
        description="Code templates for HIPAA-compliant healthcare applications",
        framework="HIPAA",
        version="1.5.0",
        requirements_covered=[
            "164.312(a) - Access Control",
            "164.312(b) - Audit Controls",
            "164.312(c) - Integrity Controls",
            "164.312(d) - Person Authentication",
            "164.312(e) - Transmission Security",
            "164.308(a)(5) - Security Awareness Training",
        ],
        supported_languages=[
            TemplateLanguage.PYTHON,
            TemplateLanguage.JAVA,
        ],
        prerequisites=[
            "Python 3.9+ or Java 17+",
            "PostgreSQL with encryption",
            "TLS certificates",
        ],
        quick_start="""
1. Extract the archive
2. Configure encryption keys in `config/encryption.yaml`
3. Set up access control lists
4. Enable audit logging
5. Review and customize PHI handling code
""",
    )

    kit.code_templates = [
        CodeTemplate(
            name="PHI Access Controller",
            description="Role-based access control for PHI",
            language=TemplateLanguage.PYTHON,
            category=TemplateCategory.ACCESS_CONTROL,
            file_name="phi_access_control.py",
            content=_hipaa_access_control_template(),
            frameworks=["HIPAA"],
            requirement_ids=["164.312(a)", "164.312(d)"],
        ),
        CodeTemplate(
            name="PHI Encryption Service",
            description="Encrypt/decrypt PHI data",
            language=TemplateLanguage.PYTHON,
            category=TemplateCategory.ENCRYPTION,
            file_name="phi_encryption.py",
            content=_hipaa_encryption_template(),
            frameworks=["HIPAA"],
            requirement_ids=["164.312(e)"],
        ),
        CodeTemplate(
            name="HIPAA Audit Trail",
            description="Comprehensive audit logging for PHI access",
            language=TemplateLanguage.PYTHON,
            category=TemplateCategory.AUDIT,
            file_name="hipaa_audit.py",
            content=_hipaa_audit_template(),
            frameworks=["HIPAA"],
            requirement_ids=["164.312(b)"],
        ),
    ]

    kit.config_templates = [
        ConfigTemplate(
            name="HIPAA Security Configuration",
            description="Security settings for HIPAA compliance",
            file_name="hipaa_security.yaml",
            content=_hipaa_security_config(),
            frameworks=["HIPAA"],
        ),
    ]

    kit.document_templates = [
        DocumentTemplate(
            name="BAA Template",
            description="Business Associate Agreement template",
            content=_baa_template(),
            document_type="agreement",
            frameworks=["HIPAA"],
        ),
    ]

    return kit


def _hipaa_access_control_template() -> str:
    return '''"""
HIPAA-Compliant PHI Access Control

Implements 164.312(a) Access Control and 164.312(d) Person Authentication.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Set
from datetime import datetime


class AccessLevel(str, Enum):
"""HIPAA access levels for PHI."""
NONE = "none"
VIEW = "view"
EDIT = "edit"
FULL = "full"


@dataclass
class PHIAccessPolicy:
"""Access policy for PHI resources."""
resource_type: str
allowed_roles: Set[str]
access_level: AccessLevel
requires_break_glass: bool = False
audit_all_access: bool = True


class PHIAccessController:
"""
Role-based access control for Protected Health Information.

HIPAA Requirements:
- 164.312(a)(1): Unique user identification
- 164.312(a)(2)(i): Automatic logoff
- 164.312(a)(2)(ii): Audit controls
- 164.312(d): Person authentication
"""

def __init__(self, audit_logger, session_manager):
    self.audit_logger = audit_logger
    self.session_manager = session_manager
    _policies: dict[str, PHIAccessPolicy] = {}
    _initialize_default_policies()

def _initialize_default_policies():
    """Set up default PHI access policies."""
    _policies["patient_record"] = PHIAccessPolicy(
        resource_type="patient_record",
        allowed_roles={"physician", "nurse", "admin"},
        access_level=AccessLevel.VIEW,
        audit_all_access=True,
    )
    
    _policies["medication_record"] = PHIAccessPolicy(
        resource_type="medication_record",
        allowed_roles={"physician", "pharmacist"},
        access_level=AccessLevel.EDIT,
        audit_all_access=True,
    )

async def check_access(
    self,
    user_id: str,
    user_roles: Set[str],
    resource_type: str,
    resource_id: str,
    requested_access: AccessLevel,
) -> bool:
    """
    Check if user has access to PHI resource.
    
    All access checks are logged for HIPAA compliance.
    """
    policy = _policies.get(resource_type)
    if not policy:
        await _log_access_denied(user_id, resource_type, resource_id, "No policy")
        return False
    
    # Check role permission
    if not user_roles.intersection(policy.allowed_roles):
        await _log_access_denied(user_id, resource_type, resource_id, "Role not permitted")
        return False
    
    # Check access level
    access_levels = [AccessLevel.NONE, AccessLevel.VIEW, AccessLevel.EDIT, AccessLevel.FULL]
    if access_levels.index(requested_access) > access_levels.index(policy.access_level):
        await _log_access_denied(user_id, resource_type, resource_id, "Insufficient access level")
        return False
    
    # Log successful access
    await self.audit_logger.log_phi_access(
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        access_level=requested_access,
        granted=True,
    )
    
    return True

async def _log_access_denied(
    self,
    user_id: str,
    resource_type: str,
    resource_id: str,
    reason: str,
):
    """Log denied access attempt."""
    await self.audit_logger.log_phi_access(
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        access_level=AccessLevel.NONE,
        granted=False,
        denial_reason=reason,
    )

async def break_glass_access(
    self,
    user_id: str,
    resource_id: str,
    reason: str,
) -> bool:
    """
    Emergency access to PHI (break-the-glass).
    
    Used for emergency situations where normal access rules
    would prevent necessary care. All such access is heavily audited.
    """
    await self.audit_logger.log_break_glass(
        user_id=user_id,
        resource_id=resource_id,
        reason=reason,
    )
    
    # Grant temporary elevated access
    return True
'''


def _hipaa_encryption_template() -> str:
    return '''"""
HIPAA PHI Encryption Service

Implements 164.312(e) Transmission Security for ePHI.
"""

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64


class PHIEncryption:
"""
Encryption service for Protected Health Information.

HIPAA Requirements:
- 164.312(a)(2)(iv): Encryption and decryption
- 164.312(e)(1): Transmission security
- 164.312(e)(2)(ii): Encryption
"""

def __init__(self, key_manager):
    self.key_manager = key_manager

def encrypt_phi(self, data: bytes, context: str = "phi") -> bytes:
    """
    Encrypt PHI using AES-256-GCM.
    
    Args:
        data: PHI data to encrypt
        context: Additional context for key derivation
        
    Returns:
        Encrypted data with nonce prepended
    """
    key = self.key_manager.get_encryption_key(context)
    aesgcm = AESGCM(key)
    
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, data, context.encode())
    
    return nonce + ciphertext

def decrypt_phi(self, encrypted_data: bytes, context: str = "phi") -> bytes:
    """
    Decrypt PHI data.
    
    Args:
        encrypted_data: Encrypted data with nonce
        context: Context used during encryption
        
    Returns:
        Decrypted PHI data
    """
    key = self.key_manager.get_encryption_key(context)
    aesgcm = AESGCM(key)
    
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]
    
    return aesgcm.decrypt(nonce, ciphertext, context.encode())

def encrypt_field(self, value: str, field_name: str) -> str:
    """Encrypt a single PHI field."""
    encrypted = self.encrypt_phi(value.encode(), f"field:{field_name}")
    return base64.b64encode(encrypted).decode()

def decrypt_field(self, encrypted_value: str, field_name: str) -> str:
    """Decrypt a single PHI field."""
    encrypted = base64.b64decode(encrypted_value.encode())
    decrypted = self.decrypt_phi(encrypted, f"field:{field_name}")
    return decrypted.decode()
'''


def _hipaa_audit_template() -> str:
    return '''"""
HIPAA Audit Trail Implementation

Implements 164.312(b) Audit Controls.
"""

from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum


class PHIAuditAction(str, Enum):
"""HIPAA-specific audit actions."""
VIEW = "view"
CREATE = "create"
UPDATE = "update"
DELETE = "delete"
PRINT = "print"
FAX = "fax"
EXPORT = "export"
QUERY = "query"
BREAK_GLASS = "break_glass"


@dataclass
class PHIAuditEntry:
"""Audit entry for PHI access."""
id: UUID = field(default_factory=uuid4)
timestamp: datetime = field(default_factory=datetime.utcnow)
user_id: str = ""
patient_id: str = ""
action: PHIAuditAction = PHIAuditAction.VIEW
resource_type: str = ""
resource_id: str = ""
fields_accessed: list[str] = field(default_factory=list)
access_granted: bool = True
denial_reason: Optional[str] = None
ip_address: Optional[str] = None
workstation_id: Optional[str] = None


class HIPAAAuditLogger:
"""
HIPAA-compliant audit logging.

Requirements:
- Log all access to ePHI
- Include user, patient, timestamp, action
- Tamper-evident storage
- Retention per policy (typically 6 years)
"""

def __init__(self, storage):
    self.storage = storage

async def log_phi_access(
    self,
    user_id: str,
    resource_type: str,
    resource_id: str,
    access_level: str,
    granted: bool,
    patient_id: Optional[str] = None,
    fields_accessed: Optional[list[str]] = None,
    denial_reason: Optional[str] = None,
    ip_address: Optional[str] = None,
    workstation_id: Optional[str] = None,
) -> PHIAuditEntry:
    """Log PHI access attempt."""
    entry = PHIAuditEntry(
        user_id=user_id,
        patient_id=patient_id or "",
        action=PHIAuditAction.VIEW,
        resource_type=resource_type,
        resource_id=resource_id,
        fields_accessed=fields_accessed or [],
        access_granted=granted,
        denial_reason=denial_reason,
        ip_address=ip_address,
        workstation_id=workstation_id,
    )
    
    await self.storage.save(entry)
    return entry

async def log_break_glass(
    self,
    user_id: str,
    resource_id: str,
    reason: str,
) -> PHIAuditEntry:
    """Log emergency break-glass access."""
    entry = PHIAuditEntry(
        user_id=user_id,
        action=PHIAuditAction.BREAK_GLASS,
        resource_id=resource_id,
        access_granted=True,
        denial_reason=f"EMERGENCY: {reason}",
    )
    
    await self.storage.save(entry)
    
    # Alert security team
    await _alert_security_team(entry)
    
    return entry

async def _alert_security_team(self, entry: PHIAuditEntry):
    """Alert security team of break-glass access."""
    # Implementation depends on notification system
    pass

async def generate_access_report(
    self,
    patient_id: str,
    start_date: datetime,
    end_date: datetime,
) -> list[PHIAuditEntry]:
    """Generate patient access report for compliance."""
    return await self.storage.query(
        patient_id=patient_id,
        start_date=start_date,
        end_date=end_date,
    )
'''


def _hipaa_security_config() -> str:
    return """# HIPAA Security Configuration
# Based on HIPAA Security Rule Requirements

security:
  # 164.312(a) Access Control
  access_control:
unique_user_ids: true
automatic_logoff_minutes: 15
emergency_access_procedure: true
encryption_required: true

  # 164.312(b) Audit Controls
  audit:
log_all_phi_access: true
log_retention_years: 6
tamper_evident: true
real_time_alerts: true

  # 164.312(c) Integrity
  integrity:
checksum_validation: true
version_control: true

  # 164.312(d) Person Authentication
  authentication:
mfa_required: true
password_complexity: true
session_timeout_minutes: 30
failed_login_lockout: 5

  # 164.312(e) Transmission Security
  transmission:
tls_version: "1.3"
certificate_validation: true
encrypt_all_phi: true

# Minimum necessary standard
minimum_necessary:
  enabled: true
  role_based_access: true
  field_level_access: true
"""


def _baa_template() -> str:
    return """# Business Associate Agreement

This Business Associate Agreement ("Agreement") is entered into by:

**Covered Entity:** {{ covered_entity_name }}
**Business Associate:** {{ business_associate_name }}

## 1. Definitions

Terms used in this Agreement have the meanings set forth in HIPAA.

## 2. Obligations of Business Associate

Business Associate agrees to:

a) Not use or disclose PHI except as permitted by this Agreement
b) Use appropriate safeguards to prevent unauthorized use
c) Report any security incidents
d) Ensure subcontractors agree to same restrictions
e) Make PHI available to individuals upon request
f) Make PHI available for amendment
g) Provide accounting of disclosures
h) Make internal practices available to HHS
i) Return or destroy PHI upon termination

## 3. Permitted Uses and Disclosures

Business Associate may:
- Perform services outlined in the service agreement
- Use PHI for proper management and administration
- Provide data aggregation services

## 4. Obligations of Covered Entity

Covered Entity shall:
- Notify Business Associate of any restrictions
- Notify of changes to Notice of Privacy Practices
- Notify of any revocation of authorization

## 5. Term and Termination

This Agreement terminates when the service agreement terminates or upon material breach.

## 6. Signatures

Covered Entity: ___________________ Date: ___________
Business Associate: ___________________ Date: ___________
"""
