# HITRUST CSF Compliance Guide

This guide covers how ComplianceAgent helps you achieve compliance with the HITRUST Common Security Framework (CSF).

## Overview

| Attribute | Value |
|-----------|-------|
| **Full Name** | HITRUST Common Security Framework |
| **Jurisdiction** | United States (primarily healthcare) |
| **Current Version** | HITRUST CSF v11 |
| **Certification Body** | HITRUST Alliance |
| **Certification Validity** | 2 years (r2 Validated Assessment) |

### What is HITRUST?

HITRUST CSF is a certifiable security framework that harmonizes requirements from multiple regulations and standards including HIPAA, NIST, ISO 27001, PCI-DSS, and GDPR. It provides a prescriptive, risk-based approach to security and compliance, particularly valued in healthcare and industries handling sensitive data.

### Assessment Types

| Assessment | Description | Duration |
|------------|-------------|----------|
| **e1** | Essential, foundational cybersecurity (44 requirements) | ~3 months |
| **i1** | Implemented, leading security practices (182 requirements) | ~6 months |
| **r2** | Risk-based, comprehensive (custom scope, 500+ requirements) | ~9-12 months |

## Key Control Domains

### Control Categories

| Domain | Description | Code Impact |
|--------|-------------|-------------|
| **Access Control** | User authentication, authorization, MFA | Auth modules, RBAC |
| **Audit Logging** | Event logging, monitoring, chain of custody | Audit trail, SIEM integration |
| **Data Protection** | Encryption at rest and in transit | TLS, AES-256, key management |
| **Incident Management** | Detection, response, notification | Alerting, runbooks |
| **Risk Management** | Assessment, mitigation, monitoring | Risk scoring, dashboards |
| **Vulnerability Management** | Scanning, patching, remediation | CI/CD security gates |
| **Network Protection** | Segmentation, firewalls, monitoring | Infrastructure config |

### Mapping to Other Frameworks

HITRUST CSF maps controls to multiple standards:

| HITRUST Control | HIPAA | ISO 27001 | NIST CSF | PCI-DSS |
|-----------------|-------|-----------|----------|---------|
| Access Control | §164.312(a) | A.9 | PR.AC | Req 7-8 |
| Audit Logging | §164.312(b) | A.12.4 | DE.AE | Req 10 |
| Encryption | §164.312(a)(2)(iv) | A.10 | PR.DS | Req 3-4 |
| Incident Response | §164.308(a)(6) | A.16 | RS.RP | Req 12.10 |

## ComplianceAgent Detection

### Automatically Detected Issues

```
HITRUST-001: Missing multi-factor authentication
HITRUST-002: Insufficient audit logging coverage
HITRUST-003: Data not encrypted at rest
HITRUST-004: Missing vulnerability scanning in CI/CD
HITRUST-005: Incomplete incident response procedures
HITRUST-006: Access reviews not implemented
HITRUST-007: Missing data classification tagging
HITRUST-008: Inadequate session management controls
HITRUST-009: Missing security awareness training tracking
HITRUST-010: Backup and recovery procedures not documented
```

### Example Detection

**Issue: HITRUST-002 - Insufficient audit logging**

```python
# ❌ Non-compliant: No audit logging on data access
def get_patient_record(patient_id: str):
    return db.query(Patient).filter_by(id=patient_id).first()

# ✅ Compliant: Full audit trail on sensitive data access
def get_patient_record(patient_id: str, requesting_user: str):
    record = db.query(Patient).filter_by(id=patient_id).first()
    audit_log.record(
        event_type="phi_access",
        resource_id=patient_id,
        actor=requesting_user,
        action="read",
        outcome="success" if record else "not_found",
    )
    return record
```

## Configuration

```yaml
# complianceagent.yml
regulations:
  hitrust:
    enabled: true
    severity: high
    assessment_type: r2  # e1, i1, or r2
    rules:
      hitrust-check-access-control: true
      hitrust-check-audit-logging: true
      hitrust-check-encryption: true
      hitrust-check-vulnerability-mgmt: true
      hitrust-check-incident-response: true
      hitrust-check-data-classification: true
```

## Resources

- [HITRUST Alliance](https://hitrustalliance.net/)
- [HITRUST CSF Overview](https://hitrustalliance.net/hitrust-csf/)
- [HITRUST Assessment Handbook](https://hitrustalliance.net/resources/)

## Related Frameworks

- [HIPAA](hipaa.md) - Healthcare privacy and security (HITRUST primary mapping)
- [ISO 27001](iso27001.md) - Information security management system
- [SOC 2](soc2.md) - Security controls audit framework
- [Audit Trail Feature](../features/audit-trail.md)
