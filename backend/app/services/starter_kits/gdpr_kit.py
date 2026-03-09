"""GDPR starter kit definition."""

from app.services.starter_kits.models import (
    CodeTemplate,
    ConfigTemplate,
    DocumentTemplate,
    StarterKit,
    TemplateCategory,
    TemplateLanguage,
)


def create_gdpr_kit() -> StarterKit:
    """Create GDPR starter kit."""
    kit = StarterKit(
        name="GDPR Compliance Starter Kit",
        description="Comprehensive code templates and configurations for GDPR compliance",
        framework="GDPR",
        version="2.0.0",
        requirements_covered=[
            "Article 5 - Data Processing Principles",
            "Article 6 - Lawful Basis",
            "Article 7 - Consent Management",
            "Article 17 - Right to Erasure",
            "Article 20 - Data Portability",
            "Article 25 - Privacy by Design",
            "Article 32 - Security of Processing",
            "Article 33 - Breach Notification",
        ],
        supported_languages=[
            TemplateLanguage.PYTHON,
            TemplateLanguage.TYPESCRIPT,
            TemplateLanguage.JAVA,
        ],
        prerequisites=[
            "Python 3.9+ or Node.js 18+",
            "PostgreSQL or compatible database",
            "Redis (optional, for caching)",
        ],
        quick_start="""
1. Extract the archive to your project
2. Install dependencies: `pip install -r requirements.txt`
3. Configure your database in `config/database.yaml`
4. Run migrations: `python manage.py migrate`
5. Start using the compliance modules in your code
""",
    )

    # Add code templates
    kit.code_templates = [
        CodeTemplate(
            name="Consent Manager",
            description="GDPR-compliant consent management system",
            language=TemplateLanguage.PYTHON,
            category=TemplateCategory.CONSENT,
            file_name="consent_manager.py",
            content=_gdpr_consent_template(),
            frameworks=["GDPR"],
            requirement_ids=["Art7"],
        ),
        CodeTemplate(
            name="Data Subject Rights Handler",
            description="Handle DSAR (Data Subject Access Requests)",
            language=TemplateLanguage.PYTHON,
            category=TemplateCategory.DATA_PROTECTION,
            file_name="dsar_handler.py",
            content=_gdpr_dsar_template(),
            frameworks=["GDPR"],
            requirement_ids=["Art15", "Art17", "Art20"],
        ),
        CodeTemplate(
            name="Personal Data Encryption",
            description="Encrypt personal data at rest and in transit",
            language=TemplateLanguage.PYTHON,
            category=TemplateCategory.ENCRYPTION,
            file_name="data_encryption.py",
            content=_encryption_template(),
            frameworks=["GDPR"],
            requirement_ids=["Art32"],
        ),
        CodeTemplate(
            name="Audit Logger",
            description="GDPR-compliant audit logging",
            language=TemplateLanguage.PYTHON,
            category=TemplateCategory.AUDIT,
            file_name="audit_logger.py",
            content=_audit_logger_template(),
            frameworks=["GDPR"],
            requirement_ids=["Art30"],
        ),
    ]

    # Add config templates
    kit.config_templates = [
        ConfigTemplate(
            name="Data Retention Policy",
            description="Configure data retention periods",
            file_name="retention_policy.yaml",
            content=_retention_config_template(),
            frameworks=["GDPR"],
        ),
        ConfigTemplate(
            name="Privacy Settings",
            description="Default privacy configuration",
            file_name="privacy_config.yaml",
            content=_privacy_config_template(),
            frameworks=["GDPR"],
        ),
    ]

    # Add document templates
    kit.document_templates = [
        DocumentTemplate(
            name="Privacy Policy Template",
            description="GDPR-compliant privacy policy",
            content=_privacy_policy_template(),
            document_type="policy",
            frameworks=["GDPR"],
        ),
        DocumentTemplate(
            name="Data Processing Agreement",
            description="Template for DPA with processors",
            content=_dpa_template(),
            document_type="agreement",
            frameworks=["GDPR"],
        ),
    ]

    return kit


