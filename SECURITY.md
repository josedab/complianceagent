# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |

## Reporting a Vulnerability

We take the security of ComplianceAgent seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

1. **Do NOT open a public GitHub issue** for security vulnerabilities.
2. Email your findings to **security@complianceagent.dev** (or use [GitHub Security Advisories](https://github.com/josedab/complianceagent/security/advisories/new)).
3. Include:
   - A description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact assessment
   - Suggested fix (if any)

### What to Expect

- **Acknowledgement** within 48 hours of your report.
- **Status update** within 5 business days with an assessment and expected timeline.
- **Resolution** — we aim to patch critical vulnerabilities within 14 days.

### Scope

The following are in scope:

- Authentication and authorization flaws
- SQL injection, XSS, CSRF, and other OWASP Top 10 issues
- Sensitive data exposure (API keys, credentials, PII leaks)
- Dependency vulnerabilities with a known exploit
- Container escape or privilege escalation

### Out of Scope

- Issues in third-party dependencies without a proof of concept
- Denial-of-service attacks requiring excessive resources
- Social engineering attacks
- Issues found through automated scanning without manual validation

### Safe Harbor

We support safe harbor for security researchers who:

- Make a good faith effort to avoid privacy violations, data destruction, and service disruption
- Only interact with accounts you own or with explicit permission
- Do not exploit a vulnerability beyond what is necessary to confirm it
- Report findings promptly

We will not pursue legal action against researchers who follow this policy.

## Security Best Practices for Contributors

- Never commit secrets, API keys, or credentials to the repository
- Use `.env` files for local configuration (these are git-ignored)
- Run `make security-check` before submitting PRs
- Keep dependencies updated and review security advisories
- Follow the principle of least privilege for database and API access
