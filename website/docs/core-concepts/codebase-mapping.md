---
sidebar_position: 4
title: Codebase Mapping
description: How ComplianceAgent identifies code affected by compliance requirements
---

# Codebase Mapping

ComplianceAgent automatically maps compliance requirements to specific code locations, identifying gaps and affected areas.

## How Mapping Works

### Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Codebase Mapping                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Requirements              Mapping Engine              Code      │
│  ────────────              ──────────────              ────      │
│                                                                  │
│  ┌─────────────┐         ┌─────────────────┐      ┌───────────┐ │
│  │ Encrypt     │         │  Pattern        │      │ src/      │ │
│  │ personal    │────────▶│  Matching       │◀────▶│ utils/    │ │
│  │ data        │         │                 │      │ crypto.py │ │
│  └─────────────┘         └────────┬────────┘      └───────────┘ │
│                                   │                             │
│  ┌─────────────┐                  │               ┌───────────┐ │
│  │ Delete data │                  │               │ src/api/  │ │
│  │ on request  │                  ▼               │ users.py  │ │
│  └─────────────┘         ┌─────────────────┐      └───────────┘ │
│                          │  Gap Analysis   │                    │
│                          │                 │                    │
│                          │ ✓ Met           │                    │
│                          │ ⚠ Gap           │                    │
│                          │ ? Unknown       │                    │
│                          └─────────────────┘                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Step 1: Repository Analysis

When you connect a repository, ComplianceAgent:

1. **Clones the repository** (shallow clone for efficiency)
2. **Indexes the codebase** - Files, structures, dependencies
3. **Builds an AST** - Abstract Syntax Tree for code understanding
4. **Extracts patterns** - Function signatures, data flows, imports

### Step 2: Pattern Matching

Requirements are matched to code using multiple strategies:

#### Keyword Matching

Simple but effective for clear patterns:

```python
# Requirement: "Encrypt personal data"
# Matches code containing:
ENCRYPTION_PATTERNS = [
    r"encrypt\(",
    r"AES\.|RSA\.|Fernet",
    r"bcrypt\.|argon2",
    r"crypto\.|cryptography",
]
```

#### Semantic Analysis

AI-powered understanding of code intent:

```python
# Requirement: "Obtain user consent before processing"
# AI identifies:
# - Consent collection logic (even if not named "consent")
# - Pre-processing checks
# - User acknowledgment flows
```

#### Data Flow Analysis

Tracks how data moves through the application:

```
User Input → Validation → Processing → Storage → Output
     ↓           ↓            ↓           ↓         ↓
  Consent?   Sanitized?   Logged?    Encrypted?  Filtered?
```

### Step 3: Gap Identification

Each requirement gets a compliance status:

| Status | Meaning | Visual |
|--------|---------|--------|
| **Met** | Code satisfies the requirement | ✅ |
| **Gap** | Requirement not satisfied | ⚠️ |
| **Partial** | Partially implemented | 🟡 |
| **Not Applicable** | Doesn't apply to this code | ➖ |
| **Unknown** | Needs manual review | ❓ |

## Mapping Strategies

### Pattern Libraries

ComplianceAgent includes pre-built patterns for common requirements:

#### GDPR Patterns

```yaml
patterns:
  consent_collection:
    indicators:
      - "consent"
      - "opt_in"
      - "accept_terms"
      - "gdpr_consent"
    file_patterns:
      - "**/consent/**"
      - "**/auth/**"
      - "**/registration/**"
    
  data_deletion:
    indicators:
      - "delete_user"
      - "erase_data"
      - "forget_me"
      - "right_to_erasure"
    required_patterns:
      - must_delete_all_tables
      - must_delete_backups
      - must_notify_processors
```

#### HIPAA Patterns

```yaml
patterns:
  phi_protection:
    indicators:
      - "phi"
      - "protected_health"
      - "patient_data"
      - "medical_record"
    security_requirements:
      - encryption_at_rest
      - encryption_in_transit
      - access_logging
```

### Custom Pattern Definition

Define patterns specific to your codebase:

```yaml
# custom-patterns.yml
organization: acme-corp

patterns:
  - name: "pii_handling"
    requirement_category: "data_protection"
    indicators:
      positive:
        - "PersonalData"
        - "CustomerInfo"
        - "UserProfile"
      negative:
        - "test_"
        - "mock_"
        - "fixture_"
    file_patterns:
      include:
        - "src/models/**"
        - "src/services/**"
      exclude:
        - "**/*_test.py"
        - "**/fixtures/**"
```

## Language Support

ComplianceAgent analyzes code in multiple languages:

| Language | Support Level | Features |
|----------|--------------|----------|
| Python | Full | AST, type hints, decorators |
| TypeScript/JavaScript | Full | AST, types, JSX |
| Java | Full | AST, annotations, Spring |
| Go | Full | AST, struct tags |
| C# | Partial | Basic pattern matching |
| Ruby | Partial | Basic pattern matching |

### Language-Specific Analysis

#### Python

```python
# Detects:
# - Decorator-based patterns (@require_consent)
# - Type hints (data: PersonalData)
# - Framework patterns (Django, FastAPI)

@require_consent
def process_user_data(user: User, data: PersonalData) -> Result:
    """Processes user personal data after consent."""
    # Compliance mapping: GDPR consent requirement
    pass
```

#### TypeScript

