"""Compliance test fixtures for consistent testing data."""

from datetime import datetime, timezone
from uuid import uuid4

# Sample regulations for testing
SAMPLE_REGULATIONS = [
    {
        "id": str(uuid4()),
        "name": "GDPR - General Data Protection Regulation",
        "description": "European Union regulation on data protection and privacy",
        "source_url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "jurisdiction": "EU",
        "industry": "All",
        "status": "active",
        "version": "2016/679",
        "effective_date": "2018-05-25",
        "full_text": """
REGULATION (EU) 2016/679 OF THE EUROPEAN PARLIAMENT AND OF THE COUNCIL
of 27 April 2016 on the protection of natural persons with regard to the
processing of personal data and on the free movement of such data.

Article 5 - Principles relating to processing of personal data:
1. Personal data shall be:
   (a) processed lawfully, fairly and in a transparent manner;
   (b) collected for specified, explicit and legitimate purposes;
   (c) adequate, relevant and limited to what is necessary;
   (d) accurate and kept up to date;
   (e) kept in a form which permits identification for no longer than necessary;
   (f) processed in a manner that ensures appropriate security.

Article 17 - Right to erasure ('right to be forgotten'):
The data subject shall have the right to obtain from the controller the erasure
of personal data concerning him or her without undue delay.
""",
    },
    {
        "id": str(uuid4()),
        "name": "CCPA - California Consumer Privacy Act",
        "description": "California state law for consumer privacy rights",
        "source_url": "https://oag.ca.gov/privacy/ccpa",
        "jurisdiction": "US-CA",
        "industry": "All",
        "status": "active",
        "version": "2018",
        "effective_date": "2020-01-01",
        "full_text": """
California Consumer Privacy Act of 2018

Section 1798.100 - Consumer Rights:
(a) A consumer shall have the right to request that a business that collects
    a consumer's personal information disclose to that consumer:
    (1) The categories of personal information it has collected.
    (2) The categories of sources from which the personal information is collected.
    (3) The business or commercial purpose for collecting or selling personal information.
    (4) The categories of third parties with whom the business shares personal information.
    (5) The specific pieces of personal information it has collected about that consumer.

Section 1798.105 - Right to Deletion:
(a) A consumer shall have the right to request that a business delete any personal
    information about the consumer which the business has collected from the consumer.
""",
    },
    {
        "id": str(uuid4()),
        "name": "PCI-DSS v4.0",
        "description": "Payment Card Industry Data Security Standard",
        "source_url": "https://www.pcisecuritystandards.org/document_library",
        "jurisdiction": "Global",
        "industry": "Finance",
        "status": "active",
        "version": "4.0",
        "effective_date": "2024-03-31",
        "full_text": """
PCI Data Security Standard v4.0

Requirement 3: Protect Stored Account Data
3.1 Account data storage is kept to a minimum.
3.2 Sensitive authentication data is not stored after authorization.
3.3 Primary account numbers (PAN) are protected wherever stored.
3.4 PAN is rendered unreadable anywhere it is stored using cryptography.
3.5 Cryptographic keys are secured.

Requirement 4: Protect Cardholder Data During Transmission
4.1 Strong cryptography is used during transmission over open, public networks.
4.2 PAN is secured with strong cryptography during transmission.
""",
    },
    {
        "id": str(uuid4()),
        "name": "EU AI Act",
        "description": "European Union Artificial Intelligence Act",
        "source_url": "https://artificialintelligenceact.eu/",
        "jurisdiction": "EU",
        "industry": "Technology",
        "status": "active",
        "version": "2024/1689",
        "effective_date": "2024-08-01",
        "full_text": """
Regulation (EU) 2024/1689 - Artificial Intelligence Act

Article 6 - Classification of High-Risk AI Systems:
1. An AI system shall be considered high-risk if it is intended for use as:
   (a) a safety component of a product covered by Union harmonisation legislation;
   (b) a product covered by Union harmonisation legislation listed in Annex II.

Article 9 - Risk Management System:
1. A risk management system shall be established, implemented, documented and maintained.
2. The risk management system shall be a continuous iterative process.
3. Risk management measures shall give due consideration to effects and interactions.

Article 10 - Data and Data Governance:
1. High-risk AI systems which make use of techniques involving training with data
   shall be developed on the basis of training, validation and testing data sets.
""",
    },
]

