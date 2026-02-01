---
sidebar_position: 6
title: Audit Trails
description: Maintain tamper-proof compliance audit records
---

# Audit Trails

ComplianceAgent maintains comprehensive, tamper-proof audit trails for compliance evidence and regulatory reporting.

## What Gets Audited

Every compliance-relevant action is recorded:

| Category | Events |
|----------|--------|
| **Assessments** | Analysis runs, gap identification, score changes |
| **Remediations** | Fix generation, PR creation, code deployments |
| **Data Access** | Repository access, report generation, exports |
| **Configuration** | Framework changes, threshold updates, user permissions |
| **Authentication** | Logins, API key usage, SSO events |

## Audit Entry Structure

Each audit entry contains:

```json
{
  "id": "aud_2024011510300042",
  "timestamp": "2024-01-15T10:30:00.042Z",
  "organization_id": "org_acme",
  "user": {
    "id": "usr_john",
    "email": "john@acme.com",
    "ip_address": "192.168.1.100"
  },
  "event": {
    "type": "compliance.gap_resolved",
    "category": "remediation",
    "severity": "info"
  },
  "resource": {
    "type": "compliance_gap",
    "id": "gap_gdpr_art17_001",
    "name": "GDPR Art. 17 - User deletion incomplete"
  },
  "details": {
    "resolution": "code_fix_merged",
    "pr_number": 142,
    "repository": "acme/backend",
    "commit": "abc123def456"
  },
  "context": {
    "framework": "GDPR",
    "requirement": "Article 17(1)",
    "before_score": 84,
    "after_score": 87
  },
  "hash": "sha256:7d4e8f9a2b1c3d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e",
  "previous_hash": "sha256:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2"
}
```

## Tamper-Proof Hash Chain

### How It Works

Each audit entry is cryptographically linked to the previous entry:

```
┌──────────────────────────────────────────────────────────────────┐
│                    Hash Chain Verification                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Entry 1              Entry 2              Entry 3                │
│  ┌─────────┐          ┌─────────┐          ┌─────────┐           │
│  │ Data    │          │ Data    │          │ Data    │           │
│  │         │          │         │          │         │           │
│  │ Hash: A │─────────▶│ Prev: A │─────────▶│ Prev: B │           │
│  │         │          │ Hash: B │          │ Hash: C │           │
│  └─────────┘          └─────────┘          └─────────┘           │
│                                                                   │
│  If any entry is modified, the chain breaks and                   │
│  verification fails.                                              │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Verification

Verify the integrity of your audit trail:

```bash
curl -X GET "http://localhost:8000/api/v1/audit/verify-chain" \
  -H "Authorization: Bearer $TOKEN"
```

Response:

```json
{
  "verified": true,
  "entries_checked": 15847,
  "first_entry": "2023-06-01T00:00:00Z",
  "last_entry": "2024-01-15T10:30:00Z",
  "chain_valid": true,
  "anomalies": []
}
```

If tampering is detected:

```json
{
  "verified": false,
  "chain_valid": false,
  "anomalies": [
    {
      "entry_id": "aud_2024010812450033",
      "issue": "hash_mismatch",
      "expected_hash": "sha256:abc...",
      "actual_hash": "sha256:def...",
      "timestamp": "2024-01-08T12:45:00Z"
    }
  ]
}
```

## Viewing Audit Logs

### Dashboard

Navigate to **Audit** in the sidebar:

```
┌──────────────────────────────────────────────────────────────────┐
│                        Audit Trail                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Filters: [All Events ▼] [Last 7 days ▼] [All Users ▼] [Search]  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 10:30 AM  Gap Resolved                           john@acme │  │
│  │           GDPR Art. 17 fixed via PR #142                   │  │
│  │           Repository: acme/backend                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 10:15 AM  Fix Generated                          system    │  │
│  │           Generated code fix for GDPR Art. 17              │  │
│  │           Confidence: 94%                                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 09:45 AM  Assessment Completed                   system    │  │
│  │           Repository: acme/backend                         │  │
│  │           Score: 84% → 3 new gaps identified               │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  [Load More]                                                      │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Filtering

Filter audit logs by:

- **Date range** - Custom or preset (24h, 7d, 30d, 90d)
- **Event type** - Assessment, remediation, access, config
- **User** - Specific user or system events
- **Resource** - Repository, framework, gap ID
- **Severity** - Info, warning, error, critical

### API Access

```bash
# Get recent audit entries
curl -X GET "http://localhost:8000/api/v1/audit?limit=100" \
  -H "Authorization: Bearer $TOKEN"

# Filter by event type
curl -X GET "http://localhost:8000/api/v1/audit?event_type=compliance.gap_resolved" \
  -H "Authorization: Bearer $TOKEN"

# Filter by date range
curl -X GET "http://localhost:8000/api/v1/audit?from=2024-01-01&to=2024-01-15" \
  -H "Authorization: Bearer $TOKEN"

# Filter by user
curl -X GET "http://localhost:8000/api/v1/audit?user_id=usr_john" \
  -H "Authorization: Bearer $TOKEN"
```

