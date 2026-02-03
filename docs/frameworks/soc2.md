# SOC 2 Compliance Guide

This guide covers how ComplianceAgent helps you achieve and maintain compliance with SOC 2 (Service Organization Control 2).

## Overview

| Attribute | Value |
|-----------|-------|
| **Full Name** | Service Organization Control 2 |
| **Jurisdiction** | United States (Global recognition) |
| **Developed By** | AICPA (American Institute of CPAs) |
| **Report Types** | Type I (point-in-time), Type II (over time) |
| **Audit Frequency** | Annual |

## Trust Service Criteria

SOC 2 is built around five Trust Service Criteria (TSC):

| Criteria | Description | Code Impact |
|----------|-------------|-------------|
| **Security** | Protection against unauthorized access | Authentication, encryption, access controls |
| **Availability** | System uptime and accessibility | Error handling, redundancy, monitoring |
| **Processing Integrity** | Accurate and timely processing | Validation, logging, error detection |
| **Confidentiality** | Protection of confidential data | Encryption, access controls, data classification |
| **Privacy** | Personal information handling | Consent, data minimization, retention |

## Key Requirements

### Security (Common Criteria)

| Control ID | Requirement | Implementation |
|------------|-------------|----------------|
| CC6.1 | Logical access security | Role-based access control (RBAC) |
| CC6.2 | Authentication mechanisms | MFA, strong passwords, session management |
| CC6.3 | Authorization controls | Permission verification, least privilege |
| CC6.6 | Encryption of data | TLS, AES-256, key management |
| CC6.7 | Transmission security | HTTPS, secure APIs |
| CC7.1 | Vulnerability management | Dependency scanning, patching |
| CC7.2 | Security monitoring | Logging, alerting, SIEM integration |

### Availability

| Control ID | Requirement | Implementation |
|------------|-------------|----------------|
| A1.1 | Capacity planning | Resource monitoring, auto-scaling |
| A1.2 | Disaster recovery | Backups, failover, recovery procedures |
| A1.3 | Recovery testing | Regular DR drills, RTO/RPO validation |

### Processing Integrity

| Control ID | Requirement | Implementation |
|------------|-------------|----------------|
| PI1.1 | Input validation | Schema validation, sanitization |
| PI1.2 | Processing accuracy | Checksums, reconciliation |
| PI1.3 | Output completeness | Response validation, audit trails |

### Confidentiality

| Control ID | Requirement | Implementation |
|------------|-------------|----------------|
| C1.1 | Data classification | Labeling, handling procedures |
| C1.2 | Confidential data protection | Encryption at rest and in transit |

## ComplianceAgent Detection

### Automatically Detected Issues

```
SOC2-001: Missing authentication on endpoint
SOC2-002: Hardcoded credentials or secrets
SOC2-003: Insufficient logging for security events
SOC2-004: Missing input validation
SOC2-005: Unencrypted sensitive data storage
SOC2-006: Missing rate limiting
SOC2-007: Inadequate error handling exposing internals
SOC2-008: Missing access control checks
SOC2-009: Insecure session management
SOC2-010: Missing audit trail for data changes
```

### Example Detection

**Issue: SOC2-002 - Hardcoded credentials**

```python
# ❌ Non-compliant: Hardcoded database credentials
DATABASE_URL = "postgresql://admin:secretpassword123@db.example.com/prod"

def connect_database():
    return create_engine(DATABASE_URL)
```

**ComplianceAgent Fix:**

```python
# ✅ Compliant: Credentials from secure configuration
import os
from functools import lru_cache

@lru_cache
def get_database_url() -> str:
    """Retrieve database URL from secure environment configuration."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable not set")
    return url

def connect_database():
    return create_engine(get_database_url())
```

**Issue: SOC2-003 - Insufficient logging**

```python
# ❌ Non-compliant: No audit logging for sensitive operation
@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str, current_user: User):
    await db.users.delete(user_id)
    return {"status": "deleted"}
```

**ComplianceAgent Fix:**

```python
# ✅ Compliant: Comprehensive audit logging
import structlog
from datetime import datetime

logger = structlog.get_logger()

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str, current_user: User):
    # SOC2 CC7.2: Log security-relevant events
    logger.info(
        "user_deletion_initiated",
        target_user_id=user_id,
        initiated_by=current_user.id,
        initiated_at=datetime.utcnow().isoformat(),
        ip_address=request.client.host,
    )
    
    await db.users.delete(user_id)
    
    logger.info(
        "user_deletion_completed",
        target_user_id=user_id,
        initiated_by=current_user.id,
    )
    return {"status": "deleted"}
```

