# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

> **Note:** Features below are under active development and not yet released.
> See the [Roadmap](docs/guides/roadmap.md) for planned timelines.

### Planned (v3.0.0 - Next-Gen Platform Features)

- **Real-Time Compliance Telemetry Dashboard**
  - Live telemetry snapshot with posture gauges, metrics cards, framework scores
  - Metric recording with threshold-based alerting (critical/warning)
  - Time series data with synthetic demo generation
  - Compliance heatmap by framework and day
  - Event feed with severity filtering
  - Frontend dashboard page with React components (posture gauge, event feed, heatmap)
  - New API endpoints: `/api/v1/telemetry/snapshot`, `/metrics`, `/events`, `/time-series/{type}`, `/thresholds`, `/heatmap`

- **Natural Language Compliance Query Engine**
  - Intent classification (regulation, code, violation, audit, status, comparison, recommendation)
  - Built-in knowledge base for GDPR, HIPAA, PCI-DSS, SOC 2
  - Code reference extraction with file/line context
  - Follow-up suggestion generation
  - Query history and feedback tracking
  - New API endpoints: `/api/v1/nl-query/query`, `/history`, `/feedback`, `/intents`

- **Automated Compliance Remediation Workflows**
  - State machine: detected → planning → generating → review → approved → merging → completed
  - Pattern-based fix generation (GDPR, HIPAA, PCI-DSS)
  - Approval chains with rollback capability
  - PR creation simulation and workflow history tracking
  - New API endpoints: `/api/v1/remediation/workflows`, `/generate`, `/approve`, `/merge`, `/rollback`, `/config`

- **Compliance Posture Scoring & Benchmarking**
  - 7-dimension scoring (privacy, security, regulatory, access, incident, vendor, documentation)
  - Letter grades (A+ through F) with weighted aggregation
  - Industry benchmarking with percentile ranking (fintech, healthtech, SaaS, ecommerce)
  - Executive report generation with highlights and action items
  - New API endpoints: `/api/v1/posture/score`, `/benchmark/{industry}`, `/industries`, `/report`, `/history`

- **Multi-Tenant Organization Hierarchy**
  - Parent/child org tree up to 5 levels deep (root → business unit → department → team → project)
  - 6 RBAC roles (owner, admin, compliance_officer, developer, auditor, viewer)
  - Policy inheritance modes (inherit, override, merge)
  - Aggregated compliance scoring across hierarchy
  - New API endpoints: `/api/v1/org-hierarchy/nodes`, `/tree`, `/members`, `/policies`, `/compliance`

- **Compliance-as-Code Policy SDK**
  - 5 built-in policies (GDPR consent, HIPAA PHI encryption, PCI tokenization, SOC 2 logging, EU AI Act transparency)
  - Custom policy creation with YAML/Rego/Python/TypeScript support
  - Policy validation with error/warning reporting
  - Community marketplace for policy sharing
  - SDK packages directory (Python, TypeScript, Go)
  - New API endpoints: `/api/v1/policy-sdk/policies`, `/validate`, `/publish`, `/marketplace`, `/sdks`

- **Audit Preparation Autopilot**
  - Gap analysis for SOC 2 Type II, ISO 27001, HIPAA, PCI-DSS (4 frameworks, 40+ controls)
  - Evidence package auto-generation with control mapping
  - Readiness report with recommendations and prep time estimates
  - New API endpoints: `/api/v1/audit-autopilot/gap-analysis/{fw}`, `/evidence-package/{fw}`, `/readiness-report/{fw}`, `/frameworks`

- **Regulatory Change Impact Timeline**
  - 8 built-in upcoming regulatory events (EU AI Act, DORA, NIS2, GDPR, PCI-DSS, HIPAA, PDPA)
  - Predictive events with confidence scoring
  - Auto-task generation with priority assignment based on deadline proximity
  - Framework and jurisdiction filtering
  - New API endpoints: `/api/v1/impact-timeline/timeline`, `/events`, `/tasks`

- **Federated Compliance Intelligence Network**
  - Differential privacy with Laplace noise (configurable epsilon: 0.1, 1.0, 5.0)
  - 8 seed anonymized compliance patterns across industries
  - 'Companies like you' insights based on industry and size
  - Network participation with contribution tracking
  - New API endpoints: `/api/v1/compliance-intel/join`, `/patterns`, `/insights`, `/similar-orgs`, `/stats`

