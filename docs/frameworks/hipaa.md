# HIPAA Compliance Guide

This guide covers how ComplianceAgent helps you achieve compliance with the Health Insurance Portability and Accountability Act (HIPAA).

## Overview

| Attribute | Value |
|-----------|-------|
| **Full Name** | Health Insurance Portability and Accountability Act |
| **Jurisdiction** | United States (Federal) |
| **Effective Date** | Privacy Rule: 2003, Security Rule: 2005 |
| **Enforcing Authority** | HHS Office for Civil Rights (OCR) |
| **Max Penalty** | $1.5M per violation category per year |

### Who Must Comply

- **Covered Entities**: Healthcare providers, health plans, healthcare clearinghouses
- **Business Associates**: Third parties handling PHI on behalf of covered entities

## Key Concepts

### Protected Health Information (PHI)

PHI includes any health information that can identify an individual:

```python
class PHIIdentifiers(Enum):
    """18 HIPAA identifiers that make health info PHI."""
    NAME = "name"
    GEOGRAPHIC = "geographic_subdivision"  # Smaller than state
    DATES = "dates"  # Birth, admission, discharge, death
    PHONE = "phone_number"
    FAX = "fax_number"
    EMAIL = "email"
    SSN = "social_security_number"
    MRN = "medical_record_number"
    HEALTH_PLAN_ID = "health_plan_beneficiary"
    ACCOUNT_NUMBER = "account_number"
    LICENSE_NUMBER = "certificate_license_number"
    VEHICLE_ID = "vehicle_identifier"
    DEVICE_ID = "device_identifier"
    URL = "web_url"
    IP_ADDRESS = "ip_address"
    BIOMETRIC = "biometric_identifier"
    PHOTO = "full_face_photo"
    OTHER_UNIQUE = "other_unique_identifier"
```

### The Three Rules

| Rule | Focus | Key Requirements |
|------|-------|------------------|
| **Privacy Rule** | Use/disclosure of PHI | Minimum necessary, patient rights, authorizations |
| **Security Rule** | ePHI protection | Administrative, physical, technical safeguards |
| **Breach Notification** | Incident response | 60-day notification, risk assessment |

## ComplianceAgent Detection

### Automatically Detected Issues

```
HIPAA-001: PHI transmitted without encryption
HIPAA-002: Missing access controls for PHI
HIPAA-003: Inadequate audit logging
HIPAA-004: PHI in application logs
HIPAA-005: Missing encryption at rest
HIPAA-006: No session timeout for PHI access
HIPAA-007: PHI exposed in error messages
HIPAA-008: Missing Business Associate Agreement check
HIPAA-009: Insufficient backup/disaster recovery
HIPAA-010: PHI retention beyond required period
```

### Example Detection

**Issue: HIPAA-001 - PHI transmitted without encryption**

```python
# ❌ Non-compliant: Sending PHI over unencrypted connection
import requests

def send_patient_data(patient):
    # PHI sent without TLS
    response = requests.post(
        "http://api.example.com/patients",  # HTTP not HTTPS!
        json={
            "name": patient.name,
            "ssn": patient.ssn,
            "diagnosis": patient.diagnosis
        }
    )
    return response.json()
```

**ComplianceAgent Fix:**

```python
# ✅ Compliant: Encrypted transmission with certificate validation
import httpx
from cryptography.fernet import Fernet

class HIPAACompliantClient:
    def __init__(self, base_url: str, cert_path: str):
        # HIPAA §164.312(e)(1): Transmission security
        if not base_url.startswith("https://"):
            raise ValueError("HIPAA requires encrypted transmission (HTTPS)")
        
        self.client = httpx.Client(
            base_url=base_url,
            verify=cert_path,  # Certificate validation
            timeout=30.0
        )
        self.encryptor = Fernet(settings.PHI_ENCRYPTION_KEY)
    
    def send_patient_data(self, patient: Patient) -> dict:
        # Encrypt sensitive fields at application layer
        encrypted_data = {
            "name": self.encrypt_phi(patient.name),
            "ssn": self.encrypt_phi(patient.ssn),
            "diagnosis": self.encrypt_phi(patient.diagnosis),
            "encrypted": True
        }
        
        # Audit log (without PHI)
        audit_log.record(
            action="phi_transmitted",
            patient_id=patient.id,
            destination="api.example.com",
            user=current_user.id
        )
        
        response = self.client.post("/patients", json=encrypted_data)
        return response.json()
    
    def encrypt_phi(self, value: str) -> str:
        return self.encryptor.encrypt(value.encode()).decode()
```