def _gdpr_consent_template() -> str:
    return '''"""
GDPR-Compliant Consent Management System

This module provides functionality for managing user consent in accordance with
GDPR Article 7 requirements for valid consent.
"""

from datetime import datetime, UTC
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field
from uuid import UUID, uuid4


class ConsentPurpose(str, Enum):
"""Consent purposes as per GDPR."""
MARKETING = "marketing"
ANALYTICS = "analytics"
PERSONALIZATION = "personalization"
THIRD_PARTY_SHARING = "third_party_sharing"
ESSENTIAL = "essential"


class ConsentStatus(str, Enum):
GRANTED = "granted"
DENIED = "denied"
WITHDRAWN = "withdrawn"
PENDING = "pending"


@dataclass
class ConsentRecord:
"""Immutable record of consent given or withdrawn."""
id: UUID = field(default_factory=uuid4)
user_id: str = ""
purpose: ConsentPurpose = ConsentPurpose.ESSENTIAL
status: ConsentStatus = ConsentStatus.PENDING
version: str = "1.0"
ip_address: Optional[str] = None
user_agent: Optional[str] = None
timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
withdrawal_timestamp: Optional[datetime] = None


class ConsentManager:
"""
Manages user consent with full audit trail.

GDPR Requirements Addressed:
- Article 7(1): Demonstrable consent
- Article 7(2): Clear and plain language
- Article 7(3): Easy withdrawal
"""

def __init__(self, storage_backend):
    self.storage = storage_backend
    _consent_cache: dict[str, dict[ConsentPurpose, ConsentRecord]] = {}

async def request_consent(
    self,
    user_id: str,
    purpose: ConsentPurpose,
    consent_text: str,
    version: str = "1.0",
) -> ConsentRecord:
    """
    Request consent from user for a specific purpose.
    
    Args:
        user_id: Unique identifier for the user
        purpose: The purpose for which consent is requested
        consent_text: Clear description of what consent is for
        version: Version of consent text (for tracking changes)
    
    Returns:
        ConsentRecord with pending status
    """
    record = ConsentRecord(
        user_id=user_id,
        purpose=purpose,
        status=ConsentStatus.PENDING,
        version=version,
    )
    
    await self.storage.save_consent_record(record)
    return record

async def record_consent(
    self,
    user_id: str,
    purpose: ConsentPurpose,
    granted: bool,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> ConsentRecord:
    """
    Record user's consent decision with full context.
    
    This creates an immutable audit record of the consent decision.
    """
    record = ConsentRecord(
        user_id=user_id,
        purpose=purpose,
        status=ConsentStatus.GRANTED if granted else ConsentStatus.DENIED,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    await self.storage.save_consent_record(record)
    
    # Update cache
    if user_id not in _consent_cache:
        _consent_cache[user_id] = {}
    _consent_cache[user_id][purpose] = record
    
    return record

async def withdraw_consent(
    self,
    user_id: str,
    purpose: ConsentPurpose,
) -> ConsentRecord:
    """
    Withdraw previously granted consent.
    
    Per GDPR Article 7(3), withdrawal must be as easy as giving consent.
    """
    record = ConsentRecord(
        user_id=user_id,
        purpose=purpose,
        status=ConsentStatus.WITHDRAWN,
        withdrawal_timestamp=datetime.now(UTC),
    )
    
    await self.storage.save_consent_record(record)
    
    # Update cache
    if user_id in _consent_cache:
        _consent_cache[user_id][purpose] = record
    
    return record

async def check_consent(
    self,
    user_id: str,
    purpose: ConsentPurpose,
) -> bool:
    """Check if user has granted consent for a purpose."""
    # Check cache first
    if user_id in _consent_cache:
        if purpose in _consent_cache[user_id]:
            return _consent_cache[user_id][purpose].status == ConsentStatus.GRANTED
    
    # Query storage
    record = await self.storage.get_latest_consent(user_id, purpose)
    if record:
        return record.status == ConsentStatus.GRANTED
    
    return False

async def get_consent_history(
    self,
    user_id: str,
) -> list[ConsentRecord]:
    """Get full consent history for a user (for DSAR compliance)."""
    return await self.storage.get_all_consent_records(user_id)
'''


