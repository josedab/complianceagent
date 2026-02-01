---
sidebar_position: 3
title: Generating Compliance Code
description: Use AI to generate compliant code fixes for identified gaps
---

# Generating Compliance Code

ComplianceAgent can automatically generate code to fix compliance gaps. This guide shows you how to review, customize, and deploy these fixes.

## Finding Gaps to Fix

### Dashboard View

Navigate to gaps in the dashboard:

1. Go to **Compliance → Gaps**
2. Filter by severity, framework, or repository
3. Click a gap to see details

### Gap Detail View

```
┌─────────────────────────────────────────────────────────────────┐
│              Gap: GDPR Art. 17 - Right to Erasure                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Severity: 🟠 HIGH                                               │
│  Repository: acme/backend                                        │
│  File: src/api/users.py (lines 45-67)                           │
│                                                                  │
│  Requirement:                                                    │
│  "The data subject shall have the right to obtain from the       │
│  controller the erasure of personal data concerning him or       │
│  her without undue delay"                                        │
│                                                                  │
│  Issue:                                                          │
│  User deletion endpoint removes primary data but does not:       │
│  • Delete from backup systems                                    │
│  • Remove from search indices                                    │
│  • Notify third-party processors                                 │
│                                                                  │
│  [Generate Fix] [Mark as Not Applicable] [Dismiss]               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Generating a Fix

### Step 1: Request Generation

Click **Generate Fix** to start the AI generation process.

ComplianceAgent will:
1. Gather context from your codebase
2. Analyze the specific requirement
3. Generate appropriate code changes
4. Validate the generated code

### Step 2: Review Generated Code

```
┌─────────────────────────────────────────────────────────────────┐
│                    Generated Fix Preview                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  File: src/api/users.py                                         │
│                                                                  │
│  - async def delete_user(user_id: UUID) -> None:                │
│  -     """Delete a user."""                                     │
│  -     await db.delete(User, id=user_id)                        │
│  + async def delete_user(                                        │
│  +     user_id: UUID,                                            │
│  +     include_backups: bool = True                              │
│  + ) -> DeletionResult:                                          │
│  +     """Delete user and all associated data per GDPR Art 17."""│
│  +     result = DeletionResult(user_id=user_id)                  │
│  +                                                               │
│  +     # Delete from primary database                            │
│  +     async with db.transaction():                              │
│  +         await db.delete(User, id=user_id)                     │
│  +         await db.delete(UserProfile, user_id=user_id)         │
│  +         await db.delete(UserPreferences, user_id=user_id)     │
│  +         result.primary_deleted = True                         │
│  +                                                               │
│  +     # Delete from search index                                │
│  +     await search.delete_user_documents(user_id)               │
│  +     result.search_deleted = True                              │
│  +                                                               │
│  +     # Schedule backup deletion                                │
│  +     if include_backups:                                       │
│  +         await backup_service.schedule_deletion(user_id)       │
│  +         result.backup_scheduled = True                        │
│  +                                                               │
│  +     # Notify processors                                       │
│  +     await notify_data_processors(user_id, "deletion")         │
│  +     result.processors_notified = True                         │
│  +                                                               │
│  +     # Audit log                                               │
│  +     await audit_log.record_deletion(user_id, result)          │
│  +                                                               │
│  +     return result                                              │
│                                                                  │
│  Additional files:                                               │
│  + src/models/deletion.py (new)                                  │
│  ~ src/services/backup.py (modified)                             │
│  + tests/test_user_deletion.py (new)                             │
│                                                                  │
│  [View Full Diff] [Edit] [Create PR] [Regenerate]                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Step 3: Customize the Fix

Before creating a PR, you can customize the generated code:

#### Edit Inline

Click **Edit** to modify the code directly in the browser.

#### Request Changes

Ask for specific modifications:

```
"Use our existing `DataDeletionService` instead of inline logic"
```

Click **Regenerate with Instructions** to get updated code.

### Step 4: Create Pull Request

When satisfied, click **Create PR**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Create Pull Request                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Title:                                                          │
│  [🛡️ Compliance: GDPR Art. 17 - Complete user data deletion]   │
│                                                                  │
│  Branch:                                                         │
│  [compliance/gdpr-art-17-deletion-fix]                           │
│                                                                  │
│  Base:                                                           │
│  [main ▼]                                                        │
│                                                                  │
│  Labels:                                                         │
│  [x] compliance                                                  │
│  [x] gdpr                                                        │
│  [x] auto-generated                                              │
│  [ ] needs-security-review                                       │
│                                                                  │
│  Reviewers:                                                      │
│  [Add reviewers...]                                              │
│                                                                  │
│  [Create Pull Request]                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Generated PR Structure

The created PR includes:

### Title and Labels

```markdown
🛡️ Compliance: GDPR Art. 17 - Complete user data deletion

Labels: compliance, gdpr, auto-generated
```

### Description

```markdown
## Summary

This PR implements complete user data deletion to comply with GDPR Article 17 
(Right to Erasure).

## Compliance Context

**Requirement**: GDPR Article 17(1)
> The data subject shall have the right to obtain from the controller the 
> erasure of personal data concerning him or her without undue delay.

**Gap Identified**: User deletion endpoint didn't fully remove all user data.

## Changes

### `src/api/users.py`
- Extended `delete_user` to handle complete data erasure
- Added backup deletion scheduling
- Added processor notification
- Added audit logging

### `src/models/deletion.py` (new)
- `DeletionResult` model for tracking deletion status

### `src/services/backup.py`
- Added `schedule_deletion` method for GDPR-compliant backup removal

### `tests/test_user_deletion.py` (new)
- Tests for complete deletion flow
- Tests for backup scheduling
- Tests for processor notification

## Compliance Checklist

- [x] Primary database records deleted
- [x] Search indices cleared
- [x] Backup deletion scheduled
- [x] Third-party processors notified
- [x] Audit trail created

## Testing

```bash
pytest tests/test_user_deletion.py -v
```

## Related

- ComplianceAgent Gap: #GAP-2024-0142
- GDPR Article 17: [Link]

---
*Generated by ComplianceAgent*
```