## Implementation Patterns

### Access Control (§164.312(a)(1))

```python
from enum import Enum
from functools import wraps

class PHIAccessLevel(Enum):
    NONE = 0
    VIEW = 1
    EDIT = 2
    ADMIN = 3

class Role(Enum):
    PATIENT = PHIAccessLevel.VIEW  # Own records only
    NURSE = PHIAccessLevel.VIEW
    DOCTOR = PHIAccessLevel.EDIT
    ADMIN = PHIAccessLevel.ADMIN

def require_phi_access(minimum_level: PHIAccessLevel):
    """
    HIPAA §164.312(a)(1): Access control.
    Decorator to enforce PHI access requirements.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = get_current_user()
            patient_id = kwargs.get('patient_id')
            
            # Check access level
            if user.phi_access_level.value < minimum_level.value:
                audit_log.record(
                    action="phi_access_denied",
                    user=user.id,
                    patient_id=patient_id,
                    reason="insufficient_privileges"
                )
                raise HTTPException(403, "Insufficient PHI access privileges")
            
            # Minimum necessary: Check if user needs this specific patient
            if not await can_access_patient(user, patient_id):
                audit_log.record(
                    action="phi_access_denied",
                    user=user.id,
                    patient_id=patient_id,
                    reason="no_treatment_relationship"
                )
                raise HTTPException(403, "No authorized access to this patient")
            
            # Log access
            audit_log.record(
                action="phi_accessed",
                user=user.id,
                patient_id=patient_id,
                access_type=func.__name__
            )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@app.get("/api/patients/{patient_id}/records")
@require_phi_access(PHIAccessLevel.VIEW)
async def get_patient_records(patient_id: str):
    """Retrieve patient medical records."""
    return await db.get_patient_records(patient_id)
```

### Audit Controls (§164.312(b))

```python
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON

class PHIAuditLog(Base):
    """
    HIPAA §164.312(b): Audit controls.
    Immutable log of all PHI access.
    """
    __tablename__ = "phi_audit_log"
    
    id = Column(UUID, primary_key=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    user_id = Column(UUID, nullable=False)
    action = Column(String, nullable=False)  # view, create, update, delete, export
    patient_id = Column(UUID)
    resource_type = Column(String)  # patient, prescription, lab_result
    resource_id = Column(UUID)
    ip_address = Column(String)
    user_agent = Column(String)
    success = Column(Boolean, default=True)
    failure_reason = Column(String)
    # Store what fields were accessed (not values)
    fields_accessed = Column(JSON)
    
    # Hash chain for tamper detection
    previous_hash = Column(String)
    entry_hash = Column(String)

async def log_phi_access(
    action: str,
    user: User,
    patient_id: str = None,
    resource_type: str = None,
    resource_id: str = None,
    fields: list[str] = None,
    success: bool = True,
    failure_reason: str = None
):
    """Log all PHI access with tamper-evident hash chain."""
    # Get previous entry hash
    last_entry = await db.query(PHIAuditLog).order_by(
        PHIAuditLog.timestamp.desc()
    ).first()
    previous_hash = last_entry.entry_hash if last_entry else "GENESIS"
    
    entry = PHIAuditLog(
        timestamp=datetime.utcnow(),
        user_id=user.id,
        action=action,
        patient_id=patient_id,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        success=success,
        failure_reason=failure_reason,
        fields_accessed=fields,
        previous_hash=previous_hash
    )
    
    # Calculate hash
    entry.entry_hash = calculate_hash(entry, previous_hash)
    
    db.add(entry)
    await db.commit()
```

### Encryption at Rest (§164.312(a)(2)(iv))

```python
from sqlalchemy import TypeDecorator, String
from cryptography.fernet import Fernet

class EncryptedPHI(TypeDecorator):
    """
    HIPAA §164.312(a)(2)(iv): Encryption at rest.
    Automatically encrypts PHI when stored, decrypts when retrieved.
    """
    impl = String
    cache_ok = True
    
    def __init__(self):
        super().__init__()
        self.fernet = Fernet(settings.PHI_ENCRYPTION_KEY)
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return self.fernet.encrypt(value.encode()).decode()
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return self.fernet.decrypt(value.encode()).decode()
        return value

class Patient(Base):
    """Patient model with encrypted PHI fields."""
    __tablename__ = "patients"
    
    id = Column(UUID, primary_key=True)
    # Non-PHI
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    # Encrypted PHI
    name = Column(EncryptedPHI)
    ssn = Column(EncryptedPHI)
    date_of_birth = Column(EncryptedPHI)
    address = Column(EncryptedPHI)
    phone = Column(EncryptedPHI)
    email = Column(EncryptedPHI)
    medical_record_number = Column(EncryptedPHI)
```

