# Colorado CPA Compliance Guide

This guide covers how ComplianceAgent helps you achieve compliance with the Colorado Privacy Act (CPA).

## Overview

| Attribute | Value |
|-----------|-------|
| **Full Name** | Colorado Privacy Act |
| **Jurisdiction** | Colorado, USA |
| **Effective Date** | July 1, 2023 |
| **Enforcing Authority** | Colorado Attorney General |
| **Max Penalty** | $20,000 per violation (up to $500,000 per action) |

### Applicability

The Colorado CPA applies to entities that:
- Conduct business in Colorado or target Colorado residents
- Control or process personal data of ≥100,000 consumers per year, OR
- Control or process data of ≥25,000 consumers and derive revenue from data sales

## Key Requirements

### Consumer Rights

| Right | Description | Code Impact |
|-------|-------------|-------------|
| **Access** | Right to confirm and access personal data | Data export endpoint |
| **Correction** | Right to correct inaccuracies | Edit functionality |
| **Deletion** | Right to delete personal data | Delete endpoint, cascade deletion |
| **Portability** | Right to obtain data in portable format | JSON/CSV export |
| **Opt-Out** | Right to opt out of targeted advertising, data sales, and profiling | Preference management |

### Universal Opt-Out Mechanism

The CPA uniquely requires controllers to recognize **universal opt-out signals** (e.g., Global Privacy Control):

- Must honor browser-based opt-out signals
- Cannot require consumers to submit individual requests
- Must be implemented by July 1, 2024

### Data Protection Assessments

Required for processing activities involving:
- Targeted advertising
- Sale of personal data
- Certain profiling activities
- Processing sensitive data

## ComplianceAgent Detection

### Automatically Detected Issues

```
CPA-001: Missing consumer data access mechanism
CPA-002: No universal opt-out signal recognition
CPA-003: Sensitive data processed without explicit consent
CPA-004: Missing data protection assessment
CPA-005: Inadequate data deletion implementation
CPA-006: No privacy notice or insufficient disclosures
CPA-007: Missing data portability export
CPA-008: Opt-out mechanism not implemented
```

### Example Detection

**Issue: CPA-002 - Missing universal opt-out recognition**

```python
# ❌ Non-compliant: Ignoring Global Privacy Control signal
def track_user(request, user_id: str):
    set_tracking_cookie(user_id)
    send_to_ad_network(user_id, request.url)

# ✅ Compliant: Honoring universal opt-out signal
def track_user(request, user_id: str):
    gpc_header = request.headers.get("Sec-GPC", "0")
    if gpc_header == "1":
        log_opt_out(user_id, source="global_privacy_control")
        return  # Respect universal opt-out
    if not has_consent(user_id, purpose="targeted_advertising"):
        return
    set_tracking_cookie(user_id)
    send_to_ad_network(user_id, request.url)
```

## Configuration

```yaml
# complianceagent.yml
regulations:
  colorado-cpa:
    enabled: true
    severity: high
    rules:
      cpa-check-consumer-rights: true
      cpa-check-universal-opt-out: true
      cpa-check-consent: true
      cpa-check-data-assessment: true
      cpa-check-processor-agreements: true
```

## Resources

- [Colorado CPA Full Text](https://leg.colorado.gov/bills/sb21-190)
- [Colorado AG Privacy Resources](https://coag.gov/resources/data-protection/)

## Related Frameworks

- [CCPA/CPRA](ccpa.md) - California privacy law
- [Virginia VCDPA](vcdpa.md) - Virginia privacy law
- [GDPR](gdpr.md) - EU data protection regulation
