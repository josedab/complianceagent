# ComplianceAgent SDK for Python

Embed compliance directly in your Python code with decorators and validators.

## Installation

```bash
pip install complianceagent-sdk
```

For encryption support:
```bash
pip install complianceagent-sdk[encryption]
```

## Quick Start

```python
from complianceagent import (
    configure,
    require_consent,
    encrypt_pii,
    audit_log,
    hipaa_phi,
    ComplianceValidator,
    EnforcementMode,
)

# Configure the SDK
configure(
    enforcement_mode=EnforcementMode.STRICT,
    regulations=["GDPR", "HIPAA"],
)

# Require consent before processing
@require_consent("marketing")
def send_marketing_email(user_id: str, content: str):
    # Only executes if user has marketing consent
    send_email(user_id, content)

# Automatically encrypt PII fields
@encrypt_pii(fields=["email", "ssn"])
def store_user(user_id: str, email: str, ssn: str):
    # email and ssn are encrypted before this runs
    database.save(user_id, email, ssn)

# Log all data access for audit trail
@audit_log(action="data_access", regulation="GDPR")
def get_user_profile(user_id: str):
    return database.get_user(user_id)

# HIPAA PHI handling
@hipaa_phi(purpose="treatment")
def get_patient_record(patient_id: str, accessor_id: str):
    # PHI access is logged and validated
    return medical_db.get_record(patient_id)
```

## Features

### Decorators

| Decorator | Description | Regulation |
|-----------|-------------|------------|
| `@require_consent(type)` | Verify user consent before execution | GDPR |
| `@encrypt_pii(fields)` | Automatically encrypt PII fields | GDPR |
| `@audit_log(action)` | Log function calls for audit trail | All |
| `@hipaa_phi(purpose)` | HIPAA PHI access controls | HIPAA |
| `@pci_cardholder()` | PCI-DSS cardholder data handling | PCI-DSS |
| `@gdpr_compliant(basis)` | General GDPR compliance | GDPR |
| `@data_retention(days)` | Enforce retention policies | GDPR |
| `@access_control(roles)` | Role-based access control | All |
| `@breach_detection()` | Detect anomalous access patterns | All |
| `@privacy_by_design()` | Enforce privacy by design | GDPR |

### Validators

```python
from complianceagent import ComplianceValidator, Regulation

validator = ComplianceValidator(regulations=[Regulation.GDPR, Regulation.PCI_DSS])

# Validate data for compliance
result = validator.validate(user_data)
if not result.valid:
    for violation in result.violations:
        print(f"{violation.rule_id}: {violation.message}")

# Validate PII handling
result = validator.validate_pii(
    data={"email": "user@example.com", "ssn": "123-45-6789"},
    allowed_fields=["email"],
)

# Validate consent
result = validator.validate_consent(
    user_id="user123",
    purpose="analytics",
    consent_records=consent_db.get_all(),
)

# Validate retention
result = validator.validate_retention(
    data_records=old_records,
    retention_policy={"user_data": 365, "analytics": 90},
)
```

### Audit Logging

```python
from complianceagent import AuditLogger, AuditAction, AuditSeverity

logger = AuditLogger(
    service_name="user-service",
    output_file="/var/log/compliance/audit.log",
)

# Log data access
logger.log(
    action=AuditAction.ACCESS,
    resource_type="user",
    resource_id="user123",
    user_id="admin@example.com",
    regulation="GDPR",
)

# Log PHI access
logger.log_phi_access(
    user_id="doctor@hospital.com",
    patient_id="patient456",
    purpose="treatment",
)

# Verify audit chain integrity
valid, errors = logger.verify_chain()
```

### Configuration

```python
from complianceagent import configure, EnforcementMode

configure(
    # Enforcement mode
    enforcement_mode=EnforcementMode.STRICT,  # or PERMISSIVE, DISABLED
    
    # Enabled regulations
    regulations=["GDPR", "HIPAA", "PCI-DSS"],
    
    # Consent callback
    consent_callback=lambda user_id, consent_type: check_consent_db(user_id, consent_type),
    
    # Encryption settings
    encryption_key="your-fernet-key",  # For automatic PII encryption
    
    # Audit settings
    audit_log_file="/var/log/compliance/audit.log",
    audit_to_stdout=True,
    
    # Violation handler
    on_violation=lambda type, details: alert_security_team(type, details),
)
```

## Utility Functions

```python
from complianceagent import mask_pii, anonymize_data, validate_email

# Mask sensitive data
masked = mask_pii("1234-5678-9012-3456", visible_chars=4)  # "************3456"

# Anonymize records
safe_data = anonymize_data(
    data={"name": "John Doe", "email": "john@example.com", "status": "active"},
    fields_to_anonymize=["name", "email"],
)
# {"name": "****Doe", "email": "***********com", "status": "active"}

# Validate formats
is_valid = validate_email("user@example.com")  # True
```

## Supported Regulations

- **GDPR** - General Data Protection Regulation
- **HIPAA** - Health Insurance Portability and Accountability Act
- **PCI-DSS** - Payment Card Industry Data Security Standard
- **SOC2** - Service Organization Control 2
- **ISO27001** - Information Security Management
- **CCPA** - California Consumer Privacy Act
- **FERPA** - Family Educational Rights and Privacy Act
- **GLBA** - Gramm-Leach-Bliley Act

## License

MIT License - see LICENSE for details.