def _gdpr_dsar_template() -> str:
    return '''"""
Data Subject Access Request (DSAR) Handler

Implements GDPR Articles 15-22 for data subject rights.
"""

from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Any
from uuid import UUID, uuid4


class DSARType(str, Enum):
"""Types of Data Subject Requests."""
ACCESS = "access"  # Article 15
RECTIFICATION = "rectification"  # Article 16
ERASURE = "erasure"  # Article 17 (Right to be forgotten)
RESTRICTION = "restriction"  # Article 18
PORTABILITY = "portability"  # Article 20
OBJECTION = "objection"  # Article 21


class DSARStatus(str, Enum):
RECEIVED = "received"
IDENTITY_VERIFICATION = "identity_verification"
IN_PROGRESS = "in_progress"
COMPLETED = "completed"
REJECTED = "rejected"


@dataclass
class DSAR:
"""Data Subject Access Request."""
id: UUID = field(default_factory=uuid4)
user_id: str = ""
request_type: DSARType = DSARType.ACCESS
status: DSARStatus = DSARStatus.RECEIVED
received_at: datetime = field(default_factory=lambda: datetime.now(UTC))
deadline: datetime = field(default_factory=lambda: datetime.now(UTC) + timedelta(days=30))
completed_at: Optional[datetime] = None
response_data: Optional[dict] = None
notes: str = ""


class DSARHandler:
"""
Handles Data Subject Access Requests.

GDPR Requirements:
- Response within 30 days (extendable to 90 days for complex requests)
- Verify identity before processing
- Provide data in commonly used format
"""

def __init__(self, data_store, notifier):
    self.data_store = data_store
    self.notifier = notifier
    _requests: dict[UUID, DSAR] = {}

async def submit_request(
    self,
    user_id: str,
    request_type: DSARType,
    details: Optional[str] = None,
) -> DSAR:
    """Submit a new DSAR."""
    request = DSAR(
        user_id=user_id,
        request_type=request_type,
        notes=details or "",
    )
    
    _requests[request.id] = request
    
    # Notify compliance team
    await self.notifier.notify_compliance_team(
        f"New DSAR received: {request_type.value} for user {user_id}"
    )
    
    return request

async def verify_identity(
    self,
    request_id: UUID,
    verification_method: str,
    verified: bool,
) -> DSAR:
    """Verify the identity of the requester."""
    request = _requests.get(request_id)
    if not request:
        raise ValueError("Request not found")
    
    if verified:
        request.status = DSARStatus.IN_PROGRESS
    else:
        request.status = DSARStatus.REJECTED
        request.notes += f"\\nIdentity verification failed: {verification_method}"
    
    return request

async def process_access_request(self, request_id: UUID) -> dict:
    """
    Process a data access request (Article 15).
    
    Returns all personal data held about the subject.
    """
    request = _requests.get(request_id)
    if not request or request.request_type != DSARType.ACCESS:
        raise ValueError("Invalid request")
    
    # Collect all personal data
    data = await self.data_store.get_all_user_data(request.user_id)
    
    request.response_data = data
    request.status = DSARStatus.COMPLETED
    request.completed_at = datetime.now(UTC)
    
    return data

async def process_erasure_request(self, request_id: UUID) -> bool:
    """
    Process a right to erasure request (Article 17).
    
    Deletes all personal data unless legal retention required.
    """
    request = _requests.get(request_id)
    if not request or request.request_type != DSARType.ERASURE:
        raise ValueError("Invalid request")
    
    # Check for legal retention requirements
    retention_required = await self.data_store.check_retention_requirements(
        request.user_id
    )
    
    if retention_required:
        request.status = DSARStatus.REJECTED
        request.notes += "\\nData retention required for legal compliance"
        return False
    
    # Delete all personal data
    await self.data_store.delete_user_data(request.user_id)
    
    request.status = DSARStatus.COMPLETED
    request.completed_at = datetime.now(UTC)
    
    return True

async def process_portability_request(self, request_id: UUID) -> bytes:
    """
    Process a data portability request (Article 20).
    
    Returns data in machine-readable format (JSON).
    """
    request = _requests.get(request_id)
    if not request or request.request_type != DSARType.PORTABILITY:
        raise ValueError("Invalid request")
    
    # Get data in portable format
    data = await self.data_store.export_user_data_portable(request.user_id)
    
    request.status = DSARStatus.COMPLETED
    request.completed_at = datetime.now(UTC)
    
    return data
'''


