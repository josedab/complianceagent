---
sidebar_position: 6
title: Audit API
description: API endpoints for audit logs and evidence
---

# Audit API

Access audit logs, export evidence packages, and manage compliance history.

## Get Audit Logs

```bash
GET /api/v1/audit/logs
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `repository_id` | string | Filter by repository |
| `event_type` | string | Filter by event type |
| `actor` | string | Filter by actor (user or system) |
| `from` | datetime | Start date |
| `to` | datetime | End date |
| `page` | integer | Page number |
| `limit` | integer | Results per page |

### Event Types

| Type | Description |
|------|-------------|
| `scan.started` | Compliance scan started |
| `scan.completed` | Compliance scan completed |
| `issue.created` | New issue detected |
| `issue.updated` | Issue status changed |
| `issue.resolved` | Issue marked resolved |
| `fix.generated` | AI fix generated |
| `fix.applied` | Fix applied to repository |
| `config.changed` | Configuration changed |
| `access.granted` | User access granted |
| `access.revoked` | User access revoked |

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "log_abc123",
      "event_type": "issue.resolved",
      "actor": {
        "type": "user",
        "id": "user_123",
        "email": "dev@acme.com"
      },
      "resource": {
        "type": "issue",
        "id": "issue_456",
        "name": "Missing encryption for PII"
      },
      "repository": {
        "id": "repo_789",
        "name": "acme/web-app"
      },
      "details": {
        "previous_status": "open",
        "new_status": "fixed",
        "fix_method": "pull_request",
        "pr_number": 456
      },
      "ip_address": "203.0.113.1",
      "user_agent": "Mozilla/5.0...",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 1523
  }
}
```

## Get Single Log Entry

```bash
GET /api/v1/audit/logs/{log_id}
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "log_abc123",
    "event_type": "fix.applied",
    "actor": {
      "type": "user",
      "id": "user_123",
      "email": "dev@acme.com",
      "name": "Alice Developer"
    },
    "resource": {
      "type": "fix",
      "id": "fix_789",
      "issue_id": "issue_456"
    },
    "repository": {
      "id": "repo_789",
      "name": "acme/web-app"
    },
    "details": {
      "fix_type": "encryption",
      "files_changed": [
        "src/models/user.py",
        "src/utils/encryption.py"
      ],
      "pull_request": {
        "url": "https://github.com/acme/web-app/pull/456",
        "number": 456
      },
      "framework": "gdpr",
      "requirement": "art_32"
    },
    "metadata": {
      "ip_address": "203.0.113.1",
      "user_agent": "Mozilla/5.0...",
      "session_id": "sess_abc123",
      "request_id": "req_xyz789"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "hash": "sha256:abc123def456...",
    "previous_hash": "sha256:xyz789ghi012..."
  }
}
```

## Export Evidence Package

```bash
POST /api/v1/audit/evidence/export
```

### Request Body

```json
{
  "format": "zip",
  "framework": "soc2",
  "audit_period": {
    "from": "2024-01-01",
    "to": "2024-03-31"
  },
  "include": [
    "compliance_reports",
    "scan_results",
    "issue_history",
    "fix_records",
    "access_logs",
    "configuration_history"
  ],
  "repository_ids": ["repo_123", "repo_456"]
}
```

### Response

```json
{
  "success": true,
  "data": {
    "job_id": "export_abc123",
    "status": "processing",
    "estimated_size_mb": 245,
    "estimated_completion": "2024-01-15T11:00:00Z"
  }
}
```

## Get Export Status

```bash
GET /api/v1/audit/evidence/export/{job_id}
```

### Response

```json
{
  "success": true,
  "data": {
    "job_id": "export_abc123",
    "status": "completed",
    "download_url": "https://exports.complianceagent.io/export_abc123.zip",
    "expires_at": "2024-01-22T11:00:00Z",
    "file_size_mb": 243,
    "files_included": 1547,
    "created_at": "2024-01-15T10:45:00Z",
    "completed_at": "2024-01-15T10:58:00Z"
  }
}
```

## Get Compliance History