### Session Management (§164.312(d))

```python
from datetime import datetime, timedelta

# HIPAA requires automatic logoff
SESSION_TIMEOUT_MINUTES = 15

@app.middleware("http")
async def hipaa_session_middleware(request: Request, call_next):
    """
    HIPAA §164.312(d): Person or entity authentication.
    Automatic session timeout for PHI access.
    """
    session = get_session(request)
    
    if session and session.user_id:
        last_activity = session.last_activity
        
        # Check for timeout
        if datetime.utcnow() - last_activity > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            # Log session timeout
            await log_phi_access(
                action="session_timeout",
                user=session.user,
                success=True
            )
            
            # Invalidate session
            await invalidate_session(session)
            raise HTTPException(401, "Session expired due to inactivity")
        
        # Update last activity
        session.last_activity = datetime.utcnow()
        await save_session(session)
    
    return await call_next(request)
```

### Breach Notification

```python
from datetime import datetime, timedelta

class BreachAssessment(BaseModel):
    """HIPAA breach risk assessment."""
    discovered_at: datetime
    notification_deadline: datetime  # 60 days
    individuals_affected: int
    phi_types: list[str]
    probability_compromised: float  # 0-1
    
    def requires_notification(self) -> bool:
        """
        Determine if breach requires notification.
        Notification required unless low probability of compromise.
        """
        return self.probability_compromised > 0.1

@app.post("/api/security/breach-report")
async def report_breach(
    breach: BreachReport,
    current_user: User = Depends(get_current_user)
):
    """
    HIPAA Breach Notification Rule.
    Must notify within 60 days of discovery.
    """
    assessment = BreachAssessment(
        discovered_at=datetime.utcnow(),
        notification_deadline=datetime.utcnow() + timedelta(days=60),
        individuals_affected=breach.affected_count,
        phi_types=breach.phi_types,
        probability_compromised=assess_compromise_probability(breach)
    )
    
    if assessment.requires_notification():
        # Initiate notification process
        await initiate_breach_notification(assessment)
        
        if assessment.individuals_affected >= 500:
            # Media notification required
            await notify_media(assessment)
            # Immediate HHS notification
            await notify_hhs_immediately(assessment)
        else:
            # Annual HHS log
            await log_for_annual_hhs_report(assessment)
    
    return {"assessment": assessment, "requires_notification": assessment.requires_notification()}
```

## Configuration

```bash
# .env
COMPLIANCE_FRAMEWORKS=hipaa
HIPAA_ENCRYPTION_KEY=<32-byte-base64-key>
HIPAA_SESSION_TIMEOUT_MINUTES=15
HIPAA_AUDIT_RETENTION_YEARS=6
HIPAA_BAA_REQUIRED=true
```

## Business Associate Requirements

```python
async def validate_vendor_baa(vendor_id: str) -> bool:
    """
    HIPAA requires BAA with all business associates.
    Check BAA status before sharing PHI.
    """
    baa = await db.business_associate_agreements.get(vendor_id)
    
    if not baa or not baa.is_active:
        audit_log.record(
            action="phi_share_blocked",
            reason="missing_baa",
            vendor_id=vendor_id
        )
        raise ComplianceError("Cannot share PHI: No active BAA with vendor")
    
    return True
```

## CI/CD Integration

```yaml
- name: HIPAA Compliance Check
  uses: complianceagent/compliance-action@v1
  with:
    frameworks: hipaa
    fail-on: critical
    hipaa-check-encryption: true
    hipaa-check-audit-logs: true
    hipaa-check-access-controls: true
```

## Resources

- [HHS HIPAA Homepage](https://www.hhs.gov/hipaa/index.html)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [Breach Notification Rule](https://www.hhs.gov/hipaa/for-professionals/breach-notification/index.html)

## Related Frameworks

- [GDPR](gdpr.md) - EU data protection with health data provisions
- [SOC 2](soc2.md) - Security controls audit framework
- [HITRUST](hitrust.md) - Healthcare-specific security framework
