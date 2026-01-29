# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (v0.3.0 - Next-Gen Features)
- **IDE Compliance Copilot**
  - Real-time compliance suggestions in VS Code/JetBrains
  - AI-powered quick-fix generation
  - Regulation tooltips with article references
  - Deep code block analysis
  - New API endpoints: `/api/v1/ide/suggest`, `/quickfix`, `/tooltip`, `/deep-analyze`

- **Compliance CI/CD Gates**
  - GitHub Action for compliance checks (`compliance-check`)
  - SARIF output for GitHub Security tab
  - GitLab Code Quality report format
  - Incremental scanning (changed files only)
  - Configurable severity thresholds
  - New API endpoints: `/api/v1/cicd/scan`, `/scan/sarif`, `/scan/gitlab`

- **Regulatory Prediction Engine**
  - ML-powered regulatory change predictions
  - 15+ regulatory source monitors (EUR-Lex, Congress.gov, FTC, etc.)
  - 6-12 month advance warnings
  - Impact assessment for codebases
  - New API endpoints: `/api/v1/predictions/analyze`, `/predictions`, `/impact-assessment`

- **Compliance-as-Code Templates**
  - Pre-built code templates for common compliance patterns
  - GDPR consent banner, HIPAA PHI handler, DSAR handler
  - Audit logging, PCI card tokenization templates
  - Multi-language support (Python, TypeScript, Java, Go)
  - New API endpoint: `/api/v1/features/templates`

- **Multi-Cloud Compliance Posture**
  - Infrastructure-as-Code analysis (Terraform, CloudFormation, Kubernetes)
  - 15+ cloud compliance rules
  - Data residency, encryption, access control checks
  - New API endpoint: `/api/v1/features/cloud/scan`

- **Compliance Knowledge Graph**
  - Interactive visualization of compliance relationships
  - Natural language queries
  - Regulation coverage statistics
  - Impact analysis
  - New API endpoints: `/api/v1/features/graph/*`

- **Vendor/Third-Party Risk Module**
  - Vendor compliance assessment
  - Dependency vulnerability scanning (npm, pip, maven)
  - License compliance checking
  - Risk scoring and recommendations
  - New API endpoints: `/api/v1/features/vendor/*`

- **Compliance Simulation Sandbox**
  - What-if analysis for code changes
  - Architecture change impact simulation
  - Vendor change compliance assessment
  - Regulation adoption planning
  - New API endpoints: `/api/v1/features/sandbox/*`

- **Automated Evidence Collection**
  - Multi-framework support (SOC 2, ISO 27001, HIPAA, PCI-DSS, NIST)
  - Code-to-control mapping
  - Audit report generation
  - Coverage tracking
  - New API endpoints: `/api/v1/features/evidence/*`

- **Regulatory Chatbot**
  - Conversational compliance assistant
  - Codebase-aware answers
  - Source citations from regulations
  - Quick answers without session
  - New API endpoints: `/api/v1/features/chat/*`

### Added
- Initial project implementation
- Multi-tenant architecture with organization support
- JWT authentication with refresh tokens
- SAML/SSO enterprise authentication
- Regulatory monitoring system
  - Web crawler infrastructure with Playwright
  - Support for EUR-Lex, EDPB, national DPAs
  - Change detection with content hashing
- AI-powered legal parsing with GitHub Copilot SDK
  - Obligation extraction (MUST/SHOULD/MAY)
  - Entity and citation extraction
  - Confidence scoring
- Codebase integration
  - GitHub repository analysis
  - File pattern detection
  - Compliance gap identification
- Code generation system
  - Context-aware suggestions
  - PR creation with audit context
- Regulatory frameworks
  - GDPR (EU General Data Protection Regulation)
  - CCPA (California Consumer Privacy Act)
  - HIPAA (Health Insurance Portability and Accountability Act)
  - EU AI Act
- Multi-jurisdiction conflict resolution
- Dashboard UI with Next.js 14
  - Compliance status overview
  - Regulation browser
  - Repository management
  - Action tracking
  - Audit trail viewer
  - Settings management
- Audit trail system with hash chain verification
- Stripe billing integration
- Docker Compose for local development
- Terraform AWS infrastructure
- GitHub Actions CI/CD

### Added (v0.2.0 - Market Expansion)
- **Asia-Pacific Regulatory Module**
  - Singapore PDPA (Personal Data Protection Act)
  - India DPDP (Digital Personal Data Protection Act 2023)
  - Japan APPI (Act on Protection of Personal Information)
  - South Korea PIPA (Personal Information Protection Act)
  - China PIPL (Personal Information Protection Law)
  - 16+ new regulatory sources for APAC region
  - APAC jurisdiction strictness rankings for conflict resolution
- **ESG & Sustainability Compliance**
  - EU CSRD (Corporate Sustainability Reporting Directive)
  - SEC Climate Disclosure Rules
  - TCFD (Task Force on Climate-related Financial Disclosures)
  - GRI Standards integration
  - GHG emissions (Scope 1/2/3) requirement extraction
  - 8 new ESG regulatory sources
- **AI Safety Standards Suite**
  - NIST AI Risk Management Framework (full Govern/Map/Measure/Manage)
  - ISO 42001 AI Management System
  - AI Risk Classifier with EU AI Act risk levels
  - 50+ AI system detection patterns
  - High-risk AI use case identification
  - Prohibited AI practice detection
  - 6 new AI safety regulatory sources
- **Unified Source Registry**
  - Centralized source initialization
  - Framework categorization (Privacy, Security, AI, ESG)
  - Source statistics and reporting
- **New Requirement Categories**
  - AI risk classification
  - Sustainability reporting
  - GHG emissions
  - Climate risk
  - Environmental/Social impact
  - Governance disclosure
  - Accessibility (WCAG)

### Infrastructure
- PostgreSQL for primary data storage
- Redis for caching and Celery broker
- Elasticsearch for document search
- MinIO for S3-compatible object storage
- Celery workers for background processing

## [0.1.0] - 2024-XX-XX

### Added
- Initial release

---

[Unreleased]: https://github.com/josedab/complianceagent/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/josedab/complianceagent/releases/tag/v0.1.0
