---
sidebar_position: 2
title: Quick Start
description: Get productive with ComplianceAgent in under 5 minutes
---

# Quick Start

This guide gets you from zero to monitoring your first regulation in under 5 minutes.

## What You'll Accomplish

By the end of this guide, you'll have:
- ✅ A running ComplianceAgent instance
- ✅ Your first GitHub repository connected
- ✅ GDPR compliance monitoring enabled
- ✅ An initial compliance assessment

## Prerequisites

- ComplianceAgent [installed and running](./installation)
- A GitHub account with at least one repository
- 5 minutes of your time

## Step 1: Create Your Account

Open http://localhost:3000 and click **Get Started**.

Fill in your details:

```
Email: your.email@company.com
Password: (min 8 characters, 1 uppercase, 1 number)
Full Name: Your Name
```

Click **Create Account**. You'll be redirected to the dashboard.

## Step 2: Create an Organization

Organizations group your repositories and team members.

1. Click **Create Organization** in the welcome modal
2. Enter your organization details:

```
Name: Acme Corp
Slug: acme-corp (auto-generated)
```

3. Click **Create**

## Step 3: Connect a Repository

Connect your first GitHub repository for compliance analysis.

### Option A: Public Repository (Quick)

1. Go to **Repositories** in the sidebar
2. Click **Add Repository**
3. Enter the repository URL:

```
https://github.com/your-username/your-repo
```

4. Click **Analyze**

### Option B: Private Repository (Requires GitHub App)

For private repositories, you'll need to install the ComplianceAgent GitHub App:

1. Go to **Settings → Integrations**
2. Click **Install GitHub App**
3. Select your organization and repositories
4. Return to ComplianceAgent and add your repository

## Step 4: Enable GDPR Monitoring

Now let's enable GDPR compliance monitoring for your repository.

1. Go to **Regulations** in the sidebar
2. Find **GDPR** in the list and click it
3. Click **Enable for Repository**
4. Select your connected repository
5. Click **Enable**

ComplianceAgent will now:
- Monitor GDPR regulatory sources for changes
- Analyze your codebase for compliance gaps
- Alert you when action is needed

## Step 5: Run Your First Assessment

Trigger an initial compliance assessment:

1. Go to **Repositories → Your Repository**
2. Click **Run Assessment**
3. Wait for the analysis to complete (usually 1-2 minutes)

## Understanding Your Results

After the assessment completes, you'll see:

### Compliance Score

A percentage showing your current compliance level:

```
┌─────────────────────────────────────┐
│  GDPR Compliance Score              │
│                                     │
│           78%                       │
│         ████████░░                  │
│                                     │
│  12 requirements met                │
│  3 gaps identified                  │
│  2 pending review                   │
└─────────────────────────────────────┘
```

### Identified Gaps

Specific areas where your code may not comply:

| Requirement | Status | Affected Files | Action |
|-------------|--------|----------------|--------|
| Data retention limits | ⚠️ Gap | `src/db/users.py` | [Fix] |
| Consent collection | ✅ Met | - | - |
| Right to erasure | ⚠️ Gap | `src/api/users.py` | [Fix] |

### Recommended Actions

ComplianceAgent suggests specific code changes:

```python
# Gap: Missing data retention check
# File: src/db/users.py:45

# Current code:
def get_user_data(user_id):
    return db.query(User).filter_by(id=user_id).first()

# Suggested fix:
def get_user_data(user_id):
    user = db.query(User).filter_by(id=user_id).first()
    if user and user.retention_expired:
        raise DataRetentionError("User data retention period expired")
    return user
```

## Step 6: Generate a Fix (Optional)

Let ComplianceAgent generate compliant code:

1. Click **Generate Fix** on any gap
2. Review the suggested changes
3. Click **Create Pull Request** to open a PR with the fixes

The PR includes:
- Code changes implementing the fix
- Compliance context explaining why the change is needed
- Links to relevant GDPR articles

## What's Next?

You've completed the quick start! Here's what to explore next:

### Enable More Frameworks

Add additional compliance frameworks:
- **CCPA** - California Consumer Privacy Act
- **HIPAA** - Health data protection
- **SOC 2** - Security controls

Go to **Regulations** to enable more frameworks.

### Set Up Alerts

Get notified when regulations change or compliance gaps are found:

1. Go to **Settings → Notifications**
2. Enable email or Slack notifications
3. Configure alert thresholds

### Add CI/CD Integration

Block non-compliant code from merging:

1. Go to **Settings → Integrations → CI/CD**
2. Copy the GitHub Action configuration
3. Add to your repository's `.github/workflows/`

### Invite Team Members

Collaborate with your compliance and engineering teams:

1. Go to **Settings → Team**
2. Click **Invite Member**
3. Enter their email and role

## Common Quick Start Issues

### "Repository analysis failed"

This usually means:
- The repository URL is incorrect
- The repository is private and GitHub App isn't installed
- The repository has no analyzable code files

**Solution:** Verify the URL and ensure the GitHub App has access.

### "No compliance gaps found"

This could mean:
- Your code is compliant (great!)
- The framework isn't applicable to your codebase
- The analysis scope is too narrow

**Solution:** Check the framework's requirement mappings in **Regulations → GDPR → Requirements**.

### "Assessment taking too long"

Large repositories may take longer to analyze.

**Solution:** 
- Wait up to 10 minutes for large repos
- Check worker status in **Settings → System**
- For very large repos, contact support for optimization

---

**Congratulations!** You've set up ComplianceAgent and run your first compliance assessment. Continue to [Core Concepts](../core-concepts/overview) to understand how everything works.
