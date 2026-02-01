---
sidebar_position: 5
title: IDE Integration
description: Get real-time compliance feedback in VS Code and JetBrains
---

# IDE Integration

Get compliance feedback directly in your IDE as you write code.

## VS Code Extension

### Installation

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "ComplianceAgent"
4. Click **Install**

Or install via command line:

```bash
code --install-extension complianceagent.complianceagent-vscode
```

### Configuration

After installation, configure the extension:

1. Open Settings (Ctrl+,)
2. Search for "ComplianceAgent"
3. Enter your API key

Or add to `settings.json`:

```json
{
  "complianceagent.apiKey": "your-api-key",
  "complianceagent.enabled": true,
  "complianceagent.frameworks": ["gdpr", "ccpa", "hipaa"],
  "complianceagent.severity.show": ["critical", "high", "medium"],
  "complianceagent.autoSuggest": true
}
```

### Features

#### Real-Time Diagnostics

Compliance issues appear as you type:

```
┌─────────────────────────────────────────────────────────────────┐
│  src/api/users.py                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  34 │ def save_user_profile(user_id, data):                     │
│  35 │     """Save user profile data."""                         │
│  36 │ ~~~~ user_email = data['email']  ⚠️ GDPR-ART-7           │
│  37 │     user_name = data['name']                              │
│  38 │     db.save(UserProfile(                                  │
│  39 │         user_id=user_id,                                  │
│  40 │         email=user_email,                                 │
│  41 │         name=user_name                                    │
│  42 │     ))                                                     │
│                                                                  │
│  ⚠️ Compliance Issue (GDPR Art. 7)                              │
│  Personal data (email) collected without consent verification    │
│  [Quick Fix] [View Requirement] [Ignore]                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Quick Fixes

Click the lightbulb or press Ctrl+. for quick fixes:

```
Quick Actions:
├── 🛡️ Add consent check before data collection
├── 🛡️ Wrap with consent verification decorator
├── 📖 View GDPR Article 7 details
└── ⚪ Ignore for this line
```

Selecting "Add consent check" inserts:

```python
def save_user_profile(user_id, data):
    """Save user profile data."""
    # Verify consent before processing personal data
    consent = ConsentService.verify(user_id, purpose="profile_storage")
    if not consent.valid:
        raise ConsentRequiredError("Consent required for profile storage")
    
    user_email = data['email']
    user_name = data['name']
    db.save(UserProfile(
        user_id=user_id,
        email=user_email,
        name=user_name
    ))
```

#### Hover Information

Hover over highlighted code for details:

```
┌─────────────────────────────────────────────────────────────────┐
│  GDPR Article 7 - Conditions for Consent                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  "Where processing is based on consent, the controller shall     │
│  be able to demonstrate that the data subject has consented     │
│  to processing of his or her personal data."                    │
│                                                                  │
│  This code collects personal data (email address) without       │
│  verifying that the user has provided consent.                  │
│                                                                  │
│  Severity: High                                                  │
│  Framework: GDPR                                                 │
│  Confidence: 94%                                                 │
│                                                                  │
│  [Generate Fix] [View Full Article] [Mark as False Positive]    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Code Lens

See compliance status above functions:

```python
# 🛡️ 2 compliance issues | GDPR: ⚠️ | HIPAA: ✅
def process_patient_data(patient_id, medical_records):
    ...
```

#### Problems Panel

All issues appear in the Problems panel (Ctrl+Shift+M):

```
PROBLEMS (3)
├── ⚠️ src/api/users.py
│   ├── Line 36: GDPR Art. 7 - Consent not verified
│   └── Line 52: GDPR Art. 17 - No deletion handler
└── ⚠️ src/services/analytics.py
    └── Line 18: CCPA - Opt-out not honored
```

### Commands

Access via Command Palette (Ctrl+Shift+P):

| Command | Description |
|---------|-------------|
| `ComplianceAgent: Scan File` | Scan current file |
| `ComplianceAgent: Scan Workspace` | Scan entire workspace |
| `ComplianceAgent: Show Gap Report` | Open compliance report |
| `ComplianceAgent: Generate Fix` | Generate fix for issue at cursor |
| `ComplianceAgent: Configure Frameworks` | Select active frameworks |

### Status Bar

The status bar shows overall compliance status:

```
🛡️ ComplianceAgent: 3 issues (1 high)
```

Click to open the compliance panel.

## JetBrains IDEs

### Installation

1. Open Settings (Ctrl+Alt+S)
2. Go to **Plugins → Marketplace**
3. Search for "ComplianceAgent"
4. Click **Install**
5. Restart the IDE

