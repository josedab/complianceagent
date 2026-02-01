---
sidebar_position: 1
title: Connecting Repositories
description: Connect your GitHub repositories for compliance analysis
---

# Connecting Repositories

This guide walks you through connecting GitHub repositories to ComplianceAgent for automated compliance analysis.

## Prerequisites

- A ComplianceAgent account with an organization
- GitHub account with access to the repository
- Repository admin access (for private repositories)

## Connection Methods

### Method 1: Public Repositories

For public repositories, you can connect directly using the URL:

1. Go to **Repositories** in the sidebar
2. Click **Add Repository**
3. Enter the repository URL:
   ```
   https://github.com/username/repository
   ```
4. Click **Connect**

ComplianceAgent will clone and analyze the repository.

### Method 2: GitHub App (Recommended)

For private repositories and better integration, install the ComplianceAgent GitHub App:

#### Step 1: Install the GitHub App

1. Go to **Settings → Integrations**
2. Click **Install GitHub App**
3. You'll be redirected to GitHub
4. Select your organization or personal account
5. Choose repositories to grant access:
   - **All repositories** - Easiest, grants access to everything
   - **Selected repositories** - More secure, choose specific repos

#### Step 2: Grant Permissions

The GitHub App requests these permissions:

| Permission | Reason |
|------------|--------|
| Read code | Analyze codebase for compliance |
| Read metadata | Repository information |
| Write pull requests | Create compliance fix PRs |
| Write issues | Create compliance issues |
| Read/write checks | CI/CD integration |

#### Step 3: Add Repositories

After installation:

1. Return to ComplianceAgent
2. Go to **Repositories → Add Repository**
3. Your accessible repos appear in a dropdown
4. Select and click **Connect**

## Initial Analysis

When you connect a repository, ComplianceAgent:

1. **Clones the repository** (shallow clone)
2. **Indexes the codebase** - Files, structure, dependencies
3. **Runs initial analysis** - Identifies code patterns
4. **Maps to frameworks** - Connects code to enabled regulations

This typically takes 1-5 minutes depending on repository size.

### Monitor Progress

Watch analysis progress in the dashboard:

```
Repository: acme/backend
Status: Analyzing...

[████████████░░░░░░░░] 60%

Steps:
✅ Repository cloned
✅ Files indexed (1,247 files)
✅ Dependencies analyzed
⏳ Running compliance mapping
○ Generating initial report
```

## Repository Settings

After connecting, configure repository-specific settings:

### Compliance Frameworks

Select which frameworks apply to this repository:

```yaml
# Example: A healthcare SaaS backend
frameworks:
  - gdpr          # EU users
  - hipaa         # US healthcare data
  - ccpa          # California users
```

### Analysis Scope

Configure what gets analyzed:

```yaml
# .complianceagent/config.yml
analysis:
  include:
    - src/**
    - lib/**
    - app/**
  
  exclude:
    - tests/**
    - docs/**
    - fixtures/**
    - "**/test_*.py"
    - "**/*.test.ts"
```

### Branch Settings

Choose which branches to monitor:

```yaml
branches:
  # Main branch for compliance status
  main: main
  
  # Additional branches to analyze
  analyze:
    - develop
    - release/*
  
  # Branches for PR checks
  pr_checks:
    - main
    - develop
```

## Webhook Configuration

Enable webhooks for real-time analysis:

### Automatic Setup

If using the GitHub App, webhooks are configured automatically.

### Manual Setup

For manual webhook configuration:

1. Go to your repository on GitHub
2. Navigate to **Settings → Webhooks → Add webhook**
3. Configure:
   - **Payload URL**: `https://api.complianceagent.ai/webhooks/github`
   - **Content type**: `application/json`
   - **Secret**: Copy from ComplianceAgent settings
   - **Events**: Select:
     - Push events
     - Pull request events
     - Branch or tag creation

## Multi-Repository Setup

For organizations with multiple repositories:

### Bulk Import

Import multiple repositories at once:

1. Go to **Repositories → Bulk Import**
2. Filter by:
   - Language (Python, TypeScript, etc.)
   - Topics (api, backend, etc.)
   - Visibility (public/private)
3. Select repositories
4. Click **Import Selected**

### Repository Groups

Organize repositories into groups:

```yaml
groups:
  - name: Backend Services
    repositories:
      - acme/api-gateway
      - acme/user-service
      - acme/payment-service
    frameworks:
      - gdpr
      - pci-dss
  
  - name: Frontend Apps
    repositories:
      - acme/web-app
      - acme/mobile-app
    frameworks:
      - gdpr
      - ccpa
```

## Repository Health

Monitor repository connection health:

| Status | Meaning | Action |
|--------|---------|--------|
| 🟢 Connected | Working normally | None |
| 🟡 Stale | Last sync >24h ago | Check webhooks |
| 🔴 Disconnected | Cannot access | Re-authenticate |
| ⚪ Pending | Initial analysis | Wait |

### Troubleshooting Connection Issues

#### "Repository not found"

- Verify the URL is correct
- Check that you have access to the repository
- For private repos, ensure GitHub App is installed

#### "Permission denied"

- Reinstall the GitHub App
- Verify the app has access to this specific repository
- Check organization settings allow the app

#### "Analysis stuck"

- Large repositories may take longer
- Check system status in **Settings → System**
- Contact support if stuck >30 minutes

## Disconnecting Repositories

To remove a repository:

1. Go to **Repositories**
2. Find the repository
3. Click **Settings → Disconnect**
4. Confirm disconnection

This removes:
- Compliance mappings
- Analysis history
- Generated PRs (not the PRs themselves)

The repository remains unchanged on GitHub.

## API Operations

### List Repositories

```bash
curl -X GET "http://localhost:8000/api/v1/repositories" \
  -H "Authorization: Bearer $TOKEN"
```

### Add Repository

```bash
curl -X POST "http://localhost:8000/api/v1/repositories" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "url": "https://github.com/acme/backend",
    "frameworks": ["gdpr", "hipaa"]
  }'
```

### Trigger Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/repositories/{repo_id}/analyze" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Status

```bash
curl -X GET "http://localhost:8000/api/v1/repositories/{repo_id}" \
  -H "Authorization: Bearer $TOKEN"
```

## Best Practices

### 1. Start Small

Connect one repository first, understand the results, then expand.

### 2. Use Configuration Files

Add `.complianceagent/config.yml` to your repository for consistent settings across the team.

### 3. Enable Webhooks

Real-time analysis catches issues before they reach production.

### 4. Group Related Repositories

Repositories sharing frameworks should be grouped for easier management.

### 5. Review Scope Carefully

Exclude test files and fixtures to reduce noise in compliance reports.

---

Next: Learn how to [Track Regulations](./tracking-regulations) for your connected repositories.