# Sample requirements extracted from regulations
SAMPLE_REQUIREMENTS = [
    # GDPR Requirements
    {
        "id": str(uuid4()),
        "title": "Lawful Processing",
        "description": "Personal data must be processed lawfully, fairly and in a transparent manner",
        "obligation_type": "must",
        "priority": "high",
        "section_reference": "Article 5(1)(a)",
        "full_text": "Personal data shall be processed lawfully, fairly and in a transparent manner in relation to the data subject.",
        "technical_controls": ["consent management", "privacy notices", "audit logging"],
        "keywords": ["lawful", "fair", "transparent", "processing"],
    },
    {
        "id": str(uuid4()),
        "title": "Data Minimization",
        "description": "Personal data must be adequate, relevant and limited to what is necessary",
        "obligation_type": "must",
        "priority": "high",
        "section_reference": "Article 5(1)(c)",
        "full_text": "Personal data shall be adequate, relevant and limited to what is necessary in relation to the purposes for which they are processed.",
        "technical_controls": ["data classification", "retention policies", "access controls"],
        "keywords": ["minimization", "adequate", "relevant", "limited", "necessary"],
    },
    {
        "id": str(uuid4()),
        "title": "Right to Erasure",
        "description": "Data subjects have the right to request deletion of their personal data",
        "obligation_type": "must",
        "priority": "high",
        "section_reference": "Article 17",
        "full_text": "The data subject shall have the right to obtain from the controller the erasure of personal data concerning him or her without undue delay.",
        "technical_controls": ["data deletion API", "cascade delete", "audit trail"],
        "keywords": ["erasure", "deletion", "right to be forgotten", "DSAR"],
    },
    # PCI-DSS Requirements
    {
        "id": str(uuid4()),
        "title": "Encrypt PAN at Rest",
        "description": "Primary account numbers must be rendered unreadable using cryptography",
        "obligation_type": "must",
        "priority": "critical",
        "section_reference": "Requirement 3.4",
        "full_text": "PAN is rendered unreadable anywhere it is stored using cryptography.",
        "technical_controls": ["AES-256 encryption", "tokenization", "key management"],
        "keywords": ["encryption", "PAN", "cryptography", "storage"],
    },
    {
        "id": str(uuid4()),
        "title": "Encrypt PAN in Transit",
        "description": "PAN must be secured with strong cryptography during transmission",
        "obligation_type": "must",
        "priority": "critical",
        "section_reference": "Requirement 4.2",
        "full_text": "PAN is secured with strong cryptography during transmission.",
        "technical_controls": ["TLS 1.3", "certificate pinning", "HSTS"],
        "keywords": ["encryption", "transmission", "TLS", "transit"],
    },
    # EU AI Act Requirements
    {
        "id": str(uuid4()),
        "title": "AI Risk Management System",
        "description": "A risk management system must be established for high-risk AI systems",
        "obligation_type": "must",
        "priority": "high",
        "section_reference": "Article 9",
        "full_text": "A risk management system shall be established, implemented, documented and maintained in relation to high-risk AI systems.",
        "technical_controls": ["risk assessment", "documentation", "monitoring", "testing"],
        "keywords": ["risk", "AI", "management", "high-risk"],
    },
]