- **Self-Hosted & Air-Gapped Deployment**
  - License key generation and validation (trial, standard, enterprise, government)
  - 4 offline regulation bundles (core, EU, healthcare, financial)
  - Deployment configuration (SaaS, self-hosted, air-gapped modes)
  - Local LLM support toggle
  - System health monitoring, backup, and Helm chart values
  - New API endpoints: `/api/v1/self-hosted/licenses`, `/config`, `/bundles`, `/health`, `/backup`, `/helm-values`

### Planned (v2.0.0 - Next-Gen Strategic Features)

- **Regulatory Accuracy Benchmarking Suite**
  - Benchmark parsing accuracy against expert-annotated corpus
  - Built-in GDPR corpus with 5+ annotated passages
  - Precision/recall/F1 scoring per framework
  - Public scorecard generation
  - New API endpoints: `/api/v1/benchmarking/corpora`, `/run`, `/results`, `/scorecard`

- **GitHub/GitLab Marketplace Native App**
  - One-click app installation handling
  - Webhook processing for installation, PR, and push events
  - Repository sync and compliance scan triggering
  - Marketplace plan management (Free/Team/Business/Enterprise)
  - New API endpoints: `/api/v1/marketplace-app/webhook`, `/installations`, `/listing`

- **Compliance Co-Pilot for PRs**
  - AI-powered PR compliance analysis with inline findings
  - Pattern-based fallback detection (GDPR, PCI-DSS)
  - Risk level computation and smart labeling
  - Suggestion feedback loop with learning statistics
  - Inline comment generation for GitHub/GitLab
  - New API endpoints: `/api/v1/pr-copilot/analyze`, `/reviews`, `/feedback`, `/learning-stats`

- **Industry Compliance Starter Packs**
  - Pre-configured packs for Fintech, Healthtech, AI Companies, E-commerce
  - Regulation bundles, policy templates, setup checklists
  - One-click pack provisioning with guided onboarding
  - New API endpoints: `/api/v1/industry-packs`, `/provision`, `/verticals`

- **Compliance Drift Detection & Alerting**
  - Baseline capture and comparison engine
  - Score regression detection with severity levels
  - Multi-channel alerting (Slack, Teams, PagerDuty, Email)
  - Drift reporting with top-drifting file analysis
  - New API endpoints: `/api/v1/drift-detection/baseline`, `/detect`, `/events`, `/alerts/config`

- **Multi-LLM Regulatory Parsing Engine**
  - Provider abstraction for Copilot, OpenAI, Anthropic, local models
  - Parallel multi-model inference
  - Consensus strategies: majority vote, highest confidence, weighted average
  - Divergence detection with human review flagging
  - New API endpoints: `/api/v1/multi-llm/parse`, `/providers`, `/config`

- **Evidence Vault & Auditor Portal**
  - Immutable evidence storage with hash chain integrity
  - SOC 2 control mapping (13 controls)
  - Read-only auditor sessions with expiration
  - Audit report generation with coverage metrics
  - New API endpoints: `/api/v1/evidence-vault/evidence`, `/verify`, `/controls`, `/auditor-sessions`, `/reports`

- **Public API & SDK Management**
  - API key creation, validation, and revocation
  - Tiered rate limiting (Free/Standard/Professional/Enterprise)
  - Usage tracking and summary analytics
  - SDK directory (Python, TypeScript, Go)
  - New API endpoints: `/api/v1/public-api/keys`, `/rate-limits`, `/sdks`

- **Regulatory Change Impact Simulator**
  - What-if simulation for hypothetical regulatory changes
  - 5 pre-built scenarios (GDPR, HIPAA, EU AI Act, PCI-DSS)
  - Blast radius analysis with affected component mapping
  - Risk scoring and recommendation generation
  - Multi-scenario comparison
  - New API endpoints: `/api/v1/impact-simulator/simulate`, `/scenarios`, `/results`, `/compare`

### Planned (v0.3.0 - Next-Gen Features)
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

### Planned (v0.2.0 - Market Expansion)
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

## [0.1.0] - 2025-01-15

### Added
- Initial release (see "Added" section above for full feature list)

---

[Unreleased]: https://github.com/josedab/complianceagent/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/josedab/complianceagent/releases/tag/v0.1.0
