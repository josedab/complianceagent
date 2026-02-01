---
sidebar_position: 4
title: Repositories API
description: API endpoints for repository management
---

# Repositories API

Connect and manage code repositories for compliance scanning.

## List Repositories

```bash
GET /api/v1/repositories
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `active`, `scanning`, `paused`, `error` |
| `provider` | string | Filter by provider: `github`, `gitlab`, `bitbucket`, `azure` |
| `page` | integer | Page number |
| `limit` | integer | Results per page |

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "repo_abc123",
      "name": "acme/web-app",
      "provider": "github",
      "url": "https://github.com/acme/web-app",
      "default_branch": "main",
      "status": "active",
      "compliance_score": 87,
      "last_scan": "2024-01-15T08:00:00Z",
      "issues_count": {
        "critical": 2,
        "high": 5,
        "medium": 12,
        "low": 8
      },
      "frameworks": ["gdpr", "ccpa", "soc2"],
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5
  }
}
```

## Connect Repository

```bash
POST /api/v1/repositories
```

### Request Body

```json
{
  "url": "https://github.com/acme/web-app",
  "provider": "github",
  "access_token": "github_pat_xxx",
  "frameworks": ["gdpr", "ccpa", "soc2"],
  "scan_schedule": "daily",
  "notifications": {
    "slack_webhook": "https://hooks.slack.com/...",
    "email": ["compliance@acme.com"]
  }
}
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "repo_abc123",
    "name": "acme/web-app",
    "provider": "github",
    "status": "connecting",
    "job_id": "job_xyz789"
  }
}
```

## Get Repository

```bash
GET /api/v1/repositories/{repository_id}
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "repo_abc123",
    "name": "acme/web-app",
    "provider": "github",
    "url": "https://github.com/acme/web-app",
    "default_branch": "main",
    "status": "active",
    "compliance_score": 87,
    "last_scan": "2024-01-15T08:00:00Z",
    "scan_schedule": "daily",
    "next_scan": "2024-01-16T08:00:00Z",
    "issues_count": {
      "critical": 2,
      "high": 5,
      "medium": 12,
      "low": 8,
      "total": 27
    },
    "frameworks": [
      {
        "id": "gdpr",
        "name": "GDPR",
        "score": 82,
        "issues": 15
      },
      {
        "id": "ccpa",
        "name": "CCPA",
        "score": 91,
        "issues": 8
      },
      {
        "id": "soc2",
        "name": "SOC 2",
        "score": 89,
        "issues": 4
      }
    ],
    "metrics": {
      "files_scanned": 1247,
      "lines_of_code": 98234,
      "scan_duration_seconds": 127
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-15T08:02:07Z"
  }
}
```

## Update Repository

```bash
PATCH /api/v1/repositories/{repository_id}
```

### Request Body

```json
{
  "frameworks": ["gdpr", "ccpa", "soc2", "hipaa"],
  "scan_schedule": "hourly",
  "notifications": {
    "slack_webhook": "https://hooks.slack.com/new-webhook"
  }
}
```

## Delete Repository

```bash
DELETE /api/v1/repositories/{repository_id}
```

## Scan Repository

Trigger an immediate compliance scan:

```bash
POST /api/v1/repositories/{repository_id}/scan
```

### Request Body

```json
{
  "branch": "main",
  "full_scan": false,
  "frameworks": ["gdpr"]
}
```

### Response

```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123",
    "status": "queued",
    "estimated_duration_seconds": 180
  }
}
```

## Get Scan Status

```bash
GET /api/v1/repositories/{repository_id}/scans/{job_id}
```

### Response

```json
{
  "success": true,
  "data": {
    "job_id": "job_abc123",
    "status": "completed",
    "started_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T10:32:07Z",
    "duration_seconds": 127,
    "results": {
      "files_scanned": 1247,
      "issues_found": 27,
      "issues_new": 3,
      "issues_resolved": 5,
      "compliance_score": 87,
      "score_change": 2
    }
  }
}
```

## List Scan History

```bash
GET /api/v1/repositories/{repository_id}/scans
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `completed`, `failed`, `running` |
| `since` | datetime | Scans since this date |
| `page` | integer | Page number |
| `limit` | integer | Results per page |

## Get Repository Compliance

```bash
GET /api/v1/repositories/{repository_id}/compliance
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `framework` | string | Filter by framework |
| `category` | string | Filter by requirement category |

### Response

```json
{
  "success": true,
  "data": {
    "repository_id": "repo_abc123",
    "overall_score": 87,
    "frameworks": [
      {
        "id": "gdpr",
        "name": "GDPR",
        "score": 82,
        "categories": [
          {
            "name": "data_subject_rights",
            "score": 75,
            "requirements": {
              "compliant": 4,
              "non_compliant": 2,
              "not_applicable": 1
            }
          },
          {
            "name": "security",
            "score": 95,
            "requirements": {
              "compliant": 8,
              "non_compliant": 1,
              "not_applicable": 0
            }
          }
        ]
      }
    ],
    "trends": {
      "last_7_days": [85, 85, 86, 86, 87, 87, 87],
      "last_30_days_avg": 84
    }
  }
}
```

## Get Repository Issues

```bash
GET /api/v1/repositories/{repository_id}/issues
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `severity` | string | Filter by severity: `critical`, `high`, `medium`, `low` |
| `framework` | string | Filter by framework |
| `status` | string | Filter by status: `open`, `acknowledged`, `fixed` |
| `file_path` | string | Filter by file path pattern |

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "issue_123",
      "title": "User data deletion incomplete",
      "description": "The deletion handler does not remove user data from backup systems",
      "severity": "high",
      "framework": "gdpr",
      "requirement_id": "gdpr_art_17",
      "requirement_title": "Right to erasure",
      "file_path": "src/services/user_service.py",
      "line_number": 145,
      "code_snippet": "async def delete_user(user_id: str):\n    await db.users.delete(user_id)\n    # Missing: backup deletion",
      "status": "open",
      "created_at": "2024-01-15T08:00:00Z",
      "fix_available": true
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 27
  }
}
```

## Configure Webhooks

```bash
POST /api/v1/repositories/{repository_id}/webhooks
```

### Request Body

```json
{
  "url": "https://your-app.com/webhooks/compliance",
  "events": ["scan.completed", "issue.created", "issue.resolved"],
  "secret": "webhook_secret_123"
}
```

## Get Repository Branches

```bash
GET /api/v1/repositories/{repository_id}/branches
```

### Response

```json
{
  "success": true,
  "data": [
    {
      "name": "main",
      "is_default": true,
      "last_scan": "2024-01-15T08:00:00Z",
      "compliance_score": 87
    },
    {
      "name": "feature/new-auth",
      "is_default": false,
      "last_scan": "2024-01-14T15:30:00Z",
      "compliance_score": 83
    }
  ]
}
```

## Compare Branches

```bash
GET /api/v1/repositories/{repository_id}/compare
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `base` | string | Base branch name (required) |
| `head` | string | Head branch name (required) |

### Response

```json
{
  "success": true,
  "data": {
    "base": "main",
    "head": "feature/new-auth",
    "score_diff": -4,
    "new_issues": [
      {
        "id": "issue_456",
        "title": "Hardcoded API key",
        "severity": "critical",
        "file_path": "src/config.py",
        "line_number": 23
      }
    ],
    "resolved_issues": [],
    "files_changed": 12
  }
}
```

---

See also: [Compliance API](./compliance) | [Regulations API](./regulations)
