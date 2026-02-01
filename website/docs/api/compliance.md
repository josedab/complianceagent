---
sidebar_position: 5
title: Compliance API
description: API endpoints for compliance status and issues
---

# Compliance API

Access compliance status, manage issues, and generate fixes.

## Get Compliance Dashboard

```bash
GET /api/v1/compliance/dashboard
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `repository_id` | string | Filter by repository |
| `framework` | string | Filter by framework |

### Response

```json
{
  "success": true,
  "data": {
    "overall_score": 85,
    "score_trend": "improving",
    "score_change_7d": 3,
    "repositories": {
      "total": 5,
      "compliant": 3,
      "at_risk": 2
    },
    "issues": {
      "total": 47,
      "critical": 3,
      "high": 12,
      "medium": 22,
      "low": 10
    },
    "frameworks": [
      {
        "id": "gdpr",
        "name": "GDPR",
        "score": 82,
        "issues": 18
      },
      {
        "id": "soc2",
        "name": "SOC 2",
        "score": 91,
        "issues": 8
      }
    ],
    "recent_activity": [
      {
        "type": "issue_resolved",
        "issue_id": "issue_123",
        "repository": "acme/web-app",
        "timestamp": "2024-01-15T09:30:00Z"
      },
      {
        "type": "scan_completed",
        "repository": "acme/api",
        "score": 89,
        "timestamp": "2024-01-15T08:00:00Z"
      }
    ]
  }
}
```

## List Issues

```bash
GET /api/v1/compliance/issues
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `repository_id` | string | Filter by repository |
| `severity` | string | Filter by severity: `critical`, `high`, `medium`, `low` |
| `framework` | string | Filter by framework |
| `status` | string | Filter by status: `open`, `acknowledged`, `in_progress`, `fixed`, `wont_fix` |
| `has_fix` | boolean | Filter by fix availability |
| `sort` | string | Sort by: `severity`, `created_at`, `updated_at` |
| `order` | string | Sort order: `asc`, `desc` |
| `page` | integer | Page number |
| `limit` | integer | Results per page |

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "issue_abc123",
      "title": "Missing encryption for sensitive data at rest",
      "description": "User PII is stored unencrypted in the database",
      "severity": "critical",
      "status": "open",
      "framework": "gdpr",
      "requirement": {
        "id": "gdpr_art_32",
        "title": "Security of processing",
        "article": "Article 32"
      },
      "repository": {
        "id": "repo_123",
        "name": "acme/web-app"
      },
      "location": {
        "file_path": "src/models/user.py",
        "line_start": 45,
        "line_end": 52,
        "branch": "main"
      },
      "code_snippet": "class User(Base):\n    email = Column(String)  # Unencrypted\n    ssn = Column(String)    # Unencrypted",
      "fix_available": true,
      "created_at": "2024-01-15T08:00:00Z",
      "updated_at": "2024-01-15T08:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 47
  }
}
```

## Get Issue

```bash
GET /api/v1/compliance/issues/{issue_id}
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "issue_abc123",
    "title": "Missing encryption for sensitive data at rest",
    "description": "User PII is stored unencrypted in the database",
    "detailed_explanation": "GDPR Article 32 requires appropriate security measures including encryption. Storing PII like email and SSN unencrypted exposes the organization to data breach risks and regulatory penalties.",
    "severity": "critical",
    "status": "open",
    "framework": "gdpr",
    "requirement": {
      "id": "gdpr_art_32",
      "title": "Security of processing",
      "article": "Article 32",
      "full_text": "Taking into account the state of the art, the costs of implementation..."
    },
    "repository": {
      "id": "repo_123",
      "name": "acme/web-app",
      "url": "https://github.com/acme/web-app"
    },
    "location": {
      "file_path": "src/models/user.py",
      "line_start": 45,
      "line_end": 52,
      "branch": "main",
      "commit_sha": "abc123def456"
    },
    "code_snippet": "class User(Base):\n    email = Column(String)  # Unencrypted\n    ssn = Column(String)    # Unencrypted",
    "remediation_guidance": [
      "Implement encryption at the database column level using pgcrypto or similar",
      "Use application-level encryption with secure key management",
      "Consider tokenization for highly sensitive fields like SSN"
    ],
    "fix_available": true,
    "related_issues": [
      {
        "id": "issue_xyz789",
        "title": "Missing encryption key rotation",
        "severity": "medium"
      }
    ],
    "history": [
      {
        "action": "created",
        "timestamp": "2024-01-15T08:00:00Z",
        "actor": "system"
      }
    ],
    "created_at": "2024-01-15T08:00:00Z",
    "updated_at": "2024-01-15T08:00:00Z"
  }
}
```

## Update Issue Status

```bash
PATCH /api/v1/compliance/issues/{issue_id}
```

### Request Body

```json
{
  "status": "acknowledged",
  "assignee": "user@acme.com",
  "notes": "Scheduled for sprint 23",
  "due_date": "2024-02-01T00:00:00Z"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "issue_abc123",
    "status": "acknowledged",
    "assignee": "user@acme.com",
    "notes": "Scheduled for sprint 23",
    "due_date": "2024-02-01T00:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

## Generate Fix

```bash
POST /api/v1/compliance/issues/{issue_id}/generate-fix
```

### Request Body

```json
{
  "strategy": "automatic",
  "options": {
    "encryption_method": "aes_256_gcm",
    "key_source": "aws_kms"
  }
}
```

### Response

```json
{
  "success": true,
  "data": {
    "fix_id": "fix_abc123",
    "issue_id": "issue_abc123",
    "status": "generated",
    "strategy": "automatic",
    "changes": [
      {
        "file_path": "src/models/user.py",
        "operation": "modify",
        "diff": "@@ -45,8 +45,12 @@\n class User(Base):\n-    email = Column(String)\n-    ssn = Column(String)\n+    email = Column(EncryptedString(key_id='user_pii'))\n+    ssn = Column(EncryptedString(key_id='user_pii'))"
      },
      {
        "file_path": "src/utils/encryption.py",
        "operation": "create",
        "content": "# Encryption utilities\nfrom cryptography.fernet import Fernet\n..."
      }
    ],
    "explanation": "This fix adds AES-256-GCM encryption for sensitive columns using AWS KMS for key management. The EncryptedString type automatically encrypts on write and decrypts on read.",
    "confidence_score": 0.95,
    "requires_review": true,
    "created_at": "2024-01-15T10:35:00Z"
  }
}
```

## Apply Fix

```bash
POST /api/v1/compliance/issues/{issue_id}/apply-fix
```

### Request Body

```json
{
  "fix_id": "fix_abc123",
  "create_pull_request": true,
  "pr_options": {
    "title": "fix: Add encryption for user PII fields",
    "description": "Addresses GDPR Article 32 compliance issue",
    "branch": "fix/issue-abc123",
    "reviewers": ["security-team"],
    "labels": ["compliance", "security"]
  }
}
```

### Response

```json
{
  "success": true,
  "data": {
    "fix_id": "fix_abc123",
    "applied": true,
    "pull_request": {
      "url": "https://github.com/acme/web-app/pull/456",
      "number": 456,
      "branch": "fix/issue-abc123"
    },
    "applied_at": "2024-01-15T10:40:00Z"
  }
}
```

## Preview Fix

```bash
GET /api/v1/compliance/issues/{issue_id}/fixes/{fix_id}/preview
```

### Response

```json
{
  "success": true,
  "data": {
    "fix_id": "fix_abc123",
    "files": [
      {
        "path": "src/models/user.py",
        "language": "python",
        "before": "class User(Base):\n    email = Column(String)\n    ssn = Column(String)",
        "after": "class User(Base):\n    email = Column(EncryptedString(key_id='user_pii'))\n    ssn = Column(EncryptedString(key_id='user_pii'))",
        "diff_url": "https://api.complianceagent.io/v1/fixes/fix_abc123/diff/user.py"
      }
    ]
  }
}
```

## Bulk Update Issues

```bash
PATCH /api/v1/compliance/issues/bulk
```

### Request Body

```json
{
  "issue_ids": ["issue_123", "issue_456", "issue_789"],
  "updates": {
    "status": "acknowledged",
    "assignee": "user@acme.com"
  }
}
```

## Get Compliance Status

```bash
GET /api/v1/compliance/status
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `repository_id` | string | Filter by repository |
| `framework` | string | Filter by framework |

### Response

```json
{
  "success": true,
  "data": {
    "status": "at_risk",
    "overall_score": 85,
    "frameworks": {
      "gdpr": {
        "score": 82,
        "status": "at_risk",
        "critical_issues": 1
      },
      "soc2": {
        "score": 91,
        "status": "compliant",
        "critical_issues": 0
      }
    },
    "repositories": {
      "repo_123": {
        "name": "acme/web-app",
        "score": 87,
        "status": "at_risk"
      }
    }
  }
}
```

## Get Compliance History

```bash
GET /api/v1/compliance/history
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `repository_id` | string | Filter by repository |
| `framework` | string | Filter by framework |
| `from` | datetime | Start date |
| `to` | datetime | End date |
| `interval` | string | Data interval: `day`, `week`, `month` |

### Response

```json
{
  "success": true,
  "data": {
    "interval": "day",
    "data_points": [
      {
        "date": "2024-01-08",
        "score": 82,
        "issues_open": 52,
        "issues_resolved": 3
      },
      {
        "date": "2024-01-09",
        "score": 83,
        "issues_open": 50,
        "issues_resolved": 5
      },
      {
        "date": "2024-01-10",
        "score": 85,
        "issues_open": 47,
        "issues_resolved": 4
      }
    ]
  }
}
```

## Export Compliance Report

```bash
POST /api/v1/compliance/reports/export
```

### Request Body

```json
{
  "format": "pdf",
  "repository_ids": ["repo_123", "repo_456"],
  "frameworks": ["gdpr", "soc2"],
  "include_sections": [
    "executive_summary",
    "detailed_findings",
    "remediation_plan",
    "trend_analysis"
  ],
  "date_range": {
    "from": "2024-01-01",
    "to": "2024-01-15"
  }
}
```

### Response

```json
{
  "success": true,
  "data": {
    "job_id": "export_abc123",
    "status": "processing",
    "estimated_completion": "2024-01-15T10:50:00Z"
  }
}
```

---

See also: [Audit API](./audit) | [Repositories API](./repositories)
