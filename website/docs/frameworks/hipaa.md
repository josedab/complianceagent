---
sidebar_position: 4
title: HIPAA
description: Health Insurance Portability and Accountability Act compliance with ComplianceAgent
---

# HIPAA Compliance

HIPAA establishes national standards for protecting sensitive patient health information.

## Overview

| Attribute | Value |
|-----------|-------|
| **Jurisdiction** | United States |
| **Effective Date** | 1996 (Privacy Rule: 2003) |
| **Applies To** | Covered entities and business associates |
| **Maximum Penalty** | $1.5M per violation category per year |
| **Requirements Tracked** | 89 |

## Covered Entities

HIPAA applies to:

- **Healthcare Providers** - Hospitals, clinics, physicians
- **Health Plans** - Insurance companies, HMOs
- **Healthcare Clearinghouses** - Billing services
- **Business Associates** - Vendors with PHI access

## Protected Health Information (PHI)

```python
# 18 HIPAA Identifiers
PHI_IDENTIFIERS = [
    "name",
    "geographic_subdivision_smaller_than_state",
    "dates_except_year",
    "phone_number",
    "fax_number",
    "email_address",
    "social_security_number",
    "medical_record_number",
    "health_plan_beneficiary_number",
    "account_number",
    "certificate_license_number",
    "vehicle_identifiers",
    "device_identifiers",
    "web_urls",
    "ip_addresses",
    "biometric_identifiers",
    "full_face_photos",
    "unique_identifying_codes"
]

def is_phi(data: dict, health_context: bool = False) -> bool:
    """Determine if data constitutes PHI."""
    has_identifier = any(
        identifier in data for identifier in PHI_IDENTIFIERS
    )
    has_health_info = "health_condition" in data or "treatment" in data
    
    return has_identifier and (has_health_info or health_context)
```

## Key Requirements

### Security Rule Requirements

#### Administrative Safeguards

```yaml
administrative_safeguards:
  security_management_process:
    - risk_analysis: required
    - risk_management: required
    - sanction_policy: required
    - information_system_review: required
  
  workforce_security:
    - authorization_procedures: required
    - workforce_clearance: addressable
    - termination_procedures: required
  
  security_awareness_training:
    - security_reminders: addressable
    - malware_protection: addressable
    - login_monitoring: addressable
    - password_management: addressable
```

#### Technical Safeguards

```python
# HIPAA Technical Safeguards Implementation
class HIPAASecurityControls:
    """HIPAA-compliant security controls."""
    
    # Access Control (§ 164.312(a)(1))
    async def implement_access_control(self):
        return {
            "unique_user_id": self.assign_unique_ids(),
            "emergency_access": self.configure_emergency_access(),
            "automatic_logoff": self.configure_session_timeout(15),  # minutes
            "encryption_decryption": self.enable_encryption()
        }
    
    # Audit Controls (§ 164.312(b))
    async def implement_audit_controls(self):
        return AuditConfiguration(
            log_all_phi_access=True,
            log_all_modifications=True,
            log_all_deletions=True,
            retention_period_years=6,
            tamper_proof=True
        )
    
    # Integrity Controls (§ 164.312(c)(1))
    async def implement_integrity_controls(self):
        return {
            "electronic_mechanisms": self.enable_checksums(),
            "phi_alteration_protection": self.enable_version_control()
        }
    
    # Transmission Security (§ 164.312(e)(1))
    async def implement_transmission_security(self):
        return {
            "integrity_controls": self.enable_message_authentication(),
            "encryption": self.require_tls_1_3()
        }
```

#### Physical Safeguards

```yaml
physical_safeguards:
  facility_access_controls:
    - contingency_operations: addressable
    - facility_security_plan: addressable
    - access_control_validation: addressable
    - maintenance_records: addressable
  
  workstation_use:
    - policies: required
  
  workstation_security:
    - physical_safeguards: required
  
  device_media_controls:
    - disposal: required
    - media_reuse: required
    - accountability: addressable
    - data_backup_storage: addressable
```

### Minimum Necessary Standard

```python
# Implement minimum necessary access
class MinimumNecessaryAccess:
    """Limit PHI access to minimum necessary."""
    
    def __init__(self):
        self.role_permissions = {
            "billing": ["patient_id", "service_codes", "dates"],
            "nurse": ["patient_id", "vitals", "medications", "allergies"],
            "physician": ["full_medical_record"],
            "receptionist": ["name", "contact_info", "appointment_time"]
        }
    
    def get_accessible_fields(
        self, 
        user_role: str, 
        purpose: str
    ) -> list[str]:
        """Return only fields necessary for the role/purpose."""
        base_fields = self.role_permissions.get(user_role, [])
        
        # Further restrict based on purpose
        if purpose == "appointment_reminder":
            return ["name", "phone", "appointment_time"]
        
        return base_fields
    
    async def fetch_phi(
        self, 
        patient_id: str, 
        user_role: str,
        purpose: str
    ) -> dict:
        """Fetch only minimum necessary PHI."""
        allowed_fields = self.get_accessible_fields(user_role, purpose)
        
        return await self.database.fetch(
            patient_id,
            fields=allowed_fields
        )
```

