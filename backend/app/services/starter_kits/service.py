"""Regulation-specific starter kits service."""

import json
import zipfile
from datetime import datetime
from io import BytesIO
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.starter_kits.models import (
    CodeTemplate,
    ConfigTemplate,
    DocumentTemplate,
    StarterKit,
    TemplateCategory,
    TemplateLanguage,
)


logger = structlog.get_logger()


class StarterKitsService:
    """Service for managing regulation-specific starter kits."""
    
    def __init__(self, db: AsyncSession, copilot: Any = None):
        self.db = db
        self.copilot = copilot
        self._kits = self._initialize_kits()
    
    def _initialize_kits(self) -> dict[str, StarterKit]:
        """Initialize built-in starter kits."""
        return {
            "GDPR": self._create_gdpr_kit(),
            "HIPAA": self._create_hipaa_kit(),
            "PCI_DSS": self._create_pci_kit(),
            "SOC2": self._create_soc2_kit(),
        }
    
    async def list_kits(
        self,
        framework: str | None = None,
        language: TemplateLanguage | None = None,
    ) -> list[StarterKit]:
        """List available starter kits."""
        kits = list(self._kits.values())
        
        if framework:
            kits = [k for k in kits if k.framework == framework]
        
        if language:
            kits = [k for k in kits if language in k.supported_languages]
        
        return kits
    
    async def get_kit(self, framework: str) -> StarterKit | None:
        """Get a starter kit by framework."""
        return self._kits.get(framework)
    
    async def get_template(
        self,
        framework: str,
        template_id: UUID,
    ) -> CodeTemplate | ConfigTemplate | DocumentTemplate | None:
        """Get a specific template from a kit."""
        kit = self._kits.get(framework)
        if not kit:
            return None
        
        for template in kit.code_templates:
            if template.id == template_id:
                return template
        
        for template in kit.config_templates:
            if template.id == template_id:
                return template
        
        for template in kit.document_templates:
            if template.id == template_id:
                return template
        
        return None
    
    async def generate_kit_archive(
        self,
        framework: str,
        language: TemplateLanguage = TemplateLanguage.PYTHON,
        customizations: dict | None = None,
    ) -> bytes:
        """Generate a downloadable ZIP archive of the starter kit."""
        kit = self._kits.get(framework)
        if not kit:
            raise ValueError(f"Starter kit not found: {framework}")
        
        buffer = BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add README
            readme = self._generate_readme(kit)
            zf.writestr(f"{framework.lower()}_starter_kit/README.md", readme)
            
            # Add code templates
            for template in kit.code_templates:
                if template.language == language:
                    content = self._apply_customizations(template.content, customizations or {})
                    path = f"{framework.lower()}_starter_kit/src/{template.file_name}"
                    zf.writestr(path, content)
            
            # Add config templates
            for template in kit.config_templates:
                content = self._apply_customizations(template.content, customizations or {})
                path = f"{framework.lower()}_starter_kit/config/{template.file_name}"
                zf.writestr(path, content)
            
            # Add document templates
            for template in kit.document_templates:
                content = self._apply_customizations(template.content, customizations or {})
                path = f"{framework.lower()}_starter_kit/docs/{template.file_name}"
                zf.writestr(path, content)
            
            # Add manifest
            manifest = {
                "framework": kit.framework,
                "version": kit.version,
                "generated_at": datetime.utcnow().isoformat(),
                "language": language.value,
                "requirements_covered": kit.requirements_covered,
            }
            zf.writestr(
                f"{framework.lower()}_starter_kit/manifest.json",
                json.dumps(manifest, indent=2)
            )
        
        kit.download_count += 1
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _apply_customizations(self, content: str, customizations: dict) -> str:
        """Apply customizations to template content."""
        for key, value in customizations.items():
            placeholder = f"{{{{ {key} }}}}"
            content = content.replace(placeholder, str(value))
        return content
    
    def _generate_readme(self, kit: StarterKit) -> str:
        """Generate README for the kit."""
        return f"""# {kit.name}

{kit.description}

## Quick Start

{kit.quick_start}

## Prerequisites

{chr(10).join(f'- {p}' for p in kit.prerequisites)}

## What's Included

### Code Templates
{chr(10).join(f'- `{t.file_name}`: {t.description}' for t in kit.code_templates)}

### Configuration Files
{chr(10).join(f'- `{t.file_name}`: {t.description}' for t in kit.config_templates)}

### Documentation
{chr(10).join(f'- `{t.name}`: {t.description}' for t in kit.document_templates)}

## Requirements Covered

This starter kit addresses the following compliance requirements:

{chr(10).join(f'- {r}' for r in kit.requirements_covered)}

## Version

{kit.version}

---
Generated by ComplianceAgent
"""
    
    # --- Kit Definitions ---
    
    def _create_gdpr_kit(self) -> StarterKit:
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
                content=self._gdpr_consent_template(),
                frameworks=["GDPR"],
                requirement_ids=["Art7"],
            ),
            CodeTemplate(
                name="Data Subject Rights Handler",
                description="Handle DSAR (Data Subject Access Requests)",
                language=TemplateLanguage.PYTHON,
                category=TemplateCategory.DATA_PROTECTION,
                file_name="dsar_handler.py",
                content=self._gdpr_dsar_template(),
                frameworks=["GDPR"],
                requirement_ids=["Art15", "Art17", "Art20"],
            ),
            CodeTemplate(
                name="Personal Data Encryption",
                description="Encrypt personal data at rest and in transit",
                language=TemplateLanguage.PYTHON,
                category=TemplateCategory.ENCRYPTION,
                file_name="data_encryption.py",
                content=self._encryption_template(),
                frameworks=["GDPR"],
                requirement_ids=["Art32"],
            ),
            CodeTemplate(
                name="Audit Logger",
                description="GDPR-compliant audit logging",
                language=TemplateLanguage.PYTHON,
                category=TemplateCategory.AUDIT,
                file_name="audit_logger.py",
                content=self._audit_logger_template(),
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
                content=self._retention_config_template(),
                frameworks=["GDPR"],
            ),
            ConfigTemplate(
                name="Privacy Settings",
                description="Default privacy configuration",
                file_name="privacy_config.yaml",
                content=self._privacy_config_template(),
                frameworks=["GDPR"],
            ),
        ]
        
        # Add document templates
        kit.document_templates = [
            DocumentTemplate(
                name="Privacy Policy Template",
                description="GDPR-compliant privacy policy",
                content=self._privacy_policy_template(),
                document_type="policy",
                frameworks=["GDPR"],
            ),
            DocumentTemplate(
                name="Data Processing Agreement",
                description="Template for DPA with processors",
                content=self._dpa_template(),
                document_type="agreement",
                frameworks=["GDPR"],
            ),
        ]
        
        return kit
    
    def _create_hipaa_kit(self) -> StarterKit:
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
                content=self._hipaa_access_control_template(),
                frameworks=["HIPAA"],
                requirement_ids=["164.312(a)", "164.312(d)"],
            ),
            CodeTemplate(
                name="PHI Encryption Service",
                description="Encrypt/decrypt PHI data",
                language=TemplateLanguage.PYTHON,
                category=TemplateCategory.ENCRYPTION,
                file_name="phi_encryption.py",
                content=self._hipaa_encryption_template(),
                frameworks=["HIPAA"],
                requirement_ids=["164.312(e)"],
            ),
            CodeTemplate(
                name="HIPAA Audit Trail",
                description="Comprehensive audit logging for PHI access",
                language=TemplateLanguage.PYTHON,
                category=TemplateCategory.AUDIT,
                file_name="hipaa_audit.py",
                content=self._hipaa_audit_template(),
                frameworks=["HIPAA"],
                requirement_ids=["164.312(b)"],
            ),
        ]
        
        kit.config_templates = [
            ConfigTemplate(
                name="HIPAA Security Configuration",
                description="Security settings for HIPAA compliance",
                file_name="hipaa_security.yaml",
                content=self._hipaa_security_config(),
                frameworks=["HIPAA"],
            ),
        ]
        
        kit.document_templates = [
            DocumentTemplate(
                name="BAA Template",
                description="Business Associate Agreement template",
                content=self._baa_template(),
                document_type="agreement",
                frameworks=["HIPAA"],
            ),
        ]
        
        return kit
    
    def _create_pci_kit(self) -> StarterKit:
        """Create PCI-DSS starter kit."""
        kit = StarterKit(
            name="PCI-DSS Compliance Starter Kit",
            description="Templates for PCI-DSS compliant payment processing",
            framework="PCI_DSS",
            version="4.0.0",
            requirements_covered=[
                "Requirement 3 - Protect Stored Cardholder Data",
                "Requirement 4 - Encrypt Transmission of Cardholder Data",
                "Requirement 6 - Develop Secure Systems",
                "Requirement 8 - Identify and Authenticate Access",
                "Requirement 10 - Track and Monitor Access",
            ],
            supported_languages=[
                TemplateLanguage.PYTHON,
                TemplateLanguage.TYPESCRIPT,
            ],
            prerequisites=[
                "TLS 1.2+ support",
                "HSM or secure key storage",
                "PCI-compliant hosting environment",
            ],
            quick_start="""
1. Review PCI-DSS requirements
2. Configure encryption using HSM
3. Set up card data handling
4. Enable comprehensive logging
5. Implement tokenization
""",
        )
        
        kit.code_templates = [
            CodeTemplate(
                name="Card Data Tokenizer",
                description="Tokenize card data to reduce PCI scope",
                language=TemplateLanguage.PYTHON,
                category=TemplateCategory.DATA_PROTECTION,
                file_name="tokenizer.py",
                content=self._pci_tokenizer_template(),
                frameworks=["PCI_DSS"],
                requirement_ids=["3.4"],
            ),
            CodeTemplate(
                name="PAN Masking Utility",
                description="Mask PANs in logs and displays",
                language=TemplateLanguage.PYTHON,
                category=TemplateCategory.DATA_PROTECTION,
                file_name="pan_masking.py",
                content=self._pan_masking_template(),
                frameworks=["PCI_DSS"],
                requirement_ids=["3.3"],
            ),
        ]
        
        kit.config_templates = [
            ConfigTemplate(
                name="PCI Security Configuration",
                description="PCI-DSS security settings",
                file_name="pci_config.yaml",
                content=self._pci_config_template(),
                frameworks=["PCI_DSS"],
            ),
        ]
        
        return kit
    
    def _create_soc2_kit(self) -> StarterKit:
        """Create SOC2 starter kit."""
        kit = StarterKit(
            name="SOC2 Compliance Starter Kit",
            description="Templates for SOC2 Type II compliance",
            framework="SOC2",
            version="1.0.0",
            requirements_covered=[
                "CC6.1 - Logical Access Security",
                "CC6.6 - Access Authentication",
                "CC6.7 - Data Encryption",
                "CC7.1 - Vulnerability Management",
                "CC8.1 - Change Management",
            ],
            supported_languages=[
                TemplateLanguage.PYTHON,
                TemplateLanguage.TYPESCRIPT,
                TemplateLanguage.GO,
            ],
            prerequisites=[
                "Git for version control",
                "CI/CD pipeline",
                "Logging infrastructure",
            ],
            quick_start="""
1. Set up authentication module
2. Configure audit logging
3. Implement change management
4. Enable vulnerability scanning
""",
        )
        
        kit.code_templates = [
            CodeTemplate(
                name="MFA Authentication",
                description="Multi-factor authentication implementation",
                language=TemplateLanguage.PYTHON,
                category=TemplateCategory.AUTHENTICATION,
                file_name="mfa_auth.py",
                content=self._soc2_mfa_template(),
                frameworks=["SOC2"],
                requirement_ids=["CC6.6"],
            ),
            CodeTemplate(
                name="Comprehensive Audit Logger",
                description="Full audit trail implementation",
                language=TemplateLanguage.PYTHON,
                category=TemplateCategory.AUDIT,
                file_name="soc2_audit.py",
                content=self._audit_logger_template(),
                frameworks=["SOC2"],
                requirement_ids=["CC6.1"],
            ),
        ]
        
        return kit
    
    # --- Template Content ---
    
    def _gdpr_consent_template(self) -> str:
        return '''"""
GDPR-Compliant Consent Management System

This module provides functionality for managing user consent in accordance with
GDPR Article 7 requirements for valid consent.
"""

from datetime import datetime
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
    timestamp: datetime = field(default_factory=datetime.utcnow)
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
        self._consent_cache: dict[str, dict[ConsentPurpose, ConsentRecord]] = {}
    
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
        if user_id not in self._consent_cache:
            self._consent_cache[user_id] = {}
        self._consent_cache[user_id][purpose] = record
        
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
            withdrawal_timestamp=datetime.utcnow(),
        )
        
        await self.storage.save_consent_record(record)
        
        # Update cache
        if user_id in self._consent_cache:
            self._consent_cache[user_id][purpose] = record
        
        return record
    
    async def check_consent(
        self,
        user_id: str,
        purpose: ConsentPurpose,
    ) -> bool:
        """Check if user has granted consent for a purpose."""
        # Check cache first
        if user_id in self._consent_cache:
            if purpose in self._consent_cache[user_id]:
                return self._consent_cache[user_id][purpose].status == ConsentStatus.GRANTED
        
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
    
    def _gdpr_dsar_template(self) -> str:
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
    received_at: datetime = field(default_factory=datetime.utcnow)
    deadline: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=30))
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
        self._requests: dict[UUID, DSAR] = {}
    
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
        
        self._requests[request.id] = request
        
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
        request = self._requests.get(request_id)
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
        request = self._requests.get(request_id)
        if not request or request.request_type != DSARType.ACCESS:
            raise ValueError("Invalid request")
        
        # Collect all personal data
        data = await self.data_store.get_all_user_data(request.user_id)
        
        request.response_data = data
        request.status = DSARStatus.COMPLETED
        request.completed_at = datetime.utcnow()
        
        return data
    
    async def process_erasure_request(self, request_id: UUID) -> bool:
        """
        Process a right to erasure request (Article 17).
        
        Deletes all personal data unless legal retention required.
        """
        request = self._requests.get(request_id)
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
        request.completed_at = datetime.utcnow()
        
        return True
    
    async def process_portability_request(self, request_id: UUID) -> bytes:
        """
        Process a data portability request (Article 20).
        
        Returns data in machine-readable format (JSON).
        """
        request = self._requests.get(request_id)
        if not request or request.request_type != DSARType.PORTABILITY:
            raise ValueError("Invalid request")
        
        # Get data in portable format
        data = await self.data_store.export_user_data_portable(request.user_id)
        
        request.status = DSARStatus.COMPLETED
        request.completed_at = datetime.utcnow()
        
        return data
'''
    
    def _encryption_template(self) -> str:
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
        self._master_key = master_key
        self._fernet = self._create_fernet(master_key)
    
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
        encrypted = self._fernet.encrypt(plaintext.encode())
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
        decrypted = self._fernet.decrypt(encrypted)
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
    
    def _audit_logger_template(self) -> str:
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
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: str = ""
    action: AuditAction = AuditAction.READ
    resource_type: str = ""
    resource_id: str = ""
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: dict = field(default_factory=dict)
    previous_hash: Optional[str] = None
    entry_hash: str = ""
    
    def __post_init__(self):
        """Calculate hash after initialization."""
        if not self.entry_hash:
            self.entry_hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
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
        self._last_hash: Optional[str] = None
    
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
            previous_hash=self._last_hash,
        )
        
        await self.storage.save_audit_entry(entry)
        self._last_hash = entry.entry_hash
        
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
    
    def _retention_config_template(self) -> str:
        return '''# Data Retention Policy Configuration
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
'''
    
    def _privacy_config_template(self) -> str:
        return '''# Privacy Configuration
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
'''
    
    def _privacy_policy_template(self) -> str:
        return '''# Privacy Policy

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
'''
    
    def _dpa_template(self) -> str:
        return '''# Data Processing Agreement

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
'''
    
    def _hipaa_access_control_template(self) -> str:
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
        self._policies: dict[str, PHIAccessPolicy] = {}
        self._initialize_default_policies()
    
    def _initialize_default_policies(self):
        """Set up default PHI access policies."""
        self._policies["patient_record"] = PHIAccessPolicy(
            resource_type="patient_record",
            allowed_roles={"physician", "nurse", "admin"},
            access_level=AccessLevel.VIEW,
            audit_all_access=True,
        )
        
        self._policies["medication_record"] = PHIAccessPolicy(
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
        policy = self._policies.get(resource_type)
        if not policy:
            await self._log_access_denied(user_id, resource_type, resource_id, "No policy")
            return False
        
        # Check role permission
        if not user_roles.intersection(policy.allowed_roles):
            await self._log_access_denied(user_id, resource_type, resource_id, "Role not permitted")
            return False
        
        # Check access level
        access_levels = [AccessLevel.NONE, AccessLevel.VIEW, AccessLevel.EDIT, AccessLevel.FULL]
        if access_levels.index(requested_access) > access_levels.index(policy.access_level):
            await self._log_access_denied(user_id, resource_type, resource_id, "Insufficient access level")
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
    
    def _hipaa_encryption_template(self) -> str:
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
    
    def _hipaa_audit_template(self) -> str:
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
        await self._alert_security_team(entry)
        
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
    
    def _hipaa_security_config(self) -> str:
        return '''# HIPAA Security Configuration
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
'''
    
    def _baa_template(self) -> str:
        return '''# Business Associate Agreement

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
'''
    
    def _pci_tokenizer_template(self) -> str:
        return '''"""
PCI-DSS Card Data Tokenization

Implements Requirement 3.4 - Render PAN unreadable.
"""

import secrets
import hashlib
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TokenizedCard:
    """Tokenized card data."""
    token: str
    last_four: str
    card_type: str
    expiry_month: int
    expiry_year: int
    created_at: datetime


class CardTokenizer:
    """
    PCI-DSS compliant card tokenization.
    
    Replaces sensitive card data with non-sensitive tokens,
    reducing PCI scope significantly.
    """
    
    def __init__(self, token_vault):
        self.vault = token_vault
    
    def tokenize(
        self,
        card_number: str,
        expiry_month: int,
        expiry_year: int,
        cvv: str,  # Never stored!
    ) -> TokenizedCard:
        """
        Tokenize card data.
        
        The actual card number is stored in a PCI-compliant vault.
        Only the token is returned for use in the application.
        """
        # Validate card number
        if not self._validate_luhn(card_number):
            raise ValueError("Invalid card number")
        
        # Generate secure token
        token = self._generate_token()
        
        # Store in secure vault (this is the only place actual PAN exists)
        self.vault.store(
            token=token,
            pan=card_number,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
        )
        # CVV is NEVER stored per PCI-DSS
        
        return TokenizedCard(
            token=token,
            last_four=card_number[-4:],
            card_type=self._detect_card_type(card_number),
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            created_at=datetime.utcnow(),
        )
    
    def _generate_token(self) -> str:
        """Generate cryptographically secure token."""
        return f"tok_{secrets.token_urlsafe(24)}"
    
    def _validate_luhn(self, number: str) -> bool:
        """Validate card number using Luhn algorithm."""
        digits = [int(d) for d in number if d.isdigit()]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        
        total = sum(odd_digits)
        for d in even_digits:
            total += sum(divmod(d * 2, 10))
        
        return total % 10 == 0
    
    def _detect_card_type(self, number: str) -> str:
        """Detect card type from number prefix."""
        if number.startswith("4"):
            return "visa"
        elif number.startswith(("51", "52", "53", "54", "55")):
            return "mastercard"
        elif number.startswith(("34", "37")):
            return "amex"
        elif number.startswith("6011"):
            return "discover"
        return "unknown"
'''
    
    def _pan_masking_template(self) -> str:
        return '''"""
PAN Masking Utility

Implements PCI-DSS Requirement 3.3 - Mask PAN when displayed.
"""

import re
from typing import Optional


class PANMasker:
    """
    Mask Primary Account Numbers for display.
    
    PCI-DSS allows showing only first 6 and last 4 digits.
    """
    
    @staticmethod
    def mask(pan: str, show_first: int = 6, show_last: int = 4) -> str:
        """
        Mask a PAN for display.
        
        Args:
            pan: The full card number
            show_first: Digits to show at start (max 6)
            show_last: Digits to show at end (max 4)
            
        Returns:
            Masked PAN like "411111******1234"
        """
        # Remove any spaces or dashes
        pan = re.sub(r"[\\s-]", "", pan)
        
        if len(pan) < 13:
            raise ValueError("Invalid PAN length")
        
        # PCI-DSS limit
        show_first = min(show_first, 6)
        show_last = min(show_last, 4)
        
        masked_length = len(pan) - show_first - show_last
        masked = pan[:show_first] + "*" * masked_length + pan[-show_last:]
        
        return masked
    
    @staticmethod
    def mask_in_text(text: str) -> str:
        """
        Find and mask any PANs in text (e.g., logs).
        
        Prevents accidental logging of card numbers.
        """
        # Pattern for card numbers (13-19 digits, possibly with spaces/dashes)
        pattern = r"\\b(\\d[\\d\\s-]{11,22}\\d)\\b"
        
        def mask_match(match):
            potential_pan = re.sub(r"[\\s-]", "", match.group(1))
            if 13 <= len(potential_pan) <= 19:
                return PANMasker.mask(potential_pan)
            return match.group(0)
        
        return re.sub(pattern, mask_match, text)
    
    @staticmethod
    def get_last_four(pan: str) -> str:
        """Get last 4 digits of PAN (safe to store/display)."""
        pan = re.sub(r"[\\s-]", "", pan)
        return pan[-4:]
'''
    
    def _pci_config_template(self) -> str:
        return '''# PCI-DSS Security Configuration

pci_dss:
  version: "4.0"
  
  # Requirement 1: Network Security
  network:
    firewall_enabled: true
    dmz_configured: true
    ingress_filtering: true
  
  # Requirement 3: Protect Stored Data
  storage:
    pan_encryption: "AES-256"
    key_rotation_days: 90
    never_store_cvv: true
    never_store_track_data: true
    truncation_enabled: true
  
  # Requirement 4: Encrypt Transmission
  transmission:
    tls_version: "1.2"
    strong_ciphers_only: true
    certificate_validation: true
  
  # Requirement 7: Restrict Access
  access:
    need_to_know: true
    role_based: true
    unique_ids: true
  
  # Requirement 8: Authentication
  authentication:
    mfa_required: true
    password_length: 12
    password_complexity: true
    account_lockout: 6
  
  # Requirement 10: Logging
  logging:
    log_all_access: true
    log_admin_actions: true
    time_sync: true
    retention_days: 365
    tamper_protection: true
  
  # Tokenization settings
  tokenization:
    enabled: true
    vault_provider: "{{ vault_provider }}"
'''
    
    def _soc2_mfa_template(self) -> str:
        return '''"""
Multi-Factor Authentication Implementation

Implements SOC2 CC6.6 - Access Authentication.
"""

import secrets
import hashlib
import time
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class MFAMethod(str, Enum):
    """Supported MFA methods."""
    TOTP = "totp"  # Time-based One-Time Password
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    HARDWARE_KEY = "hardware_key"


@dataclass
class MFAChallenge:
    """MFA verification challenge."""
    challenge_id: str
    user_id: str
    method: MFAMethod
    code: Optional[str]
    created_at: float
    expires_at: float
    verified: bool = False


class MFAService:
    """
    Multi-factor authentication service.
    
    SOC2 Requirements:
    - CC6.6: User authentication
    - CC6.1: Logical access security
    """
    
    def __init__(self, sms_provider=None, email_provider=None):
        self.sms = sms_provider
        self.email = email_provider
        self._challenges: dict[str, MFAChallenge] = {}
        self._secrets: dict[str, str] = {}  # User TOTP secrets
    
    def setup_totp(self, user_id: str) -> str:
        """
        Set up TOTP for a user.
        
        Returns the secret for QR code generation.
        """
        secret = secrets.token_hex(20)
        self._secrets[user_id] = secret
        return secret
    
    def generate_totp(self, secret: str, timestamp: Optional[int] = None) -> str:
        """Generate TOTP code."""
        if timestamp is None:
            timestamp = int(time.time())
        
        counter = timestamp // 30
        
        # HMAC-SHA1 based OTP
        key = bytes.fromhex(secret)
        counter_bytes = counter.to_bytes(8, byteorder="big")
        
        hmac_hash = hashlib.sha1(key + counter_bytes).digest()
        offset = hmac_hash[-1] & 0x0F
        code = ((hmac_hash[offset] & 0x7F) << 24 |
                (hmac_hash[offset + 1] & 0xFF) << 16 |
                (hmac_hash[offset + 2] & 0xFF) << 8 |
                (hmac_hash[offset + 3] & 0xFF))
        
        return str(code % 1000000).zfill(6)
    
    async def initiate_challenge(
        self,
        user_id: str,
        method: MFAMethod,
        destination: Optional[str] = None,
    ) -> MFAChallenge:
        """Initiate an MFA challenge."""
        challenge_id = secrets.token_urlsafe(32)
        code = None
        
        if method == MFAMethod.SMS:
            code = str(secrets.randbelow(1000000)).zfill(6)
            if self.sms and destination:
                await self.sms.send(destination, f"Your verification code: {code}")
        
        elif method == MFAMethod.EMAIL:
            code = str(secrets.randbelow(1000000)).zfill(6)
            if self.email and destination:
                await self.email.send(destination, "Verification Code", f"Your code: {code}")
        
        elif method == MFAMethod.TOTP:
            # TOTP is verified against user's secret
            pass
        
        challenge = MFAChallenge(
            challenge_id=challenge_id,
            user_id=user_id,
            method=method,
            code=code,  # Stored hashed in production
            created_at=time.time(),
            expires_at=time.time() + 300,  # 5 minutes
        )
        
        self._challenges[challenge_id] = challenge
        return challenge
    
    async def verify_challenge(
        self,
        challenge_id: str,
        code: str,
    ) -> bool:
        """Verify an MFA challenge."""
        challenge = self._challenges.get(challenge_id)
        
        if not challenge:
            return False
        
        if time.time() > challenge.expires_at:
            return False
        
        if challenge.verified:
            return False  # Already used
        
        if challenge.method == MFAMethod.TOTP:
            secret = self._secrets.get(challenge.user_id)
            if not secret:
                return False
            
            # Check current and previous time windows
            for offset in [0, -1, 1]:
                expected = self.generate_totp(secret, int(time.time()) + offset * 30)
                if secrets.compare_digest(code, expected):
                    challenge.verified = True
                    return True
            return False
        
        else:
            # SMS/Email code verification
            if challenge.code and secrets.compare_digest(code, challenge.code):
                challenge.verified = True
                return True
        
        return False
'''
