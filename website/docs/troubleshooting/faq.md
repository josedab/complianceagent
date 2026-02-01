---
sidebar_position: 2
title: FAQ
description: Frequently asked questions about ComplianceAgent
---

# Frequently Asked Questions

Common questions about ComplianceAgent.

## General

### What is ComplianceAgent?

ComplianceAgent is an AI-powered regulatory compliance platform that monitors regulatory changes, analyzes your codebase for compliance gaps, and generates fixes using the GitHub Copilot SDK. It helps engineering and compliance teams stay ahead of evolving regulations.

### Which regulatory frameworks are supported?

ComplianceAgent supports 100+ frameworks including:

- **Privacy:** GDPR, CCPA/CPRA, HIPAA, LGPD, PDPA
- **Security:** SOC 2, ISO 27001, PCI-DSS, NIS2
- **AI:** EU AI Act, NIST AI RMF
- **ESG:** CSRD, SEC Climate Rules

See [Frameworks Overview](../frameworks/overview) for the complete list.

### What programming languages are supported?

ComplianceAgent supports code analysis and fix generation for:

- Python
- JavaScript / TypeScript
- Java
- Go
- C# / .NET
- Ruby
- PHP
- Rust

### Is ComplianceAgent open source?

Yes, ComplianceAgent is open source under the MIT License. Enterprise features are available for teams needing SSO, advanced audit trails, and premium support.

## Pricing

### Is there a free tier?

Yes, the free tier includes:
- 3 repositories
- 2 frameworks
- 1,000 API calls/month
- 30-day audit retention

### What's included in the Pro plan?

Pro plan ($99/month) includes:
- 25 repositories
- All frameworks
- 50,000 API calls/month
- AI-powered fixes
- 2-year audit retention
- Priority support

### Do you offer enterprise pricing?

Yes, enterprise plans include unlimited repositories, custom integrations, SSO/SAML, dedicated support, and SLA guarantees. [Contact sales](mailto:sales@complianceagent.io) for pricing.

## Security

### Where is my data stored?

For cloud users, data is stored in AWS us-east-1 with encryption at rest. Self-hosted deployments store data wherever you deploy.

### Do you access my source code?

ComplianceAgent analyzes your code for compliance issues. We:
- Never store your complete source code
- Only retain code snippets relevant to compliance issues
- Never use your code to train AI models
- Delete analysis data when you disconnect a repository

### Is ComplianceAgent SOC 2 compliant?

Yes, ComplianceAgent cloud is SOC 2 Type II certified. Enterprise customers can request our SOC 2 report.

### Can I self-host ComplianceAgent?

Yes, ComplianceAgent can be deployed on-premises or in your own cloud. See [Deployment guides](../deployment/docker).

## Features

### How does AI fix generation work?

ComplianceAgent uses the GitHub Copilot SDK to analyze compliance issues and generate contextual fixes. The AI considers:
- Your existing code patterns
- Framework best practices
- The specific requirement being addressed

All fixes are suggestions that require human review before applying.

### How often are regulations monitored?

We monitor regulatory sources continuously and process updates within 24 hours of publication. You'll receive notifications based on your preferences (immediate, daily digest, or weekly).

### Can I customize compliance rules?

Yes, you can:
- Enable/disable specific requirements
- Set custom severity levels
- Add custom rules using YAML definitions
- Exclude files or patterns from scanning

### Does ComplianceAgent work with monorepos?

Yes, ComplianceAgent supports monorepos. You can:
- Scan the entire repository
- Configure different frameworks per directory
- Get per-project compliance scores

## Integration

### Which version control systems are supported?

- GitHub (Cloud & Enterprise Server)
- GitLab (Cloud & Self-Managed)
- Bitbucket (Cloud & Server)
- Azure DevOps

### Can I use ComplianceAgent in CI/CD?

Yes, we provide:
- GitHub Actions
- GitLab CI templates
- Jenkins plugin
- Generic webhook-based integration

See [CI/CD Integration guide](../guides/cicd-integration).

### Does ComplianceAgent integrate with issue trackers?

Yes, we integrate with:
- GitHub Issues
- Jira
- Linear
- Asana

Compliance issues can be automatically synced to your issue tracker.

### Can I use ComplianceAgent with my IDE?

Yes, we provide extensions for:
- VS Code
- JetBrains IDEs (IntelliJ, PyCharm, etc.)

See [IDE Integration guide](../guides/ide-integration).

## Technical

### What's the scan impact on my CI pipeline?

Scanning adds 2-5 minutes depending on repository size. Incremental scans (only changed files) typically complete in under 1 minute.

### How do I handle false positives?

1. Mark the issue as "Won't Fix" with a reason
2. Add a comment explaining why it's not applicable
3. Use inline comments to suppress specific checks:
```python
# complianceagent: ignore gdpr-art-17
```

### Can I scan branches other than main?

Yes, you can:
- Scan any branch on-demand
- Configure automatic scanning for specific branches
- Compare compliance between branches

### How do I export compliance data?

Use the API or dashboard to export:
- Compliance reports (PDF, CSV)
- Audit logs (JSON, CSV)
- Evidence packages (ZIP)

```bash
curl -X POST http://localhost:8000/api/v1/compliance/reports/export \
  -d '{"format": "pdf", "repository_ids": ["repo_123"]}'
```

## Compliance & Legal

### Does using ComplianceAgent make me compliant?

ComplianceAgent helps identify and fix compliance gaps, but it's a tool to assist your compliance program—not a replacement for legal advice or a compliance audit. Always consult with qualified compliance professionals.

### How do you handle GDPR for EU users?

ComplianceAgent is GDPR-compliant:
- Data Processing Agreement available
- Standard Contractual Clauses for transfers
- EU data residency option (Enterprise)
- Right to deletion honored

### Can I use ComplianceAgent for regulated industries?

Yes, many healthcare, financial services, and government organizations use ComplianceAgent. Contact us for industry-specific requirements.

## Troubleshooting

### My scan is taking too long

1. Enable incremental scanning
2. Exclude large vendor directories
3. Increase scan timeout
4. Check for large binary files

See [Troubleshooting guide](./common-issues#scan-timeout).

### Fix generation isn't working

1. Verify your GitHub token is valid
2. Check you have Copilot access
3. Ensure the issue has enough code context

See [Troubleshooting guide](./common-issues#fix-not-generated).

### Where can I get help?

- **Documentation:** You're here!
- **Community:** [GitHub Discussions](https://github.com/complianceagent/complianceagent/discussions)
- **Bug Reports:** [GitHub Issues](https://github.com/complianceagent/complianceagent/issues)
- **Enterprise Support:** support@complianceagent.io

---

Still have questions? [Ask in our community](https://github.com/complianceagent/complianceagent/discussions/new?category=q-a)
