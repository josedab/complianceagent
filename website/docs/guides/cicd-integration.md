---
sidebar_position: 4
title: CI/CD Integration
description: Add compliance checks to your CI/CD pipeline
---

# CI/CD Integration

Block non-compliant code from reaching production with ComplianceAgent's CI/CD integration.

## Overview

ComplianceAgent integrates with your CI/CD pipeline to:

- **Scan PRs** - Check code changes against compliance requirements
- **Block merges** - Prevent non-compliant code from merging
- **Generate reports** - SARIF format for GitHub Security tab
- **Incremental analysis** - Only check changed files for speed

## GitHub Actions

### Basic Setup

Add this workflow to `.github/workflows/compliance.yml`:

```yaml
name: Compliance Check

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  compliance:
    name: Compliance Scan
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Needed for diff analysis
      
      - name: Run ComplianceAgent Scan
        uses: complianceagent/scan-action@v1
        with:
          api-key: ${{ secrets.COMPLIANCEAGENT_API_KEY }}
          frameworks: gdpr,ccpa,hipaa
          fail-on-severity: high
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: compliance-results.sarif
```

### Configuration Options

```yaml
- name: Run ComplianceAgent Scan
  uses: complianceagent/scan-action@v1
  with:
    # Required
    api-key: ${{ secrets.COMPLIANCEAGENT_API_KEY }}
    
    # Frameworks to check (comma-separated)
    frameworks: gdpr,ccpa
    
    # Fail on severity: critical, high, medium, low
    fail-on-severity: high
    
    # Only scan changed files (faster)
    incremental: true
    
    # Custom config file
    config-file: .complianceagent/config.yml
    
    # Output formats
    output-format: sarif,json
    
    # Base branch for comparison
    base-ref: main
```

### PR Status Check

The action reports status back to GitHub:

```
┌─────────────────────────────────────────────────────────────────┐
│              PR #142: Add user profile feature                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Checks:                                                         │
│  ✅ Build                    Passed                              │
│  ✅ Tests                    47 passed                           │
│  ⚠️ Compliance Check         1 high severity issue               │
│                                                                  │
│  ComplianceAgent found issues:                                   │
│  • HIGH: Personal data collected without consent check           │
│    File: src/api/profiles.py:34                                 │
│    Requirement: GDPR Art. 7                                      │
│                                                                  │
│  [View Details] [Generate Fix]                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## GitLab CI

### Basic Setup

Add to `.gitlab-ci.yml`:

```yaml
compliance:
  stage: test
  image: complianceagent/scanner:latest
  script:
    - complianceagent scan
      --api-key $COMPLIANCEAGENT_API_KEY
      --frameworks gdpr,ccpa
      --output gitlab-code-quality
      --fail-on high
  artifacts:
    reports:
      codequality: compliance-report.json
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

### Code Quality Integration

Results appear in GitLab's Code Quality view:

```json
[
  {
    "description": "GDPR Art. 7: Consent not verified before data collection",
    "fingerprint": "gdpr-art-7-consent-check-profiles",
    "severity": "major",
    "location": {
      "path": "src/api/profiles.py",
      "lines": {
        "begin": 34,
        "end": 45
      }
    }
  }
]
```

## Jenkins

### Pipeline Integration

```groovy
pipeline {
    agent any
    
    stages {
        stage('Compliance Check') {
            steps {
                script {
                    def result = sh(
                        script: '''
                            curl -X POST https://api.complianceagent.ai/v1/scan \
                                -H "Authorization: Bearer ${COMPLIANCEAGENT_API_KEY}" \
                                -H "Content-Type: application/json" \
                                -d '{
                                    "repository": "${GIT_URL}",
                                    "commit": "${GIT_COMMIT}",
                                    "frameworks": ["gdpr", "ccpa"],
                                    "base_commit": "${GIT_PREVIOUS_COMMIT}"
                                }'
                        ''',
                        returnStdout: true
                    )
                    
                    def scanResult = readJSON text: result
                    
                    if (scanResult.high_severity_count > 0) {
                        error "Compliance check failed: ${scanResult.high_severity_count} high severity issues"
                    }
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'compliance-*.json', allowEmptyArchive: true
        }
    }
}
```

## CircleCI

### Configuration

Add to `.circleci/config.yml`:

