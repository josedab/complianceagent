# Backend Services Directory

This directory contains all business logic services for ComplianceAgent.
Services are organized by domain and maturity level.

## Service Taxonomy

### 🟢 Core Services (Stable)

These services implement the core compliance pipeline and are well-tested.

| Service | Description |
|---------|-------------|
| `monitoring/` | Regulatory source crawling and change detection (19 files) |
| `parsing/` | Legal text parsing and requirement extraction via Copilot SDK |
| `mapping/` | Codebase-to-requirement mapping and gap detection |
| `generation/` | AI-powered compliant code generation |
| `github/` | GitHub API integration (repos, PRs, webhooks) |
| `gitlab/` | GitLab API integration |
| `audit/` | Immutable audit trail with hash chain verification |
| `billing/` | Stripe subscription and payment management |
| `enterprise/` | SSO/SAML authentication for enterprise customers |
| `notification/` | Multi-channel alerting (email, Slack, webhook) |

### 🟡 Feature Services (Functional)

These implement specific product features. Most have API routes but limited test coverage.

| Service | Description |
|---------|-------------|
| `chat/` | Compliance Copilot Chat with RAG and streaming |
| `pr_bot/` | Automated PR compliance analysis with GitHub Checks |
| `pr_review/` | PR review co-pilot with inline comments |
| `ide/` | IDE integration endpoints (analyze, quickfix, suppressions) |
| `cicd/` | CI/CD compliance gates with SARIF output |
| `templates/` | Pre-built compliance-as-code templates (GDPR, HIPAA, PCI) |
| `cloud/` | Multi-cloud IaC analysis (Terraform, CloudFormation, K8s) |
| `prediction/` | Regulatory change prediction engine |
| `evidence/` | Compliance evidence generation and control mapping |
| `sandbox/` | What-if compliance simulation sandbox |
| `graph/` | Compliance relationship graph |
| `scoring/` | Compliance scoring engine |
| `infrastructure/` | Infrastructure compliance scanning |

### 🟠 Extended Features (Experimental)

These implement advanced/next-gen features. Coverage is minimal or absent.
Expect APIs to change.

| Service | Description | Notes |
|---------|-------------|-------|
| `autopilot/` | Agentic compliance autopilot | |
| `benchmarking/` | Regulatory parsing accuracy benchmarking | |
| `compliance_intel/` | Federated compliance intelligence network | |
| `data_flow/` | Cross-border data flow analysis | |
| `debt/` | Compliance debt tracking | |
| `diff_alerts/` | Compliance diff alerting | |
| `digital_twin/` | Compliance digital twin | |
| `drift_detection/` | Compliance posture drift detection | |
| `explainability/` | AI decision explainability (XAI) | |
| `federated_intel/` | Federated intelligence network | Overlaps `compliance_intel/` |
| `health_score/` | Compliance health scoring | Overlaps `scoring/` |
| `ide_agent/` | IDE agent with autonomous actions | Extends `ide/` |
| `impact_simulator/` | Regulatory change impact simulator | |
| `impact_timeline/` | Regulatory change timeline | |
| `industry_packs/` | Industry-specific compliance starter packs | |
| `intelligence/` | Regulatory intelligence analysis | |
| `knowledge_graph/` | Knowledge graph explorer | Extends `graph/` |
| `legal/` | Legal document processing | |
| `marketplace/` | API marketplace | |
| `marketplace_app/` | GitHub/GitLab Marketplace native app | Extends `marketplace/` |
| `model_cards/` | AI Model Cards (EU AI Act) | |
| `multi_llm/` | Multi-LLM regulatory parsing engine | |
| `nl_query/` | Natural language compliance query engine | |
| `orchestration/` | Compliance workflow orchestration | |
| `org_hierarchy/` | Multi-tenant organization hierarchy | |
| `pattern_marketplace/` | Compliance pattern marketplace | |
| `playbook/` | Compliance playbook engine | |
| `policy/` | Policy management | |
| `policy_as_code/` | Policy-as-Code (Rego/OPA) | Extends `policy/` |
| `policy_sdk/` | Compliance-as-Code SDK | Extends `policy/` |
| `portfolio/` | Compliance portfolio management | |
| `posture_scoring/` | Posture scoring and benchmarking | Overlaps `scoring/` |
| `pr_copilot/` | Compliance PR co-pilot | Extends `pr_review/` |
| `public_api/` | Public API key management and rate limiting | |
| `radar/` | Regulatory radar visualization | |
| `remediation_workflow/` | Automated remediation state machine | |
| `risk_quantification/` | Compliance risk quantification (CRQ) | |
| `saas_platform/` | SaaS platform multi-tenancy | |
| `sbom/` | SBOM compliance analysis | |
| `self_hosted/` | Self-hosted/air-gapped deployment support | |
| `starter_kits/` | Regulation starter kits | Overlaps `industry_packs/` |
| `telemetry/` | Real-time compliance telemetry | |
| `testing/` | Compliance testing utilities | |
| `training/` | Compliance training module | |

### Known Overlaps (Consolidation Status)

The following groups have overlapping responsibilities. Canonical modules are
marked with ✅; deprecated/legacy modules are marked with ⚠️.

| Group | Canonical | Legacy/Deprecated | Status |
|-------|-----------|-------------------|--------|
| **Chat** | `chat/` ✅ | `chatbot/` ⚠️ | `chatbot/` has deprecation notice; `/chatbot` API tagged as Legacy |
| **Vendor** | `vendor_risk/`, `vendor_assessment/` ✅ | `vendor/` ⚠️ | `vendor/` has deprecation notice |
| **Evidence** | `evidence/` ✅ | `evidence_collector/`, `evidence_vault/` | Separate scopes (collector=gathering, vault=storage) |
| **Policy** | `policy_as_code/`, `policy_sdk/` ✅ | `policy/` ⚠️ | `policy/` is empty stub with pointer |
| **Prediction** | `predictions/` ✅ (ML trends) | `prediction/` (signal-based) | Complementary; both active with cross-reference docs |
| **IDE** | `ide/` ✅ | `ide_agent/` | Separate scopes (ide=endpoints, ide_agent=autonomous agent) |
| **Scoring** | `scoring/` ✅ | `health_score/`, `posture_scoring/` | Separate scopes |
| **Graph** | `knowledge_graph/` ✅ | `graph/` ⚠️ | `graph/` has deprecation notice |
| **Query** | `query_engine/` ✅ | `query/` ⚠️ | `query/` is empty stub with pointer |
| **Marketplace** | `marketplace/` ✅ | `marketplace_app/`, `pattern_marketplace/` | Separate scopes (app=GitHub integration, pattern=community) |
| **Intelligence** | `intelligence/` ✅ | `federated_intel/`, `compliance_intel/` | Separate scopes (federated=cross-org, intel=analysis) |

### Shared Utilities

| File | Description |
|------|-------------|
| `conflict_resolution.py` | Multi-jurisdiction conflict resolution logic |

## Adding a New Service

1. Create a directory under `services/` with an `__init__.py`
2. Add a `service.py` with the core business logic
3. Create corresponding route(s) in `api/v1/`
4. Add tests in `tests/services/`
5. Register the router in `api/v1/__init__.py`
