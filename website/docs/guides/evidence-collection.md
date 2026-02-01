---
sidebar_position: 7
title: Evidence Collection
description: Automatically collect compliance evidence for audits
---

# Evidence Collection

ComplianceAgent automatically collects and organizes evidence for SOC 2, ISO 27001, HIPAA, PCI-DSS, and other compliance audits.

## How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│                   Evidence Collection Pipeline                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Sources                     Processing              Output       │
│  ─────────                   ──────────              ──────       │
│                                                                   │
│  ┌─────────────┐            ┌─────────────┐        ┌──────────┐  │
│  │ Code        │────────────│   Map to    │────────│ Evidence │  │
│  │ Analysis    │            │  Controls   │        │ Library  │  │
│  └─────────────┘            └─────────────┘        └──────────┘  │
│                                   │                     │        │
│  ┌─────────────┐                  │                     ▼        │
│  │ Audit       │──────────────────┤            ┌──────────────┐  │
│  │ Trail       │                  │            │ Audit Report │  │
│  └─────────────┘                  │            │   Generator  │  │
│                                   │            └──────────────┘  │
│  ┌─────────────┐                  │                              │
│  │ Config      │──────────────────┘                              │
│  │ Scanning    │                                                 │
│  └─────────────┘                                                 │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Supported Frameworks

| Framework | Coverage | Auto-Collection |
|-----------|----------|-----------------|
| **SOC 2 Type II** | All Trust Services Criteria | ✅ Full |
| **ISO 27001:2022** | Annex A controls | ✅ Full |
| **HIPAA** | Security Rule, Privacy Rule | ✅ Full |
| **PCI-DSS v4.0** | All requirements | ✅ Full |
| **NIST CSF** | All functions | ✅ Full |
| **GDPR** | Art. 30 requirements | ✅ Full |

## Configuring Evidence Collection

### Enable for Your Organization

1. Go to **Settings → Evidence Collection**
2. Select compliance frameworks
3. Map repositories to controls
4. Configure collection frequency

### Configuration File

```yaml
# .complianceagent/evidence.yml
evidence:
  enabled: true
  frameworks:
    - soc2
    - iso27001
    - hipaa
  
  collection:
    # How often to collect evidence
    frequency: daily
    
    # What to include
    sources:
      - code_analysis
      - audit_trail
      - configuration
      - access_logs
    
    # Control mappings
    mappings:
      soc2:
        CC6.1:  # Logical and Physical Access
          repositories:
            - acme/auth-service
            - acme/api-gateway
          evidence_types:
            - access_control_config
            - authentication_logs
            - mfa_enforcement
        
        CC6.7:  # Data Integrity
          repositories:
            - acme/backend
          evidence_types:
            - encryption_config
            - integrity_checks
```

## Control Mapping

### SOC 2 Trust Services Criteria

ComplianceAgent maps code to SOC 2 controls:

```
┌──────────────────────────────────────────────────────────────────┐
│              SOC 2 Control Mapping: CC6.1                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Control: Logical and Physical Access Controls                    │
│                                                                   │
│  Evidence Collected:                                              │
│                                                                   │
│  ✅ Access Control Implementation                                 │
│     └── src/auth/rbac.py - Role-based access control             │
│     └── src/middleware/auth.py - JWT validation                  │
│                                                                   │
│  ✅ MFA Enforcement                                               │
│     └── src/auth/mfa.py - TOTP implementation                    │
│     └── Config: MFA required for admin roles                     │
│                                                                   │
│  ✅ Access Logs                                                   │
│     └── 15,847 authentication events (last 90 days)              │
│     └── 0 unauthorized access attempts                           │
│                                                                   │
│  ✅ User Provisioning                                             │
│     └── SCIM integration enabled                                 │
│     └── 23 users provisioned via SSO                             │
│                                                                   │
│  Coverage: 100%                                                   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### ISO 27001 Annex A

```yaml
# Automatic mapping to ISO 27001 controls
iso27001:
  A.9.2.3:  # Management of privileged access rights
    evidence:
      - admin_role_assignments
      - privilege_escalation_logs
      - access_reviews
    
  A.12.3.1:  # Information backup
    evidence:
      - backup_configuration
      - backup_execution_logs
      - restoration_tests
    
  A.14.2.5:  # Secure system engineering principles
    evidence:
      - security_code_reviews
      - dependency_scanning
      - penetration_test_results