### Supported IDEs

- IntelliJ IDEA
- PyCharm
- WebStorm
- PhpStorm
- GoLand
- Rider

### Configuration

Navigate to **Settings → Tools → ComplianceAgent**:

```
┌─────────────────────────────────────────────────────────────────┐
│  ComplianceAgent Settings                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  API Key: [************************]                             │
│                                                                  │
│  ☑ Enable real-time scanning                                    │
│  ☑ Show compliance annotations                                   │
│  ☑ Enable quick fixes                                           │
│                                                                  │
│  Frameworks:                                                     │
│  ☑ GDPR                                                         │
│  ☑ CCPA                                                         │
│  ☐ HIPAA                                                        │
│  ☑ PCI-DSS                                                      │
│                                                                  │
│  Severity threshold: [High ▼]                                    │
│                                                                  │
│  [Apply] [Cancel]                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Features

#### Inspections

Compliance issues appear as inspections:

```java
// Warning: GDPR Art. 32 - Sensitive data not encrypted
String creditCard = customer.getCreditCardNumber();
```

#### Intention Actions

Press Alt+Enter for fixes:

```
Intention Actions:
├── 🛡️ Encrypt sensitive data before storage
├── 🛡️ Use tokenization service
├── 📖 View PCI-DSS requirement
└── ⚪ Suppress for this statement
```

#### Tool Window

Open the ComplianceAgent tool window (View → Tool Windows → ComplianceAgent):

```
┌─────────────────────────────────────────────────────────────────┐
│  ComplianceAgent                                          [≡][×] │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Project Compliance: 87%                                         │
│                                                                  │
│  Issues by Framework:                                            │
│  ├── GDPR (3)                                                   │
│  │   ├── ⚠️ HIGH: src/api/users.py:36                          │
│  │   ├── ⚠️ MEDIUM: src/services/email.py:22                   │
│  │   └── ℹ️ LOW: src/models/user.py:15                         │
│  └── PCI-DSS (1)                                                │
│      └── ⚠️ HIGH: src/payments/card.java:89                    │
│                                                                  │
│  [Scan Project] [Generate Report] [Settings]                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Common Patterns

### Suppressing False Positives

When the IDE flags a false positive:

#### Inline Suppression

```python
# noinspection ComplianceAgent-GDPR-ART-7
def internal_data_transfer(data):
    # This is internal processing, consent already verified at entry point
    ...
```

#### File-Level Suppression

Add to the top of the file:

```python
# complianceagent: ignore-file GDPR-ART-7
```

#### Project-Level Suppression

Add to `.complianceagent/ignores.yml`:

```yaml
ignores:
  - rule: GDPR-ART-7
    paths:
      - src/internal/**
    reason: "Internal services, consent verified at API boundary"
```

### Working with Frameworks

#### Enabling/Disabling Frameworks

Per-project frameworks in `.complianceagent/config.yml`:

```yaml
frameworks:
  enabled:
    - gdpr
    - ccpa
  disabled:
    - hipaa  # Not applicable to this project
```

#### Framework-Specific Settings

```yaml
frameworks:
  gdpr:
    severity_override:
      consent: critical  # Make consent issues critical
    
  pci-dss:
    scan_paths:
      - src/payments/**
      - src/checkout/**
```

## Performance

### Optimizing IDE Performance

For large projects:

```json
{
  "complianceagent.scanOnSave": true,
  "complianceagent.scanOnType": false,  // Disable real-time for performance
  "complianceagent.excludePaths": [
    "node_modules/**",
    "venv/**",
    "build/**",
    ".git/**"
  ],
  "complianceagent.maxFileSizeKB": 500
}
```

### Background Analysis

Enable background analysis for better performance:

```json
{
  "complianceagent.backgroundAnalysis": true,
  "complianceagent.analysisDelay": 2000  // ms after typing stops
}
```

## Troubleshooting

### "Extension not connecting"

1. Check API key is correct
2. Verify network connectivity to ComplianceAgent API
3. Check extension logs: View → Output → ComplianceAgent

### "No issues detected"

1. Verify frameworks are enabled
2. Check severity threshold isn't too high
3. Try manual scan: Ctrl+Shift+P → "ComplianceAgent: Scan File"

### "Too many false positives"

1. Add suppressions for known patterns
2. Increase severity threshold
3. Configure exclude paths for non-production code

---

Next: Learn about [Audit Trails](./audit-trails) for compliance evidence.