**Issue: SOC2-007 - Error handling exposing internals**

```python
# ❌ Non-compliant: Exposing internal error details
@app.get("/api/data/{id}")
async def get_data(id: str):
    try:
        return await db.data.get(id)
    except Exception as e:
        # Exposes stack trace and internal details
        raise HTTPException(status_code=500, detail=str(e))
```

**ComplianceAgent Fix:**

```python
# ✅ Compliant: Safe error handling with internal logging
import uuid
import structlog

logger = structlog.get_logger()

@app.get("/api/data/{id}")
async def get_data(id: str):
    try:
        return await db.data.get(id)
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Resource not found")
    except Exception as e:
        # SOC2 CC7.2: Log full error internally
        error_id = str(uuid.uuid4())
        logger.error(
            "unexpected_error",
            error_id=error_id,
            error_type=type(e).__name__,
            error_message=str(e),
            resource_id=id,
        )
        # Return safe error to client
        raise HTTPException(
            status_code=500,
            detail=f"Internal error. Reference: {error_id}"
        )
```

## SDK Integration

```python
from complianceagent import audit_log, access_control, configure

configure(regulations=["SOC2"])

# Audit logging decorator
@audit_log(action="data_access", regulation="SOC2")
async def get_customer_data(customer_id: str):
    return await db.customers.get(customer_id)

# Access control decorator
@access_control(roles=["admin", "support"])
async def view_audit_logs(start_date: str, end_date: str):
    return await db.audit_logs.query(start_date, end_date)
```

## Evidence Collection

ComplianceAgent automatically collects evidence for SOC 2 audits:

| Evidence Type | Description | Location |
|---------------|-------------|----------|
| Access logs | Authentication and authorization events | `/var/log/complianceagent/access.log` |
| Change logs | Code and configuration changes | Git history, audit trail |
| Security scans | Vulnerability scan results | Dashboard → Security → Scans |
| Incident records | Security incident documentation | Dashboard → Incidents |
| Policy documents | Security policies and procedures | `/docs/policies/` |

## Audit Preparation

### Pre-Audit Checklist

```bash
# Generate SOC 2 compliance report
complianceagent report generate --framework soc2 --output soc2-report.pdf

# Export audit evidence
complianceagent evidence export --framework soc2 --period "2024-01-01:2024-12-31"

# Verify control effectiveness
complianceagent controls test --framework soc2
```

### Control Mapping

ComplianceAgent maps your codebase to SOC 2 controls:

```
Dashboard → Compliance → SOC 2 → Control Mapping

┌─────────────────────────────────────────────────────────┐
│ Control CC6.1: Logical Access Security                  │
├─────────────────────────────────────────────────────────┤
│ Status: ✅ Implemented                                  │
│ Evidence:                                               │
│   - backend/app/core/security.py (RBAC implementation) │
│   - backend/app/api/deps.py (permission checks)        │
│   - 47 endpoints with access controls                  │
│ Last Verified: 2024-01-15                              │
└─────────────────────────────────────────────────────────┘
```

## Best Practices

### 1. Implement Defense in Depth

```python
# Multiple layers of security
@require_authentication  # Layer 1: Authentication
@require_role("admin")   # Layer 2: Authorization
@rate_limit(100, 60)     # Layer 3: Rate limiting
@audit_log("admin_action")  # Layer 4: Audit logging
async def admin_operation():
    pass
```

### 2. Encrypt Sensitive Data

```python
from complianceagent import encrypt_field

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(UUID, primary_key=True)
    name = Column(String)
    # SOC2 C1.2: Encrypt confidential data
    ssn = Column(encrypt_field(String))
    tax_id = Column(encrypt_field(String))
```

### 3. Implement Comprehensive Logging

```python
# Log all security-relevant events
SECURITY_EVENTS = [
    "login_success", "login_failure", "logout",
    "password_change", "permission_change",
    "data_access", "data_modification", "data_deletion",
    "api_key_created", "api_key_revoked",
]
```

## Resources

- [AICPA SOC 2 Guide](https://www.aicpa.org/soc2)
- [Trust Services Criteria](https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/trustservicescriteria.html)
- [SOC 2 Type II Requirements](https://www.aicpa.org/resources/article/soc-2-reporting-on-an-examination-of-controls)

## Related Documentation

- [Security Best Practices](../guides/security.md)
- [Audit Trail Feature](../features/audit-trail.md)
- [API Authentication](../api/reference.md#authentication)
