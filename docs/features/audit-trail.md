# Audit Trail

The Audit Trail provides a tamper-proof, cryptographically verified record of all compliance-related events within ComplianceAgent.

## Overview

| Attribute | Value |
|-----------|-------|
| **Purpose** | Immutable compliance event logging |
| **Integrity** | SHA-256 hash-chain verification |
| **Storage** | Evidence Vault with per-framework chains |
| **Access** | API, Dashboard, Auditor Portal |

ComplianceAgent maintains two complementary audit mechanisms:

1. **Audit Trail** — Chronological log of all compliance events (assessments, fixes, policy changes) linked via hash chain
2. **Evidence Vault** — Immutable evidence storage with per-framework chains for certification readiness

## Hash-Chain Verification

Every audit entry is linked to the previous entry using a SHA-256 hash chain, making tampering detectable.

### How It Works

1. Each new audit entry captures: organization, event type, description, event data, regulation, actor, and timestamp
2. The `previous_hash` field links to the prior entry's hash
3. A SHA-256 digest is computed over the entry data plus the previous hash
4. Any modification to a historical entry breaks the chain from that point forward

```
Entry N-1                     Entry N                       Entry N+1
┌──────────────┐              ┌──────────────┐              ┌──────────────┐
│ event_data   │              │ event_data   │              │ event_data   │
│ previous_hash│──────────┐   │ previous_hash│──────────┐   │ previous_hash│
│ entry_hash ──┼──────────┼──▶│ entry_hash ──┼──────────┼──▶│ entry_hash   │
└──────────────┘          │   └──────────────┘          │   └──────────────┘
                          │                              │
                    SHA-256(data + prev)           SHA-256(data + prev)
```

### Verifying Chain Integrity

Use the verify-chain endpoint to validate the entire audit history:

```http
GET /api/v1/audit/verify-chain
Authorization: Bearer <token>
```

**Response:**
```json
{
    "valid": true,
    "entries_checked": 1247,
    "invalid_entries": []
}
```

If tampering is detected, `valid` will be `false` and `invalid_entries` will list the affected entry IDs.

## Evidence Vault Integration

The Evidence Vault extends the audit trail with structured, per-framework evidence storage designed for certification workflows.

### Storing Evidence

```http
POST /api/v1/evidence-vault/evidence
Content-Type: application/json
Authorization: Bearer <token>

{
    "framework": "soc2",
    "control_id": "CC6.1",
    "evidence_type": "automated_scan",
    "content": "Encryption verification scan results...",
    "metadata": {
        "scanner": "complianceagent",
        "repository": "org/backend-api"
    }
}
```

Each piece of evidence is hash-chained within its framework, creating independent verifiable chains per compliance framework (SOC 2, ISO 27001, HIPAA, etc.).

### Verifying Evidence Chain

```http
GET /api/v1/evidence-vault/verify/{framework}
Authorization: Bearer <token>
```

**Response:**
```json
{
    "framework": "soc2",
    "verified": true
}
```

### Auditor Portal Access

External auditors can receive read-only access to evidence chains:

```http
POST /api/v1/evidence-vault/auditor-sessions
Content-Type: application/json
Authorization: Bearer <token>

{
    "auditor_email": "auditor@firm.com",
    "frameworks": ["soc2", "iso27001"],
    "expires_in_days": 30
}
```

## API Reference

### Audit Trail Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/audit/` | GET | List audit trail entries (filterable) |
| `/api/v1/audit/trail/{entry_id}` | GET | Get specific audit entry |
| `/api/v1/audit/verify-chain` | GET | Verify hash chain integrity |
| `/api/v1/audit/export` | GET | Export audit report |

### Evidence Vault Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/evidence-vault/evidence` | POST | Store compliance evidence |
| `/api/v1/evidence-vault/evidence` | GET | Query evidence with filters |
| `/api/v1/evidence-vault/verify/{framework}` | GET | Verify framework evidence chain |
| `/api/v1/evidence-vault/controls/{framework}` | GET | Get control mappings |
| `/api/v1/evidence-vault/auditor-sessions` | POST | Create auditor portal session |

### Query Parameters

The audit trail list endpoint supports these filters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `regulation_id` | UUID | Filter by regulation |
| `requirement_id` | UUID | Filter by requirement |
| `event_type` | string | Filter by event type |
| `start_date` | datetime | Filter from date |
| `end_date` | datetime | Filter until date |

## Event Types

| Event Type | Description |
|------------|-------------|
| `compliance_scan` | Automated compliance analysis completed |
| `fix_applied` | Compliance fix applied to codebase |
| `policy_change` | Compliance policy created or modified |
| `assessment` | Manual compliance assessment recorded |
| `violation_detected` | Compliance violation identified |
| `remediation` | Remediation action taken |
| `certification_milestone` | Certification checkpoint reached |

## Best Practices

1. **Regular verification** — Run chain verification on a schedule to detect issues early
2. **Export before audits** — Generate audit reports ahead of certification reviews
3. **Auditor sessions** — Use time-limited read-only sessions rather than sharing credentials
4. **Evidence tagging** — Include rich metadata when storing evidence for easier retrieval

## Related Documentation

- [SOC 2 Compliance](../frameworks/soc2.md)
- [ISO 27001 Compliance](../frameworks/iso27001.md)
- [FERPA Compliance](../frameworks/ferpa.md)
- [Security Best Practices](../guides/security.md)
- [API Reference](../api/reference.md)
