---
sidebar_position: 2
title: GDPR
description: General Data Protection Regulation compliance with ComplianceAgent
---

# GDPR Compliance

The General Data Protection Regulation (GDPR) is the EU's comprehensive data protection law. ComplianceAgent provides full support for GDPR compliance.

## Overview

| Attribute | Value |
|-----------|-------|
| **Jurisdiction** | European Union + EEA |
| **Effective Date** | May 25, 2018 |
| **Applies To** | Organizations processing EU residents' data |
| **Maximum Penalty** | €20M or 4% global revenue |
| **Requirements Tracked** | 127 |

## Key Requirements

### Lawful Basis for Processing (Art. 6)

Processing personal data requires a lawful basis:

```python
# ComplianceAgent detects and suggests:
class ProcessingBasis(Enum):
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"

def process_personal_data(data: PersonalData, basis: ProcessingBasis):
    """Process data only with valid lawful basis."""
    if basis == ProcessingBasis.CONSENT:
        verify_consent(data.subject_id)
    elif basis == ProcessingBasis.LEGITIMATE_INTERESTS:
        verify_lia_completed(data.purpose)
    
    # Log processing activity
    record_processing(data, basis)
```

### Consent Requirements (Art. 7)

Consent must be freely given, specific, informed, and unambiguous:

```typescript
// Generated consent collection pattern
interface ConsentRequest {
  purpose: string;
  description: string;
  dataCategories: string[];
  retentionPeriod: string;
  thirdParties?: string[];
  withdrawalMethod: string;
}

async function collectConsent(
  userId: string,
  request: ConsentRequest
): Promise<ConsentRecord> {
  // Present clear consent request
  const consent = await presentConsentUI(request);
  
  if (!consent.granted) {
    throw new ConsentDeclinedError(request.purpose);
  }
  
  // Store consent record
  return await storeConsent({
    userId,
    purpose: request.purpose,
    grantedAt: new Date(),
    version: request.version,
    method: 'explicit_opt_in'
  });
}
```

### Data Subject Rights (Art. 15-22)

| Right | Article | Implementation |
|-------|---------|----------------|
| Access | Art. 15 | Export user data in portable format |
| Rectification | Art. 16 | Allow data correction |
| Erasure | Art. 17 | Complete data deletion |
| Portability | Art. 20 | Machine-readable export |
| Object | Art. 21 | Stop processing on request |

Template for Right to Erasure:

```python
# GDPR Art. 17 - Right to Erasure Template
async def handle_erasure_request(user_id: UUID) -> ErasureResult:
    """Handle GDPR Article 17 erasure request."""
    result = ErasureResult(user_id=user_id)
    
    # 1. Verify identity
    await verify_identity(user_id)
    
    # 2. Check for exceptions (Art. 17(3))
    exceptions = await check_erasure_exceptions(user_id)
    if exceptions:
        return ErasureResult(
            status="partially_completed",
            exceptions=exceptions
        )
    
    # 3. Delete from all systems
    async with transaction():
        # Primary database
        await delete_user_records(user_id)
        
        # Search indices
        await search_service.delete_user(user_id)
        
        # File storage
        await storage_service.delete_user_files(user_id)
        
        # Backups (schedule for deletion)
        await backup_service.schedule_deletion(user_id)
    
    # 4. Notify processors
    processors = await get_data_processors()
    for processor in processors:
        await processor.notify_deletion(user_id)
    
    # 5. Create audit record
    await audit_log.record(
        event="gdpr_erasure_completed",
        user_id=user_id,
        timestamp=datetime.now()
    )
    
    return ErasureResult(status="completed")
```

### Security Measures (Art. 32)

Technical and organizational measures:

```yaml
# ComplianceAgent checks for:
security_measures:
  encryption:
    - at_rest: AES-256
    - in_transit: TLS 1.3
  
  access_control:
    - authentication: MFA required
    - authorization: RBAC implemented
    - session_management: Secure tokens
  
  logging:
    - access_logs: Enabled
    - audit_trail: Tamper-proof
  
  resilience:
    - backups: Encrypted, tested
    - disaster_recovery: Documented
```

