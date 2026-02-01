---
sidebar_position: 5
title: Code Generation
description: How ComplianceAgent generates compliant code modifications
---

# Code Generation

ComplianceAgent doesn't just identify gaps—it generates compliant code to fix them.

## How Generation Works

### Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Code Generation Pipeline                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Gap Identified          Generation Engine          Output       │
│  ──────────────          ─────────────────          ──────       │
│                                                                  │
│  ┌─────────────┐        ┌─────────────────┐       ┌───────────┐ │
│  │ Missing     │        │  1. Context     │       │ Generated │ │
│  │ encryption  │───────▶│     Gathering   │──────▶│ Code      │ │
│  │ for PII     │        └────────┬────────┘       └─────┬─────┘ │
│  └─────────────┘                 │                      │       │
│                                  ▼                      ▼       │
│                         ┌─────────────────┐       ┌───────────┐ │
│                         │  2. Code        │       │ Pull      │ │
│                         │     Generation  │       │ Request   │ │
│                         └────────┬────────┘       └───────────┘ │
│                                  │                              │
│                                  ▼                              │
│                         ┌─────────────────┐                     │
│                         │  3. Validation  │                     │
│                         │     & Testing   │                     │
│                         └─────────────────┘                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Step 1: Context Gathering

Before generating code, ComplianceAgent gathers context:

- **Existing code style** - Indentation, naming conventions, patterns
- **Framework usage** - Django, FastAPI, Express, etc.
- **Related code** - Similar functions, imports, dependencies
- **Requirement details** - Full compliance requirement with citations

### Step 2: Code Generation

Using GitHub Copilot SDK, ComplianceAgent generates fixes:

```python
from copilot_sdk import CopilotClient

def generate_fix(gap: ComplianceGap, context: CodeContext) -> GeneratedFix:
    client = CopilotClient(api_key=settings.COPILOT_API_KEY)
    
    prompt = f"""
    Generate code to fix this compliance gap.
    
    Requirement: {gap.requirement.text}
    Regulation: {gap.requirement.source_article}
    
    Current code:
    [CODE_BLOCK_START]{context.language}
    {context.current_code}
    [CODE_BLOCK_END]
    
    File: {context.file_path}
    Function: {context.function_name}
    
    Code style guidelines:
    - {context.style_guide}
    
    Generate a fix that:
    1. Addresses the compliance requirement
    2. Matches the existing code style
    3. Includes appropriate error handling
    4. Adds necessary imports
    """
    
    response = client.complete(prompt, max_tokens=2000)
    return parse_generated_code(response)
```

### Step 3: Validation

Generated code is validated before presenting:

- **Syntax check** - Code must parse without errors
- **Type check** - Type annotations must be valid
- **Import check** - All imports must be available
- **Test generation** - Basic tests are generated

## Generation Capabilities

### Fix Types

| Fix Type | Description | Example |
|----------|-------------|---------|
| **Add Code** | Insert new functionality | Add encryption function |
| **Modify Code** | Update existing logic | Add consent check |
| **Wrap Code** | Add surrounding logic | Add try/catch with audit |
| **Replace Code** | Substitute implementation | Use secure alternative |

### Templates

Pre-built templates for common compliance patterns:

#### GDPR Consent Template

```python
# Template: gdpr_consent_check
# Requirement: GDPR Art. 7 - Consent

def process_with_consent(user_id: str, data: dict) -> ProcessResult:
    """Process user data only with valid consent."""
    # Check for valid consent
    consent = get_user_consent(user_id, purpose="data_processing")
    
    if not consent or not consent.is_valid:
        raise ConsentRequiredError(
            f"Valid consent required for user {user_id}",
            purpose="data_processing"
        )
    
    # Log consent usage for audit
    audit_log.record(
        event="consent_used",
        user_id=user_id,
        consent_id=consent.id,
        purpose="data_processing"
    )
    
    # Process data
    return process_data(data)
```

#### HIPAA PHI Handler Template

```python
# Template: hipaa_phi_handler
# Requirement: HIPAA Security Rule

from encryption import encrypt_phi, decrypt_phi
from audit import phi_access_log

class PHIHandler:
    """Handler for Protected Health Information with HIPAA compliance."""
    
    def __init__(self, user_context: UserContext):
        self.user = user_context
        self._validate_access_rights()
    
    def _validate_access_rights(self):
        if not self.user.has_phi_access:
            phi_access_log.record_denied(self.user.id)
            raise PHIAccessDeniedError("User lacks PHI access rights")
    
    def read(self, record_id: str) -> PHIRecord:
        """Read PHI with audit logging."""
        phi_access_log.record_access(
            user_id=self.user.id,
            record_id=record_id,
            action="read"
        )
        encrypted_data = self._fetch_record(record_id)
        return decrypt_phi(encrypted_data)
    
    def write(self, record_id: str, data: PHIRecord) -> None:
        """Write PHI with encryption and audit."""
        phi_access_log.record_access(
            user_id=self.user.id,
            record_id=record_id,
            action="write"
        )
        encrypted_data = encrypt_phi(data)
        self._store_record(record_id, encrypted_data)
```

#### Data Deletion Template