def _encryption_template() -> str:
    return '''"""
Personal Data Encryption Service

Implements encryption for personal data as required by GDPR Article 32.
"""

import base64
import hashlib
import secrets
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class PersonalDataEncryption:
"""
Encrypts personal data at rest.

Uses AES-256 encryption via Fernet (symmetric encryption).
"""

def __init__(self, master_key: bytes):
    """
    Initialize with a master key.
    
    Args:
        master_key: 32-byte key for encryption
    """
    _master_key = master_key
    _fernet = _create_fernet(master_key)

def _create_fernet(self, key: bytes) -> Fernet:
    """Create Fernet instance from key."""
    # Derive a key using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"compliance_salt",  # In production, use unique salt
        iterations=100000,
    )
    derived_key = base64.urlsafe_b64encode(kdf.derive(key))
    return Fernet(derived_key)

def encrypt(self, plaintext: str) -> str:
    """
    Encrypt personal data.
    
    Args:
        plaintext: The data to encrypt
        
    Returns:
        Base64-encoded encrypted data
    """
    encrypted = _fernet.encrypt(plaintext.encode())
    return base64.urlsafe_b64encode(encrypted).decode()

def decrypt(self, ciphertext: str) -> str:
    """
    Decrypt personal data.
    
    Args:
        ciphertext: Base64-encoded encrypted data
        
    Returns:
        Decrypted plaintext
    """
    encrypted = base64.urlsafe_b64decode(ciphertext.encode())
    decrypted = _fernet.decrypt(encrypted)
    return decrypted.decode()

def hash_for_search(self, value: str) -> str:
    """
    Create searchable hash of value.
    
    Allows searching encrypted fields without decryption.
    """
    return hashlib.sha256(
        (value + "search_pepper").encode()
    ).hexdigest()

@staticmethod
def generate_key() -> bytes:
    """Generate a secure random key."""
    return secrets.token_bytes(32)
'''


def _audit_logger_template() -> str:
    return '''"""
Compliance Audit Logger

Provides immutable audit logging for compliance requirements.
"""

import json
import hashlib
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from uuid import UUID, uuid4
from enum import Enum


class AuditAction(str, Enum):
"""Types of auditable actions."""
CREATE = "create"
READ = "read"
UPDATE = "update"
DELETE = "delete"
LOGIN = "login"
LOGOUT = "logout"
EXPORT = "export"
CONSENT_CHANGE = "consent_change"
ACCESS_DENIED = "access_denied"


@dataclass
class AuditEntry:
"""Immutable audit log entry."""
id: UUID = field(default_factory=uuid4)
timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
user_id: str = ""
action: AuditAction = AuditAction.READ
resource_type: str = ""
resource_id: str = ""
ip_address: Optional[str] = None
user_agent: Optional[str] = None
details: dict = field(default_factory=dict)
previous_hash: Optional[str] = None
entry_hash: str = ""

def __post_init__():
    """Calculate hash after initialization."""
    if not self.entry_hash:
        self.entry_hash = _calculate_hash()

def _calculate_hash() -> str:
    """Calculate tamper-evident hash."""
    data = f"{self.timestamp.isoformat()}{self.user_id}{self.action.value}"
    data += f"{self.resource_type}{self.resource_id}{json.dumps(self.details)}"
    data += self.previous_hash or ""
    return hashlib.sha256(data.encode()).hexdigest()


class AuditLogger:
"""
Tamper-evident audit logging system.

Features:
- Immutable entries with cryptographic chaining
- Searchable by user, action, resource
- Exportable for compliance audits
"""

def __init__(self, storage_backend):
    self.storage = storage_backend
    _last_hash: Optional[str] = None

async def log(
    self,
    user_id: str,
    action: AuditAction,
    resource_type: str,
    resource_id: str,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditEntry:
    """
    Log an auditable action.
    
    Creates an immutable, chained audit entry.
    """
    entry = AuditEntry(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
        previous_hash=_last_hash,
    )
    
    await self.storage.save_audit_entry(entry)
    _last_hash = entry.entry_hash
    
    return entry

async def verify_chain(self) -> bool:
    """Verify the integrity of the audit chain."""
    entries = await self.storage.get_all_entries()
    
    previous_hash = None
    for entry in entries:
        if entry.previous_hash != previous_hash:
            return False
        
        calculated = entry._calculate_hash()
        if entry.entry_hash != calculated:
            return False
        
        previous_hash = entry.entry_hash
    
    return True

async def export_for_audit(
    self,
    start_date: datetime,
    end_date: datetime,
) -> list[dict]:
    """Export audit entries for compliance review."""
    entries = await self.storage.get_entries_by_date_range(start_date, end_date)
    return [asdict(e) for e in entries]
'''