```typescript
// Detects:
// - Interface definitions (PersonalData)
// - Decorators (@Encrypted)
// - Framework patterns (NestJS, Express)

interface PersonalData {
  email: string;
  @Encrypted()
  ssn: string;
}
```

## Mapping Results

### Compliance Map

A visual representation of requirement-to-code mappings:

```
┌─────────────────────────────────────────────────────────────┐
│                    Compliance Map                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  GDPR Requirements          Your Code                       │
│  ─────────────────          ─────────                       │
│                                                              │
│  Art 7: Consent      ──────▶  src/auth/consent.py      ✅   │
│                               src/api/registration.py   ✅   │
│                                                              │
│  Art 17: Erasure     ──────▶  src/api/users.py         ⚠️   │
│                               src/db/cleanup.py        ✅   │
│                               src/services/backup.py   ⚠️   │
│                                                              │
│  Art 32: Security    ──────▶  src/utils/crypto.py      ✅   │
│                               src/db/connection.py     ✅   │
│                               src/api/middleware.py    🟡   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Gap Report

Detailed report of compliance gaps:

```json
{
  "repository": "acme/backend",
  "framework": "GDPR",
  "assessment_date": "2024-01-15T10:30:00Z",
  "summary": {
    "total_requirements": 45,
    "met": 38,
    "gaps": 5,
    "partial": 2,
    "score": 84.4
  },
  "gaps": [
    {
      "requirement_id": "gdpr-art-17-1",
      "requirement": "Right to erasure",
      "severity": "high",
      "affected_files": [
        {
          "path": "src/api/users.py",
          "line_range": [45, 67],
          "issue": "Delete endpoint doesn't remove backup data",
          "suggested_fix": "Add backup deletion to user_delete handler"
        }
      ]
    }
  ]
}
```

## Impact Analysis

When regulations change, see exactly what's affected:

### Change Impact Report

```
┌─────────────────────────────────────────────────────────────┐
│         Impact Analysis: GDPR Amendment 2024-01              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Change: New requirement for AI-assisted decision disclosure │
│                                                              │
│  Affected Repositories:                                      │
│  ├── acme/ml-service          HIGH IMPACT                   │
│  │   └── src/predictions/     Automated decisions           │
│  │   └── src/api/scoring.py   Credit scoring                │
│  │                                                          │
│  ├── acme/backend             MEDIUM IMPACT                 │
│  │   └── src/recommendations/ Product recommendations       │
│  │                                                          │
│  └── acme/frontend            LOW IMPACT                    │
│      └── src/components/      Display requirements only     │
│                                                              │
│  Estimated Effort: 40 engineering hours                      │
│  Deadline: 6 months from effective date                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Working with Mappings

### Dashboard Views

- **Compliance Overview** - High-level scores per framework
- **Gap List** - All identified gaps with severity
- **File View** - Per-file compliance annotations
- **Requirement View** - Code mapped to each requirement

### API Access

```bash
# Get mappings for a repository
curl -X GET "http://localhost:8000/api/v1/repositories/{repo_id}/mappings" \
  -H "Authorization: Bearer $TOKEN"

# Get gaps only
curl -X GET "http://localhost:8000/api/v1/repositories/{repo_id}/gaps" \
  -H "Authorization: Bearer $TOKEN"

# Trigger re-analysis
curl -X POST "http://localhost:8000/api/v1/repositories/{repo_id}/analyze" \
  -H "Authorization: Bearer $TOKEN"
```

### Annotations in Code

View mappings directly in your IDE with the ComplianceAgent extension:

```python
# src/api/users.py

# [ComplianceAgent] Maps to: GDPR Art. 17 - Right to erasure
# [ComplianceAgent] Status: GAP - Missing backup deletion
# [ComplianceAgent] Severity: HIGH
async def delete_user(user_id: UUID) -> None:
    """Delete a user and all their data."""
    await db.delete(User, id=user_id)
    # TODO: Add backup deletion
```

## Incremental Analysis

After initial analysis, only changed files are re-analyzed:

1. **Webhook triggers** - GitHub pushes trigger analysis
2. **Changed file detection** - Git diff identifies modified files
3. **Incremental update** - Only affected mappings are updated
4. **Notification** - Team notified of compliance changes

```
┌─────────────────────────────────────────────────────────────┐
│                  Incremental Analysis                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Commit: abc123 "Add user deletion endpoint"                 │
│                                                              │
│  Changed Files:                                              │
│  ├── src/api/users.py (modified)      → Re-analyze          │
│  ├── src/models/user.py (modified)    → Re-analyze          │
│  └── tests/test_users.py (modified)   → Skip (tests)        │
│                                                              │
│  Analysis Time: 12 seconds (vs 5 minutes for full)          │
│                                                              │
│  Results:                                                    │
│  └── NEW: GDPR Art. 17 now partially met (+1 mapping)       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Tuning Accuracy

### Feedback Loop

Improve mapping accuracy by providing feedback:

1. **Mark false positives** - "This code isn't related to consent"
2. **Mark false negatives** - "This file should map to Art. 17"
3. **Add custom patterns** - Define organization-specific patterns

### Confidence Thresholds

Adjust sensitivity:

```yaml
# mapping-config.yml
thresholds:
  auto_approve: 0.90    # High confidence = automatic mapping
  review_queue: 0.70    # Medium confidence = human review
  reject: 0.50          # Low confidence = not mapped
```

---

Next: Learn how [Code Generation](./code-generation) creates compliant code automatically.
