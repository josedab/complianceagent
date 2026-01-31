# CI/CD Integration Guide

This guide covers integrating ComplianceAgent into your CI/CD pipelines to automatically check code compliance before merging.

## Table of Contents

- [Overview](#overview)
- [GitHub Actions](#github-actions)
- [GitLab CI](#gitlab-ci)
- [Jenkins](#jenkins)
- [Azure DevOps](#azure-devops)
- [SARIF Output](#sarif-output)
- [PR Comments](#pr-comments)
- [Compliance Gates](#compliance-gates)
- [Troubleshooting](#troubleshooting)

---

## Overview

ComplianceAgent provides CI/CD integrations that:

1. **Scan code changes** for compliance issues
2. **Block non-compliant PRs** from merging
3. **Generate SARIF reports** for GitHub Security tab
4. **Add inline comments** to highlight issues
5. **Track compliance trends** over time

### Supported Frameworks

All regulatory frameworks supported by ComplianceAgent can be checked in CI/CD:
- GDPR, CCPA, HIPAA, PIPL
- PCI-DSS, SOC 2, ISO 27001
- EU AI Act, NIST AI RMF

---

## GitHub Actions

### Basic Setup

Create `.github/workflows/compliance-check.yml`:

```yaml
name: Compliance Check

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  compliance:
    name: Check Compliance
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for accurate analysis

      - name: Run ComplianceAgent Check
        uses: complianceagent/compliance-action@v1
        with:
          api-token: ${{ secrets.COMPLIANCEAGENT_API_TOKEN }}
          frameworks: gdpr,ccpa,hipaa
          fail-on: critical  # critical, major, minor, or none
          
      - name: Upload SARIF results
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: compliance-results.sarif
```

### Advanced Configuration

```yaml
name: Compliance Check

on:
  pull_request:
    branches: [main, develop]
    paths:
      - 'src/**'
      - 'api/**'
      - '!**/*.md'
      - '!**/*.txt'

permissions:
  contents: read
  pull-requests: write
  security-events: write

jobs:
  compliance:
    name: Compliance Analysis
    runs-on: ubuntu-latest
    timeout-minutes: 15
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run ComplianceAgent
        id: compliance
        uses: complianceagent/compliance-action@v1
        with:
          api-token: ${{ secrets.COMPLIANCEAGENT_API_TOKEN }}
          api-url: https://api.complianceagent.ai
          
          # Frameworks to check
          frameworks: gdpr,ccpa,hipaa,pci-dss
          
          # Paths to analyze (glob patterns)
          include-paths: |
            src/**
            api/**
            lib/**
          
          # Paths to exclude
          exclude-paths: |
            **/*.test.ts
            **/*.spec.ts
            **/fixtures/**
          
          # Failure conditions
          fail-on: major  # critical, major, minor, none
          max-issues: 10   # Fail if more than N issues
          
          # Output options
          output-format: sarif,json,markdown
          output-file: compliance-results
          
          # PR integration
          add-pr-comment: true
          add-inline-comments: true
          
          # Baseline (ignore existing issues)
          baseline-branch: main

      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: compliance-results.sarif
          category: compliance

      - name: Comment on PR
        if: github.event_name == 'pull_request' && steps.compliance.outputs.issues-count > 0
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('compliance-results.md', 'utf8');
            github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: report
            });

      - name: Fail if issues found
        if: steps.compliance.outputs.failed == 'true'
        run: |
          echo "::error::Compliance check failed with ${{ steps.compliance.outputs.issues-count }} issues"
          exit 1
```

### Action Outputs

| Output | Description |
|--------|-------------|
| `issues-count` | Total number of issues found |
| `critical-count` | Number of critical issues |
| `major-count` | Number of major issues |
| `minor-count` | Number of minor issues |
| `failed` | `true` if check failed |
| `score` | Compliance score (0-100) |

### Secrets Required

| Secret | Description |
|--------|-------------|
| `COMPLIANCEAGENT_API_TOKEN` | API token from ComplianceAgent dashboard |

---

## GitLab CI

### Basic Setup

Add to `.gitlab-ci.yml`:

```yaml
stages:
  - test
  - compliance
  - deploy

compliance-check:
  stage: compliance
  image: complianceagent/ci-scanner:latest
  variables:
    COMPLIANCEAGENT_API_TOKEN: $COMPLIANCEAGENT_API_TOKEN
  script:
    - complianceagent scan
      --frameworks gdpr,ccpa,hipaa
      --fail-on critical
      --output-format sarif,json
      --output-file compliance-results
  artifacts:
    reports:
      sast: compliance-results.sarif
    paths:
      - compliance-results.json
    when: always
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Advanced Configuration

```yaml
compliance-check:
  stage: compliance
  image: complianceagent/ci-scanner:latest
  variables:
    COMPLIANCEAGENT_API_TOKEN: $COMPLIANCEAGENT_API_TOKEN
    COMPLIANCEAGENT_API_URL: https://api.complianceagent.ai
  before_script:
    - echo "Analyzing ${CI_PROJECT_NAME}"
  script:
    - |
      complianceagent scan \
        --frameworks gdpr,ccpa,hipaa,pci-dss \
        --include-paths "src/**,api/**,lib/**" \
        --exclude-paths "**/*.test.ts,**/fixtures/**" \
        --fail-on major \
        --max-issues 10 \
        --output-format sarif,json,gitlab \
        --output-file compliance-results \
        --baseline-branch $CI_DEFAULT_BRANCH
  after_script:
    - |
      if [ -f compliance-results.json ]; then
        echo "Issues found: $(jq '.issues | length' compliance-results.json)"
      fi
  artifacts:
    reports:
      sast: compliance-results.sarif
    paths:
      - compliance-results.json
      - compliance-results.md
    expire_in: 30 days
    when: always
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  allow_failure: false

# Add MR comment with results
compliance-comment:
  stage: compliance
  needs: [compliance-check]
  image: curlimages/curl:latest
  script:
    - |
      if [ -f compliance-results.md ]; then
        curl --request POST \
          --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
          --form "body=$(cat compliance-results.md)" \
          "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/merge_requests/${CI_MERGE_REQUEST_IID}/notes"
      fi
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

---

## Jenkins

### Jenkinsfile

```groovy
pipeline {
    agent any
    
    environment {
        COMPLIANCEAGENT_API_TOKEN = credentials('complianceagent-token')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Compliance Check') {
            steps {
                script {
                    docker.image('complianceagent/ci-scanner:latest').inside {
                        sh '''
                            complianceagent scan \
                                --frameworks gdpr,ccpa,hipaa \
                                --fail-on critical \
                                --output-format sarif,json \
                                --output-file compliance-results
                        '''
                    }
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'compliance-results.*', fingerprint: true
                    recordIssues(
                        tools: [sarif(pattern: 'compliance-results.sarif')],
                        qualityGates: [
                            [threshold: 1, type: 'TOTAL_HIGH', criticality: 'FAILURE'],
                            [threshold: 5, type: 'TOTAL_NORMAL', criticality: 'FAILURE']
                        ]
                    )
                }
            }
        }
        
        stage('Deploy') {
            when {
                branch 'main'
                expression { currentBuild.result == 'SUCCESS' }
            }
            steps {
                // Deploy steps
            }
        }
    }
    
    post {
        failure {
            slackSend(
                channel: '#compliance-alerts',
                color: 'danger',
                message: "Compliance check failed: ${env.BUILD_URL}"
            )
        }
    }
}
```

### Declarative Pipeline with Shared Library

```groovy
@Library('complianceagent-shared') _

pipeline {
    agent any
    
    stages {
        stage('Compliance') {
            steps {
                complianceCheck(
                    frameworks: ['gdpr', 'ccpa', 'hipaa'],
                    failOn: 'critical',
                    addPRComment: true
                )
            }
        }
    }
}
```

---

## Azure DevOps

### azure-pipelines.yml

```yaml
trigger:
  branches:
    include:
      - main
      - develop

pr:
  branches:
    include:
      - main

variables:
  - group: complianceagent-secrets

stages:
  - stage: Compliance
    displayName: 'Compliance Check'
    jobs:
      - job: Scan
        displayName: 'Run ComplianceAgent'
        pool:
          vmImage: 'ubuntu-latest'
        steps:
          - checkout: self
            fetchDepth: 0

          - task: Docker@2
            displayName: 'Run Compliance Scan'
            inputs:
              command: 'run'
              arguments: |
                --rm
                -v $(System.DefaultWorkingDirectory):/workspace
                -w /workspace
                -e COMPLIANCEAGENT_API_TOKEN=$(COMPLIANCEAGENT_API_TOKEN)
                complianceagent/ci-scanner:latest
                complianceagent scan
                  --frameworks gdpr,ccpa,hipaa
                  --fail-on critical
                  --output-format sarif,json
                  --output-file compliance-results

          - task: PublishBuildArtifacts@1
            displayName: 'Publish Results'
            inputs:
              pathToPublish: 'compliance-results.json'
              artifactName: 'compliance-report'
            condition: always()

          - task: PublishSecurityAnalysisLogs@3
            displayName: 'Publish SARIF'
            inputs:
              ArtifactName: 'CodeAnalysisLogs'
              ArtifactType: 'Container'
              AllTools: false
              ToolLogsNotFoundAction: 'Standard'
            condition: always()

          - task: PostCommentToPullRequest@1
            displayName: 'Comment on PR'
            condition: and(succeeded(), eq(variables['Build.Reason'], 'PullRequest'))
            inputs:
              commentFile: 'compliance-results.md'
```

---

## SARIF Output

ComplianceAgent generates [SARIF](https://sarifweb.azurewebsites.net/) (Static Analysis Results Interchange Format) reports compatible with:

- GitHub Security tab
- GitLab Security Dashboard
- Azure DevOps Security
- Visual Studio Code SARIF Viewer

### SARIF Structure

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
          "informationUri": "https://complianceagent.ai",
          "rules": [
            {
              "id": "GDPR-001",
              "name": "MissingConsentMechanism",
              "shortDescription": {
                "text": "Missing consent collection mechanism"
              },
              "fullDescription": {
                "text": "GDPR Article 7 requires explicit consent collection..."
              },
              "helpUri": "https://docs.complianceagent.ai/rules/GDPR-001",
              "defaultConfiguration": {
                "level": "error"
              }
            }
          ]
        }
      },
      "results": [
        {
          "ruleId": "GDPR-001",
          "level": "error",
          "message": {
            "text": "User data collection without consent mechanism detected"
          },
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {
                  "uri": "src/api/users.py"
                },
                "region": {
                  "startLine": 45,
                  "startColumn": 1,
                  "endLine": 52,
                  "endColumn": 1
                }
              }
            }
          ],
          "fixes": [
            {
              "description": {
                "text": "Add consent collection before data processing"
              },
              "artifactChanges": [
                {
                  "artifactLocation": {
                    "uri": "src/api/users.py"
                  },
                  "replacements": [
                    {
                      "deletedRegion": {
                        "startLine": 45,
                        "endLine": 45
                      },
                      "insertedContent": {
                        "text": "    consent = await get_user_consent(user_id)\n    if not consent.is_valid:\n        raise ConsentRequiredError()\n"
                      }
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

---

## PR Comments

ComplianceAgent can add detailed comments to pull requests:

### Summary Comment

```markdown
## 🔍 ComplianceAgent Scan Results

**Status**: ⚠️ Issues Found

| Severity | Count |
|----------|-------|
| 🔴 Critical | 1 |
| 🟠 Major | 3 |
| 🟡 Minor | 5 |

### Critical Issues

#### GDPR-001: Missing consent mechanism
**File**: `src/api/users.py:45`  
**Framework**: GDPR  
**Description**: User data collection without explicit consent

<details>
<summary>Suggested Fix</summary>

```python
consent = await get_user_consent(user_id)
if not consent.is_valid:
    raise ConsentRequiredError()
```

</details>

---

📊 [View Full Report](https://complianceagent.ai/reports/xxx)
```

### Inline Comments

ComplianceAgent can add inline review comments directly on the affected lines:

```
src/api/users.py line 45:

🔴 **GDPR-001**: Missing consent mechanism

This code collects user data without verifying consent. GDPR Article 7 
requires explicit consent before processing personal data.

**Suggested Fix:**
Add consent verification before data collection.
```

---

## Compliance Gates

### Blocking PRs

Configure which issues block merging:

```yaml
# GitHub Action
fail-on: critical  # Block on critical only
# or
fail-on: major     # Block on critical and major
# or
fail-on: minor     # Block on any issue
# or
fail-on: none      # Never block (warning only)
```

### Issue Thresholds

```yaml
# Allow up to N issues before failing
max-issues: 10
max-critical: 0    # No critical allowed
max-major: 5       # Up to 5 major issues
```

### Branch Protection Rules

Set up GitHub branch protection to require compliance checks:

1. Go to **Settings** → **Branches** → **Branch protection rules**
2. Select your main branch
3. Enable **Require status checks to pass**
4. Add `compliance-check` to required checks

---

## Troubleshooting

### Common Issues

**1. Scan timeout**
```yaml
# Increase timeout
timeout-minutes: 30
```

**2. API rate limiting**
```yaml
# Add delay between API calls
scan-delay: 1000  # milliseconds
```

**3. Large repository scanning**
```yaml
# Scan only changed files
scan-mode: diff  # instead of 'full'
baseline-branch: main
```

**4. Authentication errors**
```bash
# Verify token
curl -H "Authorization: Bearer $TOKEN" \
  https://api.complianceagent.ai/api/v1/auth/me
```

### Debug Mode

Enable verbose logging:

```yaml
# GitHub Actions
- name: Run ComplianceAgent
  uses: complianceagent/compliance-action@v1
  with:
    debug: true
    api-token: ${{ secrets.COMPLIANCEAGENT_API_TOKEN }}
```

```bash
# CLI
complianceagent scan --debug --verbose
```

### Support

- **Documentation**: https://docs.complianceagent.ai/cicd
- **Issues**: https://github.com/complianceagent/compliance-action/issues
- **Email**: support@complianceagent.ai

---

## Next Steps

- [Configuration Reference](configuration.md) - Environment variables
- [API Reference](../api/reference.md) - API documentation
- [Framework Guides](../frameworks/) - Framework-specific guidance
