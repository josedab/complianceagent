# Shared Modules

This directory contains shared libraries and schemas used across ComplianceAgent components.

## Contents

| Module | Description | Language |
|--------|-------------|----------|
| [`compliance-sdk-python/`](compliance-sdk-python/) | Python SDK for embedding compliance checks | Python 3.10+ |
| [`schemas/`](schemas/) | Shared JSON schemas and type definitions | JSON Schema |

---

## Python SDK

The ComplianceAgent Python SDK provides decorators and validators for embedding compliance directly into your Python applications.

### Installation

```bash
# From PyPI (when published)
pip install complianceagent-sdk

# From source (development)
cd shared/compliance-sdk-python
pip install -e .

# With encryption support
pip install -e ".[encryption]"
```

### Quick Start

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

# Use decorators for compliance
@require_consent("marketing")
def send_marketing_email(user_id: str, content: str):
    send_email(user_id, content)

@encrypt_pii(fields=["email", "ssn"])
def store_user(user_id: str, email: str, ssn: str):
    database.save(user_id, email, ssn)

@audit_log(action="data_access", regulation="GDPR")
def get_user_profile(user_id: str):
    return database.get_user(user_id)
```

### Module Structure

```
compliance-sdk-python/
├── complianceagent/
│   ├── __init__.py      # Public API exports
│   ├── config.py        # Configuration and settings
│   ├── decorators.py    # Compliance decorators
│   ├── validators.py    # Data validators
│   ├── audit.py         # Audit logging utilities
│   └── exceptions.py    # Custom exceptions
├── pyproject.toml       # Package configuration
└── README.md            # Detailed SDK documentation
```

### Features

#### Decorators

| Decorator | Purpose | Regulations |
|-----------|---------|-------------|
| `@require_consent(type)` | Verify consent before execution | GDPR, CCPA |
| `@encrypt_pii(fields)` | Auto-encrypt PII fields | GDPR, HIPAA, GLBA |
| `@audit_log(action)` | Log function calls for audit | All |
| `@hipaa_phi(purpose)` | HIPAA PHI access controls | HIPAA |
| `@pci_cardholder()` | PCI-DSS cardholder handling | PCI-DSS |
| `@gdpr_compliant(basis)` | GDPR compliance wrapper | GDPR |
| `@data_retention(days)` | Enforce retention policies | GDPR, CCPA |
| `@access_control(roles)` | Role-based access | All |

#### Validators

```python
from complianceagent import ComplianceValidator, Regulation

validator = ComplianceValidator(
    regulations=[Regulation.GDPR, Regulation.HIPAA]
)

# Validate data
result = validator.validate(user_data)
if not result.valid:
    for violation in result.violations:
        print(f"{violation.rule_id}: {violation.message}")
```

#### Configuration

```python
from complianceagent import configure, EnforcementMode

configure(
    enforcement_mode=EnforcementMode.STRICT,
    regulations=["GDPR", "HIPAA", "PCI-DSS"],
    consent_callback=check_consent_db,
    encryption_key="your-fernet-key",
    audit_log_file="/var/log/compliance/audit.log",
    on_violation=alert_security_team,
)
```

See [SDK README](compliance-sdk-python/README.md) for complete documentation.

---

## JSON Schemas

Shared schemas for API contracts and data validation.

### Available Schemas

| Schema | Description | Used By |
|--------|-------------|---------|
| `regulation.json` | Regulation data structure | Backend, Frontend |
| `compliance-result.json` | Compliance check results | All components |
| `audit-event.json` | Audit log event format | Backend, SDK |
| `violation.json` | Compliance violation format | All components |

### Usage

#### Python (jsonschema)

```python
import json
import jsonschema

with open("shared/schemas/regulation.json") as f:
    schema = json.load(f)

# Validate data against schema
jsonschema.validate(instance=data, schema=schema)
```

#### TypeScript (frontend)

```typescript
import type { Regulation } from '@/types/regulation';
// Types generated from shared schemas
```

---

## Development

### Running SDK Tests

```bash
cd shared/compliance-sdk-python
pip install -e ".[dev]"
pytest tests/ -v
```

### Building the SDK

```bash
cd shared/compliance-sdk-python
python -m build
```

### Publishing

```bash
# Test PyPI
twine upload --repository testpypi dist/*

# Production PyPI
twine upload dist/*
```

---

## Integration with Backend

The backend uses the SDK internally:

```python
# backend/app/services/compliance_check.py
from complianceagent import ComplianceValidator, audit_log

validator = ComplianceValidator(regulations=["GDPR"])

@audit_log(action="code_analysis")
async def analyze_code(code: str, regulations: list[str]):
    return validator.analyze(code, regulations)
```

## Integration with Frontend

The frontend uses TypeScript types generated from schemas:

```bash
# Generate TypeScript types from JSON schemas
npm run generate-types
```

---

## Related Documentation

- [Backend Development Guide](../docs/development/backend.md)
- [API Reference](../docs/api/reference.md)
- [SDK Documentation](../docs/api/sdk.md)
