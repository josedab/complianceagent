# Automated Compliance PR Bot

The Compliance PR Bot automatically analyzes pull requests for regulatory compliance issues, providing real-time feedback through GitHub Checks, inline comments, and smart labels.

## Overview

When a pull request is opened or synchronized, the PR Bot:
1. Queues the PR for analysis using Redis-backed queue
2. Runs compliance checks against selected regulatory frameworks
3. Creates a GitHub Check with detailed results
4. Posts inline review comments on specific code violations
5. Applies appropriate compliance labels
6. Optionally blocks merge for critical violations

## Features

### GitHub Checks Integration

The bot creates detailed check runs visible in the PR:

```
✅ ComplianceAgent: HIPAA Check - Passed
⚠️ ComplianceAgent: GDPR Check - 2 warnings
❌ ComplianceAgent: PCI-DSS Check - 1 critical violation
```

Each check includes:
- Summary of violations found
- Severity breakdown (critical, high, medium, low)
- Links to specific lines and fix suggestions

### Smart Auto-Labeling

PRs are automatically labeled based on compliance risk:

| Label | Condition |
|-------|-----------|
| `compliance-critical` | Any critical severity violations |
| `compliance-warning` | Only warnings, no critical |
| `compliance-ok` | No violations found |
| `needs-compliance-review` | Manual review recommended |
| `compliance-skip` | Analysis skipped (test files only) |

### Inline Review Comments

The bot posts contextual comments directly on affected lines:

```python
# Line 42: user_email = request.form['email']
# 
# 🔴 GDPR-PII-001: Personal data processed without consent validation
# 
# **Recommendation**: Add consent verification before processing PII
# **Article**: GDPR Article 6(1)(a) - Lawfulness of processing
# 
# Suggested fix:
#   if not user.has_valid_consent('email_processing'):
#       raise ConsentRequiredError()
```

### Merge Blocking

When enabled, critical violations prevent PR merge:

```yaml
# Organization settings
pr_bot:
  block_on_critical: true
  required_checks:
    - GDPR
    - HIPAA
```

## Configuration

### Organization Settings

Configure via API or dashboard:

```python
PUT /api/v1/pr-bot/config
{
    "enabled": true,
    "auto_comment": true,
    "auto_label": true,
    "block_on_critical": true,
    "frameworks": ["GDPR", "HIPAA", "PCI-DSS"],
    "excluded_paths": ["tests/**", "*.test.ts", "**/__mocks__/**"]
}
```

### GitHub App Setup

1. Install the ComplianceAgent GitHub App
2. Grant repository access
3. Enable webhook events: `pull_request`, `check_run`

### Webhook Configuration

The bot listens on `/api/v1/webhooks/github` for:
- `pull_request.opened` - New PR analysis
- `pull_request.synchronize` - Re-analyze on new commits
- `check_run.rerequested` - Manual re-run requested

## API Reference

### Trigger Analysis

```http
POST /api/v1/pr-bot/analyze
Content-Type: application/json
Authorization: Bearer <token>

{
    "owner": "your-org",
    "repo": "your-repo",
    "pr_number": 123,
    "frameworks": ["GDPR", "HIPAA"]
}
```

**Response:**
```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "queued",
    "pr": {
        "owner": "your-org",
        "repo": "your-repo",
        "number": 123
    }
}
```

### Get Task Status

```http
GET /api/v1/pr-bot/task/{task_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "result": {
        "pr_url": "https://github.com/org/repo/pull/123",
        "violations_by_severity": {
            "critical": 0,
            "high": 2,
            "medium": 5,
            "low": 3
        },
        "check_run_id": 12345678,
        "comments_posted": 7,
        "labels_applied": ["compliance-warning"],
        "duration_seconds": 45.2
    }
}
```

### Batch Analysis

```http
POST /api/v1/pr-bot/analyze/batch
Content-Type: application/json
Authorization: Bearer <token>

{
    "prs": [
        {"owner": "org", "repo": "repo1", "pr_number": 1},
        {"owner": "org", "repo": "repo1", "pr_number": 2},
        {"owner": "org", "repo": "repo2", "pr_number": 5}
    ]
}
```

### Get Statistics

```http
GET /api/v1/pr-bot/stats
Authorization: Bearer <token>
```

**Response:**
```json
{
    "total_analyzed": 1247,
    "blocked_prs": 23,
    "violations_found": 5621,
    "by_framework": {
        "GDPR": {"analyzed": 1100, "violations": 3200},
        "HIPAA": {"analyzed": 450, "violations": 1821}
    },
    "average_analysis_time_seconds": 38.5
}
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  GitHub Webhook │────▶│  Webhook API    │────▶│  Redis Queue    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  GitHub Checks  │◀────│  Celery Worker  │────▶│  PR Bot Service │
│  (Results)      │     │  (Async Task)   │     │  (Analysis)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │  AI Analysis    │
                                                │  (Copilot SDK)  │
                                                └─────────────────┘
```

## Best Practices

1. **Start with warnings only** - Set `block_on_critical: false` initially to understand baseline
2. **Exclude test files** - Use `excluded_paths` to avoid false positives in test code
3. **Review suppression requests** - Team members can request suppressions for false positives
4. **Monitor statistics** - Track violation trends over time to measure improvement

## Troubleshooting

### Check run not appearing

1. Verify GitHub App installation has check write permissions
2. Confirm webhook is configured and receiving events
3. Check Celery worker logs for errors

### Analysis taking too long

1. Large PRs with many files take longer - consider file limits
2. Check Redis connection and worker capacity
3. Review excluded_paths to skip unnecessary files

### False positives

1. Use team suppressions for known false positives
2. Submit feedback via IDE extension to improve patterns
3. Adjust framework-specific thresholds in configuration