# Sample code snippets for compliance testing
SAMPLE_CODE_SNIPPETS = {
    "compliant_data_encryption": '''
def save_user_data(user_id: str, personal_data: dict) -> None:
    """Save user data with encryption at rest."""
    # Encrypt sensitive fields before storage
    encrypted_data = encrypt_sensitive_fields(
        data=personal_data,
        fields=["email", "phone", "ssn"],
        algorithm="AES-256-GCM"
    )
    
    # Audit log the operation
    audit_log(
        action="data_save",
        user_id=user_id,
        data_types=list(personal_data.keys())
    )
    
    database.save(user_id, encrypted_data)
''',
    "non_compliant_plain_storage": '''
def save_user_data(user_id: str, personal_data: dict) -> None:
    """Save user data - NON-COMPLIANT: no encryption."""
    # Direct storage without encryption
    database.save(user_id, personal_data)
''',
    "compliant_data_deletion": '''
async def delete_user_data(user_id: str) -> DeleteResult:
    """Handle DSAR deletion request - GDPR Article 17 compliant."""
    # Verify user identity
    verify_user_identity(user_id)
    
    # Log the deletion request for audit
    audit_log(
        action="dsar_deletion_request",
        user_id=user_id,
        timestamp=datetime.utcnow()
    )
    
    # Delete from all data stores
    deleted_count = 0
    for store in get_all_data_stores():
        deleted_count += await store.delete_user_data(user_id)
    
    # Generate deletion certificate
    certificate = generate_deletion_certificate(
        user_id=user_id,
        deleted_records=deleted_count,
        completed_at=datetime.utcnow()
    )
    
    return DeleteResult(
        success=True,
        records_deleted=deleted_count,
        certificate_id=certificate.id
    )
''',
    "non_compliant_partial_deletion": '''
def delete_user(user_id: str) -> bool:
    """Delete user - NON-COMPLIANT: incomplete deletion."""
    # Only deletes main user record, backups retained
    return database.users.delete(user_id)
''',
    "compliant_transmission_encryption": '''
import ssl
import certifi

def create_secure_connection(host: str, port: int) -> ssl.SSLSocket:
    """Create TLS 1.3 encrypted connection - PCI-DSS 4.2 compliant."""
    context = ssl.create_default_context(cafile=certifi.where())
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    
    sock = socket.create_connection((host, port))
    return context.wrap_socket(sock, server_hostname=host)

def send_payment_data(pan: str, cvv: str, endpoint: str) -> Response:
    """Transmit payment data securely."""
    with create_secure_connection(endpoint, 443) as conn:
        # PAN is transmitted over TLS 1.3
        payload = {
            "pan": mask_pan(pan),  # Logging uses masked PAN
            "encrypted_payload": encrypt_for_transmission(pan, cvv)
        }
        return conn.send(json.dumps(payload))
''',
    "compliant_ai_risk_assessment": '''
class AIModelDeployment:
    """AI model deployment with risk management - EU AI Act Article 9 compliant."""
    
    def __init__(self, model_id: str, risk_level: str):
        self.model_id = model_id
        self.risk_level = risk_level
        self.risk_management = RiskManagementSystem(model_id)
    
    def deploy(self) -> DeploymentResult:
        """Deploy AI model with required risk assessments."""
        # Perform risk assessment (Article 9)
        risk_assessment = self.risk_management.assess()
        
        if not risk_assessment.passed:
            raise ComplianceError(
                f"Risk assessment failed: {risk_assessment.issues}"
            )
        
        # Document deployment (Article 9.1)
        documentation = self.risk_management.generate_documentation()
        
        # Set up continuous monitoring (Article 9.2)
        monitor = self.risk_management.setup_monitoring()
        
        return DeploymentResult(
            model_id=self.model_id,
            risk_assessment=risk_assessment,
            documentation_id=documentation.id,
            monitoring_enabled=True
        )
''',
}

# Sample mapping results
SAMPLE_MAPPINGS = [
    {
        "id": str(uuid4()),
        "file_path": "src/services/user_service.py",
        "function_name": "save_user_data",
        "line_start": 45,
        "line_end": 67,
        "compliance_status": "compliant",
        "confidence": 0.92,
        "matched_requirement": "Data Minimization",
        "evidence": "Uses encrypted storage and audit logging",
    },
    {
        "id": str(uuid4()),
        "file_path": "src/api/legacy_user.py",
        "function_name": "store_user",
        "line_start": 12,
        "line_end": 18,
        "compliance_status": "non_compliant",
        "confidence": 0.95,
        "matched_requirement": "Encrypt PAN at Rest",
        "gaps": ["No encryption applied to sensitive data", "Missing audit logging"],
    },
    {
        "id": str(uuid4()),
        "file_path": "src/handlers/dsar_handler.py",
        "function_name": "process_deletion_request",
        "line_start": 78,
        "line_end": 134,
        "compliance_status": "partial",
        "confidence": 0.78,
        "matched_requirement": "Right to Erasure",
        "gaps": ["Backup data not included in deletion"],
    },
]