## Bulk Fix Generation

Generate fixes for multiple gaps at once:

### Step 1: Select Gaps

1. Go to **Compliance → Gaps**
2. Check boxes next to gaps to fix
3. Click **Generate Fixes for Selected**

### Step 2: Review All Fixes

```
┌─────────────────────────────────────────────────────────────────┐
│                   Bulk Fix Generation                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Generating fixes for 5 gaps...                                  │
│                                                                  │
│  ✅ GDPR Art. 17 - User deletion          Ready for review       │
│  ✅ GDPR Art. 7 - Consent tracking        Ready for review       │
│  ⏳ GDPR Art. 32 - Encryption             Generating...         │
│  ○  HIPAA PHI logging                     Queued                 │
│  ○  PCI-DSS Card masking                  Queued                 │
│                                                                  │
│  [Review Completed] [Cancel Remaining]                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Step 3: Choose PR Strategy

- **Single PR**: All fixes in one pull request
- **Separate PRs**: One PR per fix (recommended for unrelated gaps)
- **By Framework**: Group fixes by regulatory framework

## Using Templates

### Pre-Built Templates

ComplianceAgent includes templates for common patterns:

```
┌─────────────────────────────────────────────────────────────────┐
│                   Available Templates                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  GDPR Templates:                                                 │
│  ├── gdpr-consent-banner     Consent collection UI              │
│  ├── gdpr-dsar-handler       Data subject access request        │
│  ├── gdpr-deletion-handler   Complete data deletion             │
│  └── gdpr-breach-notifier    Breach notification system         │
│                                                                  │
│  HIPAA Templates:                                                │
│  ├── hipaa-phi-handler       PHI access with logging            │
│  ├── hipaa-encryption        PHI encryption at rest             │
│  └── hipaa-audit-log         Required audit logging             │
│                                                                  │
│  PCI-DSS Templates:                                              │
│  ├── pci-card-tokenization   Card data tokenization             │
│  ├── pci-card-masking        Display masking                    │
│  └── pci-access-control      Card data access restrictions      │
│                                                                  │
│  [Use Template] [View Code]                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Applying Templates

```bash
# API: Apply template to repository
curl -X POST "http://localhost:8000/api/v1/templates/apply" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "template": "gdpr-consent-banner",
    "repository": "acme/web-app",
    "target_path": "src/components/consent/",
    "config": {
      "purposes": ["marketing", "analytics", "functional"],
      "default_language": "en",
      "style_framework": "tailwind"
    }
  }'
```

## Custom Fix Instructions

Guide the AI with specific requirements:

### Via Dashboard

When generating a fix, add instructions:

```
Instructions for this fix:
- Use our existing AuthService for user context
- Follow the repository's error handling pattern (see src/errors.py)
- Add metrics using our Prometheus client
- Use async/await consistently
```

### Via Configuration

Add to `.complianceagent/config.yml`:

```yaml
generation:
  instructions:
    global: |
      - Use Python type hints for all functions
      - Follow PEP 8 naming conventions
      - Add docstrings to public functions
    
    by_framework:
      gdpr:
        - Include GDPR article reference in docstrings
        - Always log to audit trail
      
      hipaa:
        - Use PHIHandler for all health data access
        - Encrypt at rest and in transit
```

## Reviewing and Merging

### Code Review Best Practices

1. **Verify requirement mapping** - Does the code actually address the requirement?
2. **Check edge cases** - Are error scenarios handled?
3. **Review security** - No new vulnerabilities introduced?
4. **Test coverage** - Are generated tests adequate?

### After Merge

When the PR is merged:

1. ComplianceAgent detects the merge
2. Re-analyzes the affected repository
3. Updates gap status to "Resolved"
4. Records in audit trail

## Handling Generation Failures

### Common Issues

| Issue | Solution |
|-------|----------|
| "Could not understand codebase structure" | Add more context files to analysis |
| "Conflicting patterns detected" | Provide specific instructions |
| "Required dependency not found" | Add dependencies to instructions |
| "Test generation failed" | Manual test writing may be needed |

### Requesting Manual Review

If AI can't generate a fix:

```
┌─────────────────────────────────────────────────────────────────┐
│                   Generation Not Possible                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ComplianceAgent couldn't automatically generate a fix for       │
│  this gap. This may be because:                                  │
│                                                                  │
│  • The requirement needs architectural changes                   │
│  • The codebase pattern is too unique                           │
│  • External system integration required                          │
│                                                                  │
│  Recommended: Manual implementation                              │
│                                                                  │
│  Guidance:                                                       │
│  GDPR Art. 32 requires "appropriate technical measures."         │
│  For your architecture, consider:                                │
│  1. Implementing encryption at the database layer               │
│  2. Using your cloud provider's KMS                             │
│  3. Adding TLS for internal service communication               │
│                                                                  │
│  [Create Task for Manual Implementation] [Dismiss]               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

Next: Learn about [CI/CD Integration](./cicd-integration) to block non-compliant code at merge time.
