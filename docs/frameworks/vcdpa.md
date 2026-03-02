# Virginia VCDPA Compliance Guide

This guide covers how ComplianceAgent helps you achieve compliance with the Virginia Consumer Data Protection Act (VCDPA).

## Overview

| Attribute | Value |
|-----------|-------|
| **Full Name** | Virginia Consumer Data Protection Act |
| **Jurisdiction** | Virginia, USA |
| **Effective Date** | January 1, 2023 |
| **Enforcing Authority** | Virginia Attorney General |
| **Max Penalty** | $7,500 per violation |

### Applicability

The VCDPA applies to entities that:
- Conduct business in Virginia or target Virginia residents
- Control or process personal data of ≥100,000 consumers, OR
- Control or process data of ≥25,000 consumers and derive >50% of revenue from data sales

## Key Requirements

### Consumer Rights

| Right | Description | Code Impact |
|-------|-------------|-------------|
| **Access** | Right to confirm and access personal data | Data export endpoint |
| **Correction** | Right to correct inaccuracies | Edit functionality |
| **Deletion** | Right to delete personal data | Delete endpoint, cascade deletion |
| **Portability** | Right to obtain data in portable format | JSON/CSV export |
| **Opt-Out** | Right to opt out of data sales and targeted advertising | Preference management |

### Data Protection Assessments

Controllers must conduct data protection assessments for:
- Targeted advertising
- Sale of personal data
- Profiling with significant effects
- Processing sensitive data
- Any processing presenting heightened risk

### Consent Requirements

- **Sensitive data** requires opt-in consent (racial/ethnic origin, health, biometric, geolocation, child data)
- **Data sales** require clear opt-out mechanism
- **Targeted advertising** requires opt-out mechanism

## ComplianceAgent Detection

### Automatically Detected Issues

```
VCDPA-001: Missing consumer data access mechanism
VCDPA-002: No opt-out mechanism for data sales
VCDPA-003: Sensitive data processed without explicit consent
VCDPA-004: Missing data protection assessment
VCDPA-005: Inadequate data deletion implementation
VCDPA-006: No privacy notice or insufficient disclosures
VCDPA-007: Missing data portability export
VCDPA-008: Third-party processor agreement gaps
```

### Example Detection

**Issue: VCDPA-003 - Sensitive data without consent**

```python
# ❌ Non-compliant: Processing biometric data without consent
def enroll_face_recognition(user_id: str, face_data: bytes):
    store_biometric(user_id, face_data)

# ✅ Compliant: Explicit consent before processing
def enroll_face_recognition(user_id: str, face_data: bytes):
    consent = get_user_consent(user_id, purpose="biometric_enrollment")
    if not consent or not consent.is_valid():
        raise ConsentRequiredError("Biometric consent required under VCDPA")
    store_biometric(user_id, face_data)
    log_consent_record(user_id, consent)
```

## Configuration

```yaml
# complianceagent.yml
regulations:
  vcdpa:
    enabled: true
    severity: high
    rules:
      vcdpa-check-consumer-rights: true
      vcdpa-check-consent: true
      vcdpa-check-opt-out: true
      vcdpa-check-data-assessment: true
      vcdpa-check-processor-agreements: true
```

## Resources

- [VCDPA Full Text](https://law.lis.virginia.gov/vacodefull/title59.1/chapter53/)
- [Virginia AG Consumer Protection](https://www.oag.state.va.us/consumer-protection/index.php/file-a-complaint)

## Related Frameworks

- [CCPA/CPRA](ccpa.md) - California privacy law (broader scope)
- [Colorado CPA](colorado-cpa.md) - Colorado privacy law
- [GDPR](gdpr.md) - EU data protection regulation