# Sample compliance fix suggestions
SAMPLE_FIXES = [
    {
        "id": str(uuid4()),
        "mapping_id": SAMPLE_MAPPINGS[1]["id"],
        "status": "pending",
        "original_code": SAMPLE_CODE_SNIPPETS["non_compliant_plain_storage"],
        "suggested_code": SAMPLE_CODE_SNIPPETS["compliant_data_encryption"],
        "explanation": "Added AES-256-GCM encryption for sensitive fields and audit logging to comply with data protection requirements.",
        "changes": [
            {
                "type": "addition",
                "line": 3,
                "description": "Added encryption call using encrypt_sensitive_fields()",
            },
            {
                "type": "addition",
                "line": 9,
                "description": "Added audit logging for compliance tracking",
            },
        ],
        "confidence": 0.89,
    },
    {
        "id": str(uuid4()),
        "mapping_id": SAMPLE_MAPPINGS[2]["id"],
        "status": "pending",
        "original_code": SAMPLE_CODE_SNIPPETS["non_compliant_partial_deletion"],
        "suggested_code": SAMPLE_CODE_SNIPPETS["compliant_data_deletion"],
        "explanation": "Implemented complete data deletion across all stores with audit trail and deletion certificate for GDPR Article 17 compliance.",
        "changes": [
            {
                "type": "modification",
                "description": "Complete rewrite to handle all data stores and generate deletion certificate",
            },
        ],
        "confidence": 0.85,
    },
]


def get_regulation_by_id(regulation_id: str):
    """Get a sample regulation by ID."""
    for reg in SAMPLE_REGULATIONS:
        if reg["id"] == regulation_id:
            return reg
    return None


def get_requirements_for_regulation(regulation_index: int):
    """Get requirements for a regulation by index (0-3)."""
    if regulation_index == 0:  # GDPR
        return SAMPLE_REQUIREMENTS[:3]
    elif regulation_index == 2:  # PCI-DSS
        return SAMPLE_REQUIREMENTS[3:5]
    elif regulation_index == 3:  # EU AI Act
        return SAMPLE_REQUIREMENTS[5:]
    return []


def create_test_organization():
    """Create a test organization fixture."""
    return {
        "id": str(uuid4()),
        "name": "Test Corporation",
        "slug": "test-corp",
        "plan": "enterprise",
        "settings": {
            "industry": "technology",
            "regions": ["US", "EU"],
            "compliance_frameworks": ["gdpr", "ccpa", "pci_dss"],
        },
    }


def create_test_repository():
    """Create a test repository fixture."""
    return {
        "id": str(uuid4()),
        "name": "test-application",
        "url": "https://github.com/test-corp/test-application",
        "default_branch": "main",
        "scan_patterns": ["**/*.py", "**/*.js", "**/*.ts"],
        "is_active": True,
        "last_scan": datetime.now(timezone.utc).isoformat(),
    }


# All-in-one fixture loader
class ComplianceFixtures:
    """Loader class for compliance test fixtures."""

    @staticmethod
    def regulations():
        return SAMPLE_REGULATIONS

    @staticmethod
    def requirements():
        return SAMPLE_REQUIREMENTS

    @staticmethod
    def code_snippets():
        return SAMPLE_CODE_SNIPPETS

    @staticmethod
    def mappings():
        return SAMPLE_MAPPINGS

    @staticmethod
    def fixes():
        return SAMPLE_FIXES

    @staticmethod
    def organization():
        return create_test_organization()

    @staticmethod
    def repository():
        return create_test_repository()

    @staticmethod
    def full_compliance_scenario():
        """Get a complete compliance testing scenario."""
        org = create_test_organization()
        repo = create_test_repository()
        return {
            "organization": org,
            "repository": repo,
            "regulations": SAMPLE_REGULATIONS,
            "requirements": SAMPLE_REQUIREMENTS,
            "mappings": SAMPLE_MAPPINGS,
            "fixes": SAMPLE_FIXES,
        }