```bash
GET /api/v1/audit/history
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `repository_id` | string | Filter by repository |
| `framework` | string | Filter by framework |
| `metric` | string | Metric type: `score`, `issues`, `fixes` |
| `from` | datetime | Start date |
| `to` | datetime | End date |
| `interval` | string | Data interval: `day`, `week`, `month` |

### Response

```json
{
  "success": true,
  "data": {
    "metric": "score",
    "interval": "week",
    "data_points": [
      {
        "period_start": "2024-01-01",
        "period_end": "2024-01-07",
        "value": 78,
        "change": null
      },
      {
        "period_start": "2024-01-08",
        "period_end": "2024-01-14",
        "value": 82,
        "change": 4
      },
      {
        "period_start": "2024-01-15",
        "period_end": "2024-01-21",
        "value": 85,
        "change": 3
      }
    ],
    "summary": {
      "start_value": 78,
      "end_value": 85,
      "total_change": 7,
      "trend": "improving"
    }
  }
}
```

## Verify Audit Log Integrity

```bash
POST /api/v1/audit/verify
```

### Request Body

```json
{
  "from": "2024-01-01T00:00:00Z",
  "to": "2024-01-15T23:59:59Z",
  "repository_id": "repo_123"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "verified": true,
    "logs_checked": 1523,
    "chain_valid": true,
    "hash_mismatches": 0,
    "gaps_detected": 0,
    "verification_hash": "sha256:abc123...",
    "verified_at": "2024-01-15T12:00:00Z"
  }
}
```

## Get Audit Statistics

```bash
GET /api/v1/audit/statistics
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `from` | datetime | Start date |
| `to` | datetime | End date |

### Response

```json
{
  "success": true,
  "data": {
    "period": {
      "from": "2024-01-01T00:00:00Z",
      "to": "2024-01-15T23:59:59Z"
    },
    "total_events": 4523,
    "events_by_type": {
      "scan.completed": 45,
      "issue.created": 127,
      "issue.resolved": 89,
      "fix.generated": 76,
      "fix.applied": 52
    },
    "events_by_repository": {
      "acme/web-app": 2341,
      "acme/api": 1245,
      "acme/mobile": 937
    },
    "events_by_actor_type": {
      "user": 1823,
      "system": 2700
    },
    "top_actors": [
      {
        "actor": "dev@acme.com",
        "event_count": 234
      },
      {
        "actor": "security@acme.com",
        "event_count": 189
      }
    ]
  }
}
```

## Search Audit Logs

```bash
GET /api/v1/audit/search
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search query |
| `fields` | string | Fields to search: `all`, `details`, `actor` |

### Response

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "log_abc123",
        "event_type": "fix.applied",
        "highlight": "...encryption for <em>PII</em> fields...",
        "score": 0.95,
        "timestamp": "2024-01-15T10:30:00Z"
      }
    ],
    "total": 12
  }
}
```

## Get Retention Policy

```bash
GET /api/v1/audit/retention
```

### Response

```json
{
  "success": true,
  "data": {
    "policy": {
      "audit_logs": {
        "retention_days": 2555,
        "archive_after_days": 365
      },
      "scan_results": {
        "retention_days": 730,
        "archive_after_days": 180
      },
      "evidence_exports": {
        "retention_days": 30
      }
    },
    "storage_used_gb": 12.5,
    "oldest_log": "2021-01-15T00:00:00Z"
  }
}
```

## Framework-Specific Evidence

### SOC 2 Evidence

```bash
GET /api/v1/audit/evidence/soc2
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `criteria` | string | SOC 2 criteria: `CC6.1`, `CC7.2`, etc. |
| `audit_period_start` | date | Audit period start |
| `audit_period_end` | date | Audit period end |

### Response

```json
{
  "success": true,
  "data": {
    "criteria": "CC6.1",
    "evidence_items": [
      {
        "id": "ev_123",
        "type": "access_review",
        "title": "Quarterly Access Review - Q4 2023",
        "description": "Review of user access permissions",
        "date": "2023-12-15",
        "artifacts": [
          {
            "name": "access_review_q4_2023.pdf",
            "url": "/evidence/download/ev_123_artifact_1"
          }
        ]
      },
      {
        "id": "ev_124",
        "type": "access_log",
        "title": "Authentication Logs",
        "description": "Aggregated authentication events",
        "date_range": {
          "from": "2023-10-01",
          "to": "2023-12-31"
        },
        "record_count": 45234
      }
    ]
  }
}
```

---

See also: [Compliance API](./compliance) | [Evidence Collection Guide](../guides/evidence-collection)