## Exporting Audit Trails

### Export Formats

| Format | Use Case |
|--------|----------|
| **JSON** | Integration with other systems |
| **CSV** | Spreadsheet analysis |
| **PDF** | Official reports for auditors |

### Dashboard Export

1. Go to **Audit**
2. Apply desired filters
3. Click **Export**
4. Select format and date range

### API Export

```bash
# Export as JSON
curl -X GET "http://localhost:8000/api/v1/audit/export?format=json&from=2024-01-01" \
  -H "Authorization: Bearer $TOKEN" \
  -o audit-export.json

# Export as CSV
curl -X GET "http://localhost:8000/api/v1/audit/export?format=csv&from=2024-01-01" \
  -H "Authorization: Bearer $TOKEN" \
  -o audit-export.csv

# Export as PDF report
curl -X GET "http://localhost:8000/api/v1/audit/export?format=pdf&from=2024-01-01" \
  -H "Authorization: Bearer $TOKEN" \
  -o audit-report.pdf
```

### Scheduled Exports

Configure automatic exports:

```yaml
# .complianceagent/config.yml
audit:
  exports:
    - name: "Weekly Audit Backup"
      schedule: "0 0 * * 0"  # Every Sunday
      format: json
      destination:
        type: s3
        bucket: acme-compliance-backups
        path: audits/
    
    - name: "Monthly Compliance Report"
      schedule: "0 9 1 * *"  # First of month
      format: pdf
      destination:
        type: email
        recipients:
          - compliance@acme.com
          - legal@acme.com
```

## Regulatory Reporting

### SOC 2 Evidence

Generate SOC 2-aligned audit evidence:

```bash
curl -X GET "http://localhost:8000/api/v1/audit/reports/soc2" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "period_start": "2024-01-01",
    "period_end": "2024-03-31",
    "controls": ["CC6.1", "CC6.7", "CC7.2"]
  }'
```

### ISO 27001 Evidence

```bash
curl -X GET "http://localhost:8000/api/v1/audit/reports/iso27001" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "period_start": "2024-01-01",
    "period_end": "2024-03-31",
    "controls": ["A.12", "A.14", "A.18"]
  }'
```

### HIPAA Audit Trail

```bash
curl -X GET "http://localhost:8000/api/v1/audit/reports/hipaa" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "period_start": "2024-01-01",
    "period_end": "2024-03-31",
    "include_access_logs": true
  }'
```

## Retention Policies

### Default Retention

| Entry Type | Retention |
|------------|-----------|
| Compliance events | 7 years |
| Access logs | 2 years |
| Configuration changes | 7 years |
| Authentication events | 1 year |

### Custom Retention

Configure per regulatory requirement:

```yaml
audit:
  retention:
    default: "7y"
    
    by_framework:
      hipaa: "6y"      # HIPAA requires 6 years
      gdpr: "7y"       # Match default
      pci_dss: "1y"    # PCI-DSS minimum
      sox: "7y"        # Sarbanes-Oxley
    
    by_event_type:
      authentication: "1y"
      access_logs: "2y"
```

### Archival

Older entries are archived but remain accessible:

```bash
# Access archived entries
curl -X GET "http://localhost:8000/api/v1/audit/archive?year=2022" \
  -H "Authorization: Bearer $TOKEN"
```

## Access Control

### Who Can View Audit Logs

| Role | Access Level |
|------|--------------|
| Admin | Full access |
| Compliance Officer | Full access |
| Developer | Own actions only |
| Viewer | No audit access |

### Audit Access is Audited

Access to audit logs is itself recorded:

```json
{
  "event": {
    "type": "audit.accessed",
    "category": "access"
  },
  "details": {
    "query_filters": {
      "date_from": "2024-01-01",
      "event_type": "compliance.*"
    },
    "entries_returned": 150
  }
}
```

## Integration

### SIEM Integration

Forward audit logs to your SIEM:

```yaml
audit:
  forwarding:
    - type: syslog
      host: siem.acme.com
      port: 514
      format: cef
    
    - type: webhook
      url: https://siem.acme.com/api/events
      headers:
        Authorization: "Bearer ${SIEM_TOKEN}"
```

### Splunk Integration

```yaml
audit:
  forwarding:
    - type: splunk
      hec_url: https://splunk.acme.com:8088
      token: "${SPLUNK_HEC_TOKEN}"
      index: compliance_audit
```

### Elasticsearch/OpenSearch

```yaml
audit:
  forwarding:
    - type: elasticsearch
      url: https://es.acme.com:9243
      index: complianceagent-audit
      credentials:
        username: "${ES_USER}"
        password: "${ES_PASS}"
```

---

Next: Learn about [Evidence Collection](./evidence-collection) for audit preparation.