### Breach Notification

```python
async def handle_hipaa_breach(breach: BreachIncident):
    """Handle HIPAA breach notification requirements."""
    
    # Assess if notification required (risk assessment)
    risk = await assess_breach_risk(breach)
    
    if risk.notification_required:
        affected_count = len(breach.affected_individuals)
        
        # Individual notification (within 60 days)
        await notify_individuals(
            breach.affected_individuals,
            breach_description=breach.description,
            steps_taken=breach.remediation,
            deadline=timedelta(days=60)
        )
        
        # HHS notification
        if affected_count >= 500:
            # Notify HHS within 60 days for large breaches
            await notify_hhs(breach, timeline="immediate")
            # Media notification required
            await notify_media(breach.state)
        else:
            # Log for annual HHS notification
            await log_for_annual_notification(breach)
        
        # Document everything
        await document_breach(breach, risk, notifications_sent=True)
```

## Common Gaps

### 1. Insufficient Access Logging

**Issue:** Not logging all PHI access for audit purposes.

**Solution:**

```python
# Log all PHI access
async def access_phi(user: User, patient_id: str, purpose: str):
    """Access PHI with mandatory logging."""
    
    # Log before access
    await audit_log.record(
        event="phi_access_attempt",
        user_id=user.id,
        patient_id=patient_id,
        purpose=purpose,
        timestamp=datetime.now(),
        ip_address=get_client_ip()
    )
    
    # Verify authorization
    if not await verify_authorization(user, patient_id):
        await audit_log.record(event="phi_access_denied", ...)
        raise UnauthorizedAccessError()
    
    # Fetch and log success
    data = await fetch_phi(patient_id, user.role)
    await audit_log.record(event="phi_access_success", ...)
    
    return data
```

### 2. Missing Business Associate Agreements

**Issue:** Using vendors without BAAs in place.

**Solution:** ComplianceAgent identifies vendor integrations and flags missing BAAs:

```yaml
# Vendor PHI assessment
vendor_assessment:
  aws:
    has_baa: true
    baa_signed: "2024-01-15"
    services_covered: ["S3", "RDS", "Lambda"]
  
  analytics_vendor:
    has_baa: false  # FLAG: Missing BAA
    phi_exposure: true
    action_required: "Sign BAA before PHI processing"
```

### 3. Unencrypted PHI

**Issue:** PHI stored or transmitted without encryption.

**Solution:**

```python
# Encryption requirements
class PHIEncryption:
    """HIPAA-compliant PHI encryption."""
    
    # At rest - AES-256
    @staticmethod
    def encrypt_at_rest(phi_data: bytes) -> bytes:
        return aes_256_encrypt(phi_data, get_kms_key())
    
    # In transit - TLS 1.2+
    @staticmethod
    def get_ssl_context() -> ssl.SSLContext:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        return context
```

### 4. Inadequate Risk Analysis

**Issue:** No documented risk analysis.

**Solution:** Use ComplianceAgent's risk assessment template:

```bash
# Generate HIPAA risk analysis
curl -X POST "http://localhost:8000/api/v1/compliance/hipaa/risk-analysis" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"repository": "acme/healthcare-app"}'
```

## Configuration

```yaml
# .complianceagent/config.yml
frameworks:
  hipaa:
    enabled: true
    
    # Your role
    entity_type: "covered_entity"  # or "business_associate"
    
    # PHI handling
    phi_categories:
      - medical_records
      - billing_information
      - appointment_data
    
    # Security rule requirements
    security_rule:
      addressable_implementations:
        automatic_logoff: true
        encryption: true
        audit_controls: true
```

## Templates

| Template | Description |
|----------|-------------|
| `hipaa-phi-handler` | PHI access with logging |
| `hipaa-encryption` | Encryption at rest/transit |
| `hipaa-audit-log` | Compliant audit logging |
| `hipaa-breach-handler` | Breach notification workflow |
| `hipaa-access-control` | Role-based PHI access |

## API Endpoints

```bash
# Get HIPAA compliance status
GET /api/v1/compliance/status?framework=hipaa

# Run risk analysis
POST /api/v1/compliance/hipaa/risk-analysis

# Get audit logs
GET /api/v1/audit/phi-access?patient_id=123

# Report breach
POST /api/v1/hipaa/breach
```

---

See also: [SOC 2](./soc2) | [GDPR](./gdpr) | [Frameworks Overview](./overview)
