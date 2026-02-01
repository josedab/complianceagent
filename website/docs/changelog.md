---
sidebar_position: 10
title: Changelog
description: Release notes and version history
---

# Changelog

All notable changes to ComplianceAgent are documented here.

## [Unreleased]

### Added
- EU AI Act framework support
- Kubernetes Helm chart
- Real-time compliance scoring

### Changed
- Improved fix generation accuracy
- Faster incremental scans

### Fixed
- Memory leak in long-running scans
- GitHub App installation flow

---

## [1.4.0] - 2024-01-15

### Added
- **EU AI Act Support** - Full support for the EU AI Act including risk categorization, technical documentation requirements, and high-risk system controls
- **Multi-jurisdiction Conflict Resolution** - Automatic detection and resolution of conflicting requirements across jurisdictions
- **Audit Evidence Export** - Export evidence packages for SOC 2 and ISO 27001 audits
- **VS Code Extension** - Real-time compliance feedback in VS Code

### Changed
- Upgraded to GitHub Copilot SDK 2.0 for improved fix generation
- Improved scanning performance by 40% through parallel processing
- Enhanced GDPR requirement coverage with EDPB guidance updates

### Fixed
- Fixed false positive in HIPAA PHI detection for test files
- Resolved timeout issues when scanning large monorepos
- Fixed webhook delivery retries not respecting backoff

### Security
- Updated dependencies to address CVE-2024-XXXX
- Added rate limiting to prevent API abuse

---

## [1.3.0] - 2023-12-01

### Added
- **PCI-DSS v4.0 Support** - Complete support for PCI-DSS v4.0 requirements
- **GitLab Integration** - Connect GitLab repositories (Cloud and Self-Managed)
- **Slack Notifications** - Real-time Slack alerts for compliance issues
- **Custom Rules** - Define custom compliance rules using YAML

### Changed
- Redesigned dashboard with improved compliance visualizations
- Faster API response times through query optimization
- Updated CCPA support for CPRA amendments

### Fixed
- Fixed scanner not detecting issues in TypeScript decorators
- Resolved duplicate issue detection in multi-branch scans
- Fixed PDF export formatting issues

### Deprecated
- Legacy API v0 endpoints (removal in v2.0)

---

## [1.2.0] - 2023-10-15

### Added
- **AI Fix Generation** - Generate compliance fixes using GitHub Copilot SDK
- **Incremental Scanning** - Only scan changed files for faster CI/CD
- **Branch Comparison** - Compare compliance between branches
- **API Keys** - Generate scoped API keys for integrations

### Changed
- Improved GDPR Article 17 (deletion) detection accuracy
- Enhanced error messages for easier debugging
- Updated documentation with more examples

### Fixed
- Fixed race condition in concurrent scans
- Resolved memory issues with large file processing
- Fixed timezone handling in audit logs

---

## [1.1.0] - 2023-08-01

### Added
- **SOC 2 Type II Support** - Track all Trust Services Criteria
- **Jira Integration** - Sync compliance issues to Jira
- **Webhook Events** - Receive real-time notifications
- **Dark Mode** - Dashboard dark theme

### Changed
- Improved scanning accuracy for Python async code
- Better handling of framework-specific configuration
- Enhanced API documentation

### Fixed
- Fixed authentication token refresh issues
- Resolved scanning failures for repos with submodules
- Fixed export functionality for large datasets

---

## [1.0.0] - 2023-06-01

### Added
- Initial public release
- **Core Frameworks**: GDPR, CCPA, HIPAA, SOC 2
- **Repository Scanning**: GitHub integration
- **Compliance Dashboard**: Real-time compliance status
- **Issue Management**: Track and manage compliance issues
- **API**: RESTful API for integrations
- **Documentation**: Comprehensive guides and API reference

---

## Versioning

ComplianceAgent follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking API changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

## Upgrade Guide

### From 1.3.x to 1.4.x

No breaking changes. Update and restart:

```bash
docker compose pull
docker compose up -d
```

### From 1.2.x to 1.3.x

1. Update environment variables:
```bash
# New optional variable
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

2. Run migrations:
```bash
docker compose exec backend alembic upgrade head
```

### From 1.1.x to 1.2.x

1. Update API key usage:
```python
# Old
client = Client(token="...")

# New
client = Client(api_key="ca_live_sk_...")
```

2. Run migrations:
```bash
docker compose exec backend alembic upgrade head
```

## Release Schedule

- **Major releases**: Every 6-12 months
- **Minor releases**: Every 4-8 weeks
- **Patch releases**: As needed for critical fixes

## Getting Updates

### Cloud Users
Updates are automatically deployed. Check the version in **Settings → About**.

### Self-Hosted
1. Watch releases on GitHub
2. Pull latest images
3. Run migrations
4. Restart services

```bash
# Subscribe to releases
gh repo subscribe complianceagent/complianceagent --releases
```

---

[View full changelog on GitHub](https://github.com/complianceagent/complianceagent/blob/main/CHANGELOG.md)
