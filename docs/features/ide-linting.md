# Real-Time IDE Compliance Linting

The IDE Compliance Linting extension provides real-time compliance analysis directly in your code editor, with AI-powered quick fixes and team collaboration features.

## Overview

The extension integrates with VS Code to:
- Detect 25+ compliance patterns across major frameworks
- Provide instant diagnostics as you type
- Offer AI-powered fix suggestions
- Share suppressions across your team
- Learn from feedback to reduce false positives

## Supported Frameworks

| Framework | Pattern Count | Focus Areas |
|-----------|---------------|-------------|
| GDPR | 6 | PII handling, consent, data retention |
| HIPAA | 4 | PHI protection, access controls, encryption |
| PCI-DSS | 5 | Card data, key management, logging |
| SOC 2 | 4 | Encryption, access logging, secrets |
| EU AI Act | 3 | Bias detection, explainability, data quality |
| General Security | 3 | Authentication, authorization, input validation |

## Features

### Real-Time Diagnostics

As you write code, the extension analyzes for compliance issues:

```python
# This triggers GDPR-PII-001: Personal data detected
user_email = request.form['email']  # ⚠️ Underlined

# This triggers HIPAA-PHI-001: Healthcare data
patient_ssn = data['social_security']  # 🔴 Underlined
```

Diagnostics include:
- Severity (Error, Warning, Information)
- Framework reference (e.g., "GDPR Article 32")
- Compliance requirement ID
- Suggested remediation

### AI-Powered Quick Fixes

Click the lightbulb or press `Ctrl+.` for intelligent fixes:

**Before:**
```python
print(f"User email: {user.email}")
```

**After (AI-generated fix):**
```python
# GDPR Art. 32 - Data protection by design
print(f"User email: {mask_pii(user.email)}")
```

Quick fixes include:
- Code transformations
- Required imports
- Compliance comments
- Explanation of the fix

### Bulk Fix All

Apply all fixes in a document with one command:

1. Open Command Palette (`Ctrl+Shift+P`)
2. Run "ComplianceAgent: Fix All in Document"
3. Review changes in diff view
4. Accept or reject individual fixes

### Team Suppressions

Share false-positive suppressions across your team:

```python
# compliance-suppress: GDPR-PII-001
# This is test data, not real PII
test_email = "test@example.com"
```

Team suppressions:
- Sync across all team members
- Require approval for critical rules
- Support pattern matching (e.g., `test_*.py`)
- Auto-expire after configurable period

### Learning System

The extension learns from your feedback:

1. Mark a detection as false positive
2. Provide reason (optional)
3. System improves pattern accuracy
4. Reduces similar false positives

## Installation

### VS Code Marketplace

1. Open VS Code
2. Go to Extensions (`Ctrl+Shift+X`)
3. Search "ComplianceAgent"
4. Click Install

### Manual Installation

```bash
# From the repository
cd ide-extension/vscode
npm install
npm run build
code --install-extension complianceagent-*.vsix
```

## Configuration

### Extension Settings

```json
// settings.json
{
    "complianceAgent.enabled": true,
    "complianceAgent.apiEndpoint": "https://api.complianceagent.ai",
    "complianceAgent.frameworks": ["GDPR", "HIPAA", "PCI-DSS"],
    "complianceAgent.severityThreshold": "warning",
    "complianceAgent.enableAIFixes": true,
    "complianceAgent.enableTeamSuppression": true,
    "complianceAgent.analysisDelay": 500
}
```

### Per-Workspace Configuration

```json
// .vscode/settings.json
{
    "complianceAgent.frameworks": ["HIPAA"],  // Healthcare project
    "complianceAgent.excludedPaths": [
        "**/test/**",
        "**/__mocks__/**",
        "**/fixtures/**"
    ]
}
```

## Commands

| Command | Keybinding | Description |
|---------|------------|-------------|
| Analyze Current File | `Ctrl+Shift+C A` | Run full analysis on file |
| Fix All in Document | `Ctrl+Shift+C F` | Apply all quick fixes |
| Toggle Compliance Linting | `Ctrl+Shift+C T` | Enable/disable linting |
| Request Team Suppression | `Ctrl+Shift+C S` | Request suppression approval |
| Report False Positive | `Ctrl+Shift+C R` | Submit feedback |
| Show Compliance Panel | `Ctrl+Shift+C P` | Open diagnostics panel |

## API Endpoints

The extension communicates with backend APIs:

### Analyze Document

```http
POST /api/v1/ide/analyze
Content-Type: application/json
Authorization: Bearer <token>

{
    "uri": "file:///workspace/src/user.py",
    "content": "def get_user(id): ...",
    "language": "python",
    "regulations": ["GDPR", "HIPAA"]
}
```