```

## Evidence Types

### Code-Based Evidence

Evidence derived from code analysis:

| Evidence Type | Description | Example |
|---------------|-------------|---------|
| Encryption Implementation | Cryptographic functions | `AES-256 encryption in crypto.py` |
| Access Controls | RBAC/ABAC implementation | `Permission checks in middleware` |
| Input Validation | Sanitization functions | `Input validation in validators.py` |
| Audit Logging | Logging implementation | `Audit events in audit_service.py` |
| Error Handling | Exception handling | `Secure error responses` |

### Configuration Evidence

Evidence from infrastructure configuration:

```json
{
  "control": "CC6.7",
  "evidence_type": "encryption_config",
  "collected_at": "2024-01-15T00:00:00Z",
  "source": "terraform/main.tf",
  "findings": {
    "rds_encryption": true,
    "s3_encryption": "AES256",
    "kms_key_rotation": true,
    "tls_version": "1.3"
  }
}
```

### Operational Evidence

Evidence from runtime operations:

- Authentication logs
- Access control events
- Change management records
- Incident response records

## Evidence Library

### Dashboard View

Navigate to **Evidence** in the sidebar:

```
┌──────────────────────────────────────────────────────────────────┐
│                      Evidence Library                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Framework: [SOC 2 ▼]    Period: [Q1 2024 ▼]    [Export Report]  │
│                                                                   │
│  Trust Services Criteria              Coverage    Evidence        │
│  ────────────────────────             ────────    ────────        │
│  CC1 - Control Environment            95%         47 items        │
│  CC2 - Communication & Information    100%        23 items        │
│  CC3 - Risk Assessment                88%         15 items        │
│  CC4 - Monitoring Activities          100%        31 items        │
│  CC5 - Control Activities             92%         89 items        │
│  CC6 - Logical & Physical Access      100%        112 items       │
│  CC7 - System Operations              96%         67 items        │
│  CC8 - Change Management              100%        45 items        │
│  CC9 - Risk Mitigation                90%         28 items        │
│                                                                   │
│  Overall Coverage: 96%                Total: 457 evidence items   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Control Detail View

Click on a control to see collected evidence:

```
┌──────────────────────────────────────────────────────────────────┐
│              CC6.1 - Logical & Physical Access                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Evidence Items (24)                                              │
│                                                                   │
│  📄 Access Control Policy                                         │
│     Type: Policy Document                                         │
│     Source: Confluence                                            │
│     Last Updated: 2024-01-10                                      │
│     [View] [Download]                                             │
│                                                                   │
│  💻 RBAC Implementation                                           │
│     Type: Code Analysis                                           │
│     Source: acme/auth-service                                     │
│     Files: 12 files analyzed                                      │
│     [View Details]                                                │
│                                                                   │
│  📊 Authentication Logs Summary                                   │
│     Type: Operational Logs                                        │
│     Period: Last 90 days                                          │
│     Events: 15,847 successful, 23 failed                          │
│     [View Logs] [Download]                                        │
│                                                                   │
│  ✅ Access Review Records                                         │
│     Type: Review Evidence                                         │
│     Last Review: 2024-01-05                                       │
│     Reviewed By: john@acme.com                                    │
│     [View Details]                                                │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Generating Audit Reports

### Pre-Built Reports

Generate framework-specific reports:

```bash
# SOC 2 Type II Report
curl -X POST "http://localhost:8000/api/v1/evidence/reports" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "framework": "soc2",
    "period_start": "2024-01-01",
    "period_end": "2024-03-31",
    "format": "pdf"
  }'