### Breach Notification (Art. 33-34)

```python
# Breach notification handler
async def handle_data_breach(breach: DataBreach):
    """Handle GDPR breach notification requirements."""
    
    # Assess risk to individuals
    risk_level = assess_breach_risk(breach)
    
    if risk_level != "unlikely_risk":
        # Art. 33: Notify supervisory authority within 72 hours
        await notify_supervisory_authority(
            breach=breach,
            deadline=timedelta(hours=72)
        )
    
    if risk_level == "high_risk":
        # Art. 34: Notify affected individuals
        affected_users = await identify_affected_users(breach)
        await notify_affected_individuals(
            users=affected_users,
            breach=breach
        )
    
    # Document the breach
    await document_breach(breach, risk_level)
```

## Common Gaps

ComplianceAgent frequently identifies these GDPR gaps:

### 1. Incomplete Deletion

**Issue:** User deletion doesn't remove data from all systems.

**Solution:** Implement comprehensive deletion across:
- Primary database
- Search indices
- Caches
- Backups
- Third-party processors

### 2. Missing Consent Records

**Issue:** Processing personal data without recorded consent.

**Solution:** Implement consent management with:
- Granular purposes
- Timestamp recording
- Easy withdrawal

### 3. Inadequate Data Inventory

**Issue:** No Article 30 records of processing activities.

**Solution:** Maintain automated processing records.

### 4. Insufficient Security

**Issue:** Missing encryption or access controls.

**Solution:** Implement Article 32 technical measures.

## Monitored Sources

ComplianceAgent monitors these GDPR sources:

| Source | URL | Type |
|--------|-----|------|
| EUR-Lex | eur-lex.europa.eu | Official text |
| EDPB | edpb.europa.eu | Guidelines |
| National DPAs | Various | Local guidance |
| CJEU | curia.europa.eu | Case law |

## Configuration

Enable GDPR compliance:

```yaml
# .complianceagent/config.yml
frameworks:
  gdpr:
    enabled: true
    
    # Jurisdictions to consider
    jurisdictions:
      - EU
      - DE  # Include German BDSG
      - FR  # Include French CNIL guidance
    
    # Categories to enable
    categories:
      - lawful_basis
      - consent
      - data_subject_rights
      - security
      - breach_notification
      - international_transfers
    
    # Thresholds
    thresholds:
      consent_issues: critical
      security_issues: high
```

## Templates

Available GDPR templates:

| Template | Description |
|----------|-------------|
| `gdpr-consent-banner` | Cookie/consent UI component |
| `gdpr-dsar-handler` | Data subject access request |
| `gdpr-deletion-handler` | Right to erasure implementation |
| `gdpr-export-handler` | Data portability export |
| `gdpr-breach-notifier` | Breach notification system |
| `gdpr-processing-records` | Art. 30 processing records |

Apply a template:

```bash
curl -X POST "http://localhost:8000/api/v1/templates/apply" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "template": "gdpr-consent-banner",
    "repository": "acme/web-app",
    "config": {
      "purposes": ["analytics", "marketing", "functional"],
      "default_language": "en",
      "supported_languages": ["en", "de", "fr"]
    }
  }'
```

## API Endpoints

GDPR-specific API endpoints:

```bash
# Get GDPR requirements
GET /api/v1/regulations/gdpr/requirements

# Get GDPR compliance status
GET /api/v1/compliance/status?framework=gdpr

# Handle DSAR
POST /api/v1/gdpr/dsar

# Record consent
POST /api/v1/gdpr/consent

# Report breach
POST /api/v1/gdpr/breach
```

---

See also: [CCPA](./ccpa) | [HIPAA](./hipaa) | [Core Concepts](../core-concepts/overview)