```python
# Template: data_deletion_handler
# Requirement: GDPR Art. 17 - Right to erasure

async def delete_user_data(
    user_id: UUID,
    include_backups: bool = True,
    notify_processors: bool = True
) -> DeletionResult:
    """Delete all user data per GDPR Art. 17."""
    
    result = DeletionResult(user_id=user_id)
    
    # 1. Delete from primary database
    async with db.transaction():
        tables = ["users", "profiles", "preferences", "activity_logs"]
        for table in tables:
            count = await db.delete(table, user_id=user_id)
            result.add_deleted(table, count)
    
    # 2. Delete from search indices
    await search_client.delete_user_documents(user_id)
    result.add_deleted("search_index", 1)
    
    # 3. Delete from object storage
    await storage.delete_user_files(user_id)
    result.add_deleted("file_storage", "all")
    
    # 4. Delete from backups (if requested)
    if include_backups:
        await backup_service.schedule_deletion(user_id)
        result.backup_deletion_scheduled = True
    
    # 5. Notify third-party processors
    if notify_processors:
        processors = await get_data_processors(user_id)
        for processor in processors:
            await processor.request_deletion(user_id)
        result.processors_notified = len(processors)
    
    # 6. Create audit record
    await audit_log.record_deletion(
        user_id=user_id,
        result=result,
        legal_basis="gdpr_art_17"
    )
    
    return result
```

## Pull Request Creation

### PR Structure

Generated PRs include:

```markdown
## 🛡️ Compliance Fix: GDPR Art. 17 - Right to Erasure

### Summary
This PR adds proper data deletion handling to comply with GDPR Article 17.

### Compliance Context
- **Requirement**: Data subjects have the right to erasure ("right to be forgotten")
- **Article**: GDPR Article 17(1)
- **Gap Identified**: User deletion endpoint doesn't remove backup data

### Changes
- `src/api/users.py`: Added backup deletion to delete endpoint
- `src/services/backup.py`: New function for user data purge
- `tests/test_deletion.py`: Tests for complete data erasure

### Verification
- [ ] All user data deleted from primary database
- [ ] Search indices cleared
- [ ] Backup deletion scheduled
- [ ] Third-party processors notified
- [ ] Audit trail created

### Related
- Requirement ID: `gdpr-art-17-1`
- ComplianceAgent Assessment: [Link to assessment]

---
*Generated by ComplianceAgent*
```

### PR Labels

PRs are automatically labeled:

- `compliance` - Compliance-related change
- `gdpr` / `hipaa` / `pci-dss` - Specific framework
- `auto-generated` - Created by ComplianceAgent
- `needs-review` - Requires human review

## Multi-Language Support

Code generation works across languages:

### Python

```python
# Generated: Encryption utility
from cryptography.fernet import Fernet
from typing import Union

def encrypt_pii(data: Union[str, bytes], key: bytes) -> bytes:
    """Encrypt PII data using Fernet symmetric encryption."""
    f = Fernet(key)
    if isinstance(data, str):
        data = data.encode('utf-8')
    return f.encrypt(data)
```

### TypeScript

```typescript
// Generated: Consent check middleware
import { Request, Response, NextFunction } from 'express';
import { ConsentService } from '../services/consent';

export async function requireConsent(purpose: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const userId = req.user?.id;
    if (!userId) {
      return res.status(401).json({ error: 'Authentication required' });
    }
    
    const consent = await ConsentService.check(userId, purpose);
    if (!consent.valid) {
      return res.status(403).json({ 
        error: 'Consent required',
        purpose,
        consentUrl: `/consent?purpose=${purpose}`
      });
    }
    
    req.consent = consent;
    next();
  };
}
```

### Java

```java
// Generated: PHI access logger
@Component
public class PHIAccessLogger {
    
    private final AuditRepository auditRepository;
    
    @Autowired
    public PHIAccessLogger(AuditRepository auditRepository) {
        this.auditRepository = auditRepository;
    }
    
    public void logAccess(String userId, String recordId, AccessType type) {
        AuditEntry entry = AuditEntry.builder()
            .userId(userId)
            .recordId(recordId)
            .accessType(type)
            .timestamp(Instant.now())
            .build();
        
        auditRepository.save(entry);
    }
}
```

## Review Workflow

### Review Interface

The dashboard provides a code review interface:

1. **Side-by-side diff** - Current vs. generated code
2. **Requirement context** - Why this change is needed
3. **Inline comments** - AI-generated explanations
4. **Test results** - Automated test outcomes

### Actions

- **Approve & Create PR** - Accept the fix
- **Edit & Create PR** - Modify before creating
- **Reject** - Mark as not applicable
- **Request Changes** - Ask for different approach

## Customization

### Style Matching

ComplianceAgent learns your code style:

```yaml
# .complianceagent/style.yml
python:
  indent: 4
  quotes: double
  line_length: 88
  formatter: black
  
typescript:
  indent: 2
  quotes: single
  semicolons: true
  formatter: prettier
```

### Custom Templates

Create organization-specific templates:

```yaml
# .complianceagent/templates/consent-check.yml
name: consent_check
language: python
requirements:
  - gdpr-art-7

template: |
  def {function_name}_with_consent({params}) -> {return_type}:
      """
      {docstring}
      
      Compliance: GDPR Art. 7 - Consent
      """
      consent = ConsentService.verify(
          user_id=user_id,
          purpose="{purpose}"
      )
      if not consent.valid:
          raise ConsentError(purpose="{purpose}")
      
      return {original_function}({params})
```

## Safety Guardrails

### Code Safety Checks

Generated code is checked for:

- **No credential exposure** - Secrets aren't hardcoded
- **No SQL injection** - Parameterized queries only
- **No XSS vulnerabilities** - Output is escaped
- **Dependency safety** - Only approved packages

### Review Requirements

High-risk changes require additional review:

| Change Type | Auto-merge | Required Reviews |
|-------------|------------|------------------|
| Add logging | Yes | 0 |
| Add validation | No | 1 |
| Modify auth | No | 2 |
| Change encryption | No | 2 + security |

---

Next: Learn about [Multi-Jurisdiction](./multi-jurisdiction) handling for global compliance.