```yaml
version: 2.1

orbs:
  complianceagent: complianceagent/scanner@1.0

workflows:
  build-and-test:
    jobs:
      - build
      - test
      - complianceagent/scan:
          api-key: COMPLIANCEAGENT_API_KEY
          frameworks: "gdpr,hipaa"
          fail-on-severity: high
          requires:
            - build
```

## SARIF Output

### GitHub Security Tab

SARIF results integrate with GitHub's Security tab:

```json
{
  "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "ComplianceAgent",
          "version": "1.0.0",
          "rules": [
            {
              "id": "GDPR-ART-7",
              "name": "ConsentRequired",
              "shortDescription": {
                "text": "Consent verification required"
              },
              "fullDescription": {
                "text": "GDPR Article 7 requires that consent be obtained before processing personal data."
              },
              "helpUri": "https://complianceagent.ai/docs/rules/gdpr-art-7"
            }
          ]
        }
      },
      "results": [
        {
          "ruleId": "GDPR-ART-7",
          "level": "error",
          "message": {
            "text": "Personal data is collected without verifying user consent"
          },
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {
                  "uri": "src/api/profiles.py"
                },
                "region": {
                  "startLine": 34,
                  "endLine": 45
                }
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### Viewing in GitHub

Navigate to **Security → Code scanning alerts** to see compliance issues alongside other security findings.

## Incremental Scanning

For faster PR checks, enable incremental scanning:

### How It Works

1. Identifies files changed in the PR
2. Only analyzes those files
3. Reports issues in changed code only

### Configuration

```yaml
# .complianceagent/config.yml
ci:
  incremental: true
  base_branch: main
  
  # Still do full scans periodically
  full_scan_schedule: "0 0 * * 0"  # Weekly
```

### PR-Specific vs Full Repository

| Scan Type | When Used | Speed | Coverage |
|-----------|-----------|-------|----------|
| Incremental | PRs, feature branches | ~10s | Changed files |
| Full | Main branch, releases | ~2min | Entire repo |

## Severity Thresholds

Configure what blocks merges:

```yaml
# Strict: Block on any issue
fail-on-severity: low

# Standard: Block on high+ (recommended)
fail-on-severity: high

# Lenient: Block only critical
fail-on-severity: critical

# Per-framework thresholds
thresholds:
  gdpr: high
  hipaa: medium  # Stricter for healthcare
  ccpa: high
```

## Bypass Options

Sometimes you need to bypass checks:

### Skip via Commit Message

```bash
git commit -m "feat: urgent hotfix [compliance-skip]"
```

### Skip via Label

Add label `compliance-bypass` to the PR (requires appropriate permissions).

### Audit Trail

All bypasses are recorded:

```json
{
  "event": "compliance_bypass",
  "timestamp": "2024-01-15T10:30:00Z",
  "user": "john@acme.com",
  "pr": "#142",
  "reason": "commit_message_skip",
  "issues_bypassed": 2
}
```

## Custom Rules

Add organization-specific rules:

```yaml
# .complianceagent/rules.yml
rules:
  - id: ACME-001
    name: InternalDataClassification
    description: "All data handling must include classification"
    severity: high
    pattern:
      type: function
      name_matches: "(save|store|persist).*"
      must_contain:
        - "data_classification"
    frameworks:
      - internal
```

## Notifications

Configure CI/CD notifications:

```yaml
notifications:
  on_failure:
    - type: slack
      channel: "#ci-alerts"
      webhook: ${{ secrets.SLACK_WEBHOOK }}
    
    - type: email
      recipients:
        - compliance-team@acme.com
  
  on_success:
    - type: slack
      channel: "#compliance"
      message: "PR #{pr_number} passed compliance checks"
```

## Troubleshooting

### "Scan taking too long"

- Enable incremental scanning
- Exclude test directories
- Reduce framework count for PRs

### "False positives blocking PR"

- Add inline suppressions (see below)
- Update patterns in config
- Report false positive to improve detection

### Inline Suppressions

Suppress specific issues in code:

```python
# complianceagent-ignore: GDPR-ART-7 - consent obtained via SSO
def get_user_profile(user_id):
    # This endpoint is only accessible after SSO consent
    ...
```

### "API key not working"

- Verify key in repository secrets
- Check key hasn't expired
- Ensure key has CI/CD scope

---

Next: Learn about [IDE Integration](./ide-integration) for real-time compliance feedback.