def _retention_config_template() -> str:
    return """# Data Retention Policy Configuration
# GDPR Article 5(1)(e) - Storage Limitation

retention_policies:
  # User account data
  user_accounts:
active_users: "indefinite"
inactive_users: "2 years after last activity"
deleted_accounts: "30 days"

  # Transaction data
  transactions:
financial_records: "7 years"  # Legal requirement
purchase_history: "3 years"

  # Logs and analytics
  logs:
security_logs: "1 year"
access_logs: "90 days"
analytics_data: "26 months"

  # Marketing data
  marketing:
email_preferences: "until consent withdrawn"
campaign_responses: "2 years"

  # Support data
  support:
tickets: "3 years"
chat_transcripts: "1 year"

# Automated deletion settings
auto_deletion:
  enabled: true
  schedule: "0 2 * * *"  # Daily at 2 AM
  dry_run: false
  notification_email: "privacy@{{ company_domain }}"

# Data anonymization settings
anonymization:
  enabled: true
  fields:
- email
- name
- ip_address
  method: "pseudonymization"
"""


def _privacy_config_template() -> str:
    return """# Privacy Configuration
# GDPR Privacy by Design Settings

privacy:
  default_consent: false

  purposes:
essential:
  required: true
  description: "Necessary for service operation"

analytics:
  required: false
  default: false
  description: "Usage analytics to improve service"

marketing:
  required: false
  default: false
  description: "Marketing communications"

personalization:
  required: false
  default: false
  description: "Personalized experience"

data_minimization:
  enabled: true
  collect_only_necessary: true

encryption:
  at_rest: true
  in_transit: true
  algorithm: "AES-256-GCM"

access_control:
  default_deny: true
  require_purpose: true
  audit_access: true
"""


def _privacy_policy_template() -> str:
    return """# Privacy Policy

**Last Updated:** {{ effective_date }}

## Introduction

{{ company_name }} ("we", "us", "our") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information.

## Data Controller

**{{ company_name }}**
{{ company_address }}
Email: privacy@{{ company_domain }}

## Information We Collect

### Information You Provide
- Account information (name, email, password)
- Profile information
- Communications with us

### Automatically Collected Information
- Device information
- Usage data
- Cookies and similar technologies

## Legal Basis for Processing

We process your data based on:
- **Consent** - Where you have given explicit consent
- **Contract** - To fulfill our contractual obligations
- **Legal Obligation** - To comply with applicable laws
- **Legitimate Interests** - For our legitimate business purposes

## Your Rights

Under GDPR, you have the right to:
- **Access** your personal data
- **Rectification** of inaccurate data
- **Erasure** ("right to be forgotten")
- **Restrict** processing
- **Data Portability**
- **Object** to processing
- **Withdraw Consent** at any time

To exercise these rights, contact: privacy@{{ company_domain }}

## Data Retention

We retain your data only as long as necessary for the purposes outlined in this policy or as required by law.

## International Transfers

If we transfer data outside the EEA, we ensure appropriate safeguards are in place.

## Contact Us

For privacy inquiries: privacy@{{ company_domain }}
"""


def _dpa_template() -> str:
    return """# Data Processing Agreement

This Data Processing Agreement ("DPA") is entered into between:

**Data Controller:** {{ controller_name }}
**Data Processor:** {{ processor_name }}

## 1. Subject Matter

This DPA governs the processing of personal data by the Processor on behalf of the Controller.

## 2. Duration

This DPA remains in effect for the duration of the main service agreement.

## 3. Nature and Purpose

The Processor will process personal data solely for the purposes of providing the services described in the main agreement.

## 4. Types of Personal Data

- User account information
- Usage data
- [Add specific data types]

## 5. Categories of Data Subjects

- Customers
- End users
- [Add specific categories]

## 6. Processor Obligations

The Processor shall:
- Process data only on documented instructions
- Ensure personnel confidentiality
- Implement appropriate security measures
- Assist with data subject requests
- Delete or return data upon termination
- Allow and contribute to audits

## 7. Sub-processors

The Processor may engage sub-processors with prior written consent.

## 8. Security Measures

The Processor implements:
- Encryption of personal data
- Access controls
- Regular security testing
- Incident response procedures

## 9. Breach Notification

The Processor shall notify the Controller within 72 hours of becoming aware of a personal data breach.

## 10. Signatures

Controller: ___________________ Date: ___________
Processor: ___________________ Date: ___________
"""