**Response:**
```json
{
    "diagnostics": [
        {
            "range": {"start": {"line": 5, "character": 0}, "end": {"line": 5, "character": 30}},
            "severity": 1,
            "code": "GDPR-PII-001",
            "source": "ComplianceAgent",
            "message": "Personal data handling detected without encryption",
            "data": {
                "requirementId": "GDPR-PII-001",
                "framework": "GDPR",
                "article": "Article 32"
            }
        }
    ],
    "analysis_time_ms": 45
}
```

### Get Quick Fix

```http
POST /api/v1/ide/quickfix
Content-Type: application/json
Authorization: Bearer <token>

{
    "code": "print(user.email)",
    "diagnostic_code": "GDPR-LOG-001",
    "diagnostic_message": "PII in logs",
    "language": "python"
}
```

**Response:**
```json
{
    "original_code": "print(user.email)",
    "fixed_code": "print(mask_pii(user.email))",
    "explanation": "Added PII masking to prevent data exposure in logs",
    "imports_added": ["from complianceagent.utils import mask_pii"],
    "compliance_comments": ["# GDPR Art. 32 - Data masking applied"]
}
```

### Team Suppressions

```http
GET /api/v1/ide/suppressions
Authorization: Bearer <token>
```

```http
POST /api/v1/ide/suppressions
Content-Type: application/json
Authorization: Bearer <token>

{
    "rule_id": "GDPR-PII-001",
    "reason": "Test data only",
    "pattern": "test_*.py"
}
```

### Submit Feedback

```http
POST /api/v1/ide/feedback
Content-Type: application/json
Authorization: Bearer <token>

{
    "type": "false_positive",
    "issue": {
        "requirementId": "GDPR-PII-001",
        "file": "src/test_utils.py",
        "line": 42
    },
    "reason": "This is mock test data"
}
```

## Pattern Reference

### GDPR Patterns

| ID | Pattern | Severity |
|----|---------|----------|
| GDPR-PII-001 | Personal data without encryption | Warning |
| GDPR-PII-002 | PII in logs/debug output | Error |
| GDPR-CONSENT-001 | Data collection without consent check | Warning |
| GDPR-RETENTION-001 | Missing data retention logic | Info |
| GDPR-TRANSFER-001 | Cross-border data transfer | Warning |
| GDPR-DELETE-001 | Missing right-to-deletion | Info |

### HIPAA Patterns

| ID | Pattern | Severity |
|----|---------|----------|
| HIPAA-PHI-001 | PHI without encryption | Error |
| HIPAA-PHI-002 | PHI in logs | Error |
| HIPAA-ACCESS-001 | Missing access controls | Warning |
| HIPAA-AUDIT-001 | Missing audit logging | Warning |

### PCI-DSS Patterns

| ID | Pattern | Severity |
|----|---------|----------|
| PCI-CARD-001 | Card number handling | Error |
| PCI-CVV-001 | CVV storage detected | Error |
| PCI-KEY-001 | Encryption key in code | Error |
| PCI-LOG-001 | Card data in logs | Error |
| PCI-MASK-001 | Unmasked card display | Warning |

## Troubleshooting

### Diagnostics not appearing

1. Check extension is enabled: `complianceAgent.enabled`
2. Verify API endpoint is reachable
3. Confirm file type is supported
4. Check framework selection includes relevant rules

### Quick fixes not available

1. Ensure `complianceAgent.enableAIFixes` is true
2. Check API authentication is valid
3. Verify network connectivity

### Team suppressions not syncing

1. Confirm `complianceAgent.enableTeamSuppression` is true
2. Check organization membership
3. Verify suppression hasn't expired

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     VS Code Extension                        │
├─────────────────┬─────────────────┬─────────────────────────┤
│  Language       │  Quick Fix      │  Learning               │
│  Server         │  Provider       │  System                 │
│  (Diagnostics)  │  (AI Fixes)     │  (Feedback)            │
└────────┬────────┴────────┬────────┴────────┬────────────────┘
         │                 │                  │
         ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend API                               │
├─────────────────┬─────────────────┬─────────────────────────┤
│  /ide/analyze   │  /ide/quickfix  │  /ide/feedback          │
│  Pattern Match  │  Copilot SDK    │  Pattern Learning       │
└─────────────────┴─────────────────┴─────────────────────────┘
```

## Development

### Building the Extension

```bash
cd ide-extension/vscode
npm install
npm run compile    # Development build
npm run package    # Production .vsix
```

### Running Tests

```bash
npm test
npm run test:e2e
```

### Adding New Patterns

1. Edit `src/language-server.ts`
2. Add pattern to `COMPLIANCE_PATTERNS` array:

```typescript
{
    id: 'CUSTOM-001',
    framework: 'Custom',
    severity: DiagnosticSeverity.Warning,
    pattern: /sensitivePattern/g,
    message: 'Custom compliance issue detected',
    codeDescription: {
        href: 'https://docs.custom.com/requirement-1'
    },
    recommendation: 'Apply recommended fix...'
}
```