```

### Report Contents

Generated reports include:

1. **Executive Summary** - Overall compliance status
2. **Control Matrix** - All controls with evidence mapping
3. **Evidence Inventory** - List of all collected evidence
4. **Gap Analysis** - Any missing or weak evidence
5. **Recommendations** - Steps to improve coverage

### Custom Reports

Create custom report templates:

```yaml
# .complianceagent/report-templates/quarterly-audit.yml
name: Quarterly Audit Report
sections:
  - title: Executive Summary
    include:
      - compliance_score
      - key_findings
      - recommendations
  
  - title: Control Coverage
    controls:
      - CC6.*
      - CC7.*
    include:
      - evidence_count
      - coverage_percentage
  
  - title: Evidence Details
    evidence_types:
      - code_analysis
      - configuration
    max_items_per_control: 10
  
  - title: Audit Trail
    events:
      - compliance.*
      - access.*
    period: last_90_days
```

## Continuous Monitoring

### Evidence Freshness

Track when evidence was last collected:

```
┌──────────────────────────────────────────────────────────────────┐
│                    Evidence Freshness                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  🟢 Fresh (< 7 days)     286 items (63%)                         │
│  🟡 Aging (7-30 days)    142 items (31%)                         │
│  🔴 Stale (> 30 days)     29 items (6%)                          │
│                                                                   │
│  Stale Evidence:                                                  │
│  ⚠️ CC3.1 - Risk assessment documentation - 45 days old          │
│  ⚠️ CC5.2 - Vendor security reviews - 38 days old               │
│                                                                   │
│  [Trigger Re-collection] [Review Stale Items]                     │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Alerts

Configure alerts for evidence gaps:

```yaml
evidence:
  alerts:
    - name: "Stale Evidence Alert"
      condition: "evidence_age > 30d"
      severity: warning
      channels:
        - email: compliance@acme.com
        - slack: "#compliance"
    
    - name: "Coverage Drop Alert"
      condition: "coverage < 90%"
      severity: critical
      channels:
        - email: cto@acme.com
```

## Working with Auditors

### Auditor Access

Grant auditors limited access:

1. Go to **Settings → Team → Invite**
2. Select role: **Auditor**
3. Auditor receives read-only access to:
   - Evidence library
   - Audit reports
   - Relevant audit trail entries

### Evidence Request Workflow

When auditors request additional evidence:

```
┌──────────────────────────────────────────────────────────────────┐
│                    Evidence Request                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  From: External Auditor (EY)                                      │
│  Control: CC6.7 - Data Integrity                                  │
│                                                                   │
│  Request:                                                         │
│  "Please provide evidence of encryption key rotation              │
│  procedures and execution logs for the audit period."             │
│                                                                   │
│  Matching Evidence:                                               │
│  ✅ KMS Key Rotation Config (terraform/kms.tf)                   │
│  ✅ Key Rotation Logs (AWS CloudTrail, 12 events)                │
│  ✅ Key Management Policy (policy-doc-km-001)                    │
│                                                                   │
│  [Package & Send] [Request More Details]                          │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## API Reference

### List Evidence

```bash
curl -X GET "http://localhost:8000/api/v1/evidence?framework=soc2&control=CC6.1" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Evidence Item

```bash
curl -X GET "http://localhost:8000/api/v1/evidence/{evidence_id}" \
  -H "Authorization: Bearer $TOKEN"
```

### Trigger Collection

```bash
curl -X POST "http://localhost:8000/api/v1/evidence/collect" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "framework": "soc2",
    "controls": ["CC6.1", "CC6.7"],
    "force_refresh": true
  }'
```

### Upload Manual Evidence

```bash
curl -X POST "http://localhost:8000/api/v1/evidence/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@policy-document.pdf" \
  -F "framework=soc2" \
  -F "control=CC1.1" \
  -F "description=Information Security Policy v2.0"
```

---

You've completed the Guides section. Continue to [Frameworks](../frameworks/overview) for framework-specific documentation.
