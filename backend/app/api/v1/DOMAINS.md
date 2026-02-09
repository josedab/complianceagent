# API v1 Route Domains

Quick reference for finding API route files by feature domain.

## Domain Map

### 🔐 Auth & Identity
| File | Prefix | Description |
|------|--------|-------------|
| `auth.py` | `/auth` | Login, registration, password reset |
| `sso.py` | `/sso` | SSO/SAML integration |
| `users.py` | `/users` | User profile management |
| `organizations.py` | `/organizations` | Organization CRUD |
| `org_hierarchy.py` | `/org-hierarchy` | Multi-level org hierarchy |

### 📋 Compliance Core
| File | Prefix | Description |
|------|--------|-------------|
| `regulations.py` | `/regulations` | Regulation management |
| `requirements.py` | `/requirements` | Compliance requirements |
| `compliance.py` | `/compliance` | Compliance assessments |
| `mappings.py` | `/mappings` | Code-to-regulation mapping |
| `data_flow.py` | `/data-flow` | Cross-border data flow |
| `policy_as_code.py` | `/policy-as-code` | Rego/OPA policies |
| `policy_sdk.py` | `/policy-sdk` | Policy SDK |
| `templates.py` | `/templates` | Compliance templates |
| `starter_kits.py` | `/starter-kits` | Regulation starter kits |
| `industry_packs.py` | `/industry-packs` | Industry-specific packs |

### 🤖 AI & Intelligence
| File | Prefix | Description |
|------|--------|-------------|
| `chat.py` | `/chat` | AI compliance chat (streaming + RAG) |
| `chatbot.py` | `/chatbot` | Legacy chatbot (use /chat) |
| `copilot_chat.py` | `/copilot-chat` | Non-technical copilot chat |
| `nl_query.py` | `/nl-query` | Natural language queries |
| `intelligence.py` | `/intelligence` | Regulatory intelligence |
| `predictions.py` | `/predictions` | Regulatory predictions |
| `multi_llm.py` | `/multi-llm` | Multi-LLM parsing engine |
| `ai_safety.py` | `/ai-safety` | AI safety controls |
| `explainability.py` | `/explainability` | AI explainability (XAI) |
| `model_cards.py` | `/model-cards` | EU AI Act model cards |

### 🔍 Analysis & Monitoring
| File | Prefix | Description |
|------|--------|-------------|
| `health_score.py` | `/health-score` | Health score |
| `scoring.py` | `/scoring` | Compliance scoring |
| `posture_scoring.py` | `/posture` | Posture scoring |
| `health_benchmarking.py` | `/health-benchmarking` | Benchmarking dashboard |
| `drift_detection.py` | `/drift-detection` | Compliance drift detection |
| `digital_twin.py` | `/digital-twin` | Compliance digital twin |
| `digital_twin_enhanced.py` | `/digital-twin-enhanced` | Enhanced digital twin |
| `impact_simulator.py` | `/impact-simulator` | Impact simulation |
| `impact_timeline.py` | `/impact-timeline` | Impact timeline |
| `impact_heatmap.py` | `/impact-heatmap` | Regulatory impact heat maps |
| `risk_quantification.py` | `/risk-quantification` | Risk quantification (CRQ) |
| `cost_calculator.py` | `/cost-calculator` | Predictive cost calculator |
| `simulator.py` | `/simulator` | Scenario simulator |
| `alerts.py` | `/alerts` | Regulatory alerts |
| `news_ticker.py` | `/news-ticker` | Regulatory news ticker |
| `telemetry.py` | `/telemetry` | Real-time telemetry |
| `compliance_intel.py` | `/compliance-intel` | Federated intelligence |

### 🛠️ Developer Tools
| File | Prefix | Description |
|------|--------|-------------|
| `ide.py` | `/ide` | IDE linting integration |
| `ide_agent.py` | `/ide-agent` | IDE compliance co-pilot agent |
| `cicd.py` | `/cicd` | CI/CD compliance gates |
| `pr_bot.py` | `/pr-bot` | PR compliance bot |
| `pr_review.py` | `/pr-review` | PR review co-pilot |
| `pr_copilot.py` | `/pr-copilot` | PR compliance co-pilot |
| `repositories.py` | `/repositories` | Repository management |
| `iac_scanner.py` | `/iac-scanner` | IaC compliance scanner |
| `sbom.py` | `/sbom` | SBOM compliance |

### 📊 Audit & Evidence
| File | Prefix | Description |
|------|--------|-------------|
| `audit.py` | `/audit` | Audit trail |
| `audit_autopilot.py` | `/audit-autopilot` | Audit preparation autopilot |
| `audit_reports.py` | `/audit-reports` | Automatic audit reports |
| `evidence.py` | `/evidence` | Evidence generator |
| `evidence_collector.py` | `/evidence-collector` | Evidence collection |
| `evidence_vault.py` | `/evidence-vault` | Evidence vault & auditor portal |

### 📈 Marketplace & Ecosystem
| File | Prefix | Description |
|------|--------|-------------|
| `marketplace.py` | `/marketplace` | API marketplace |
| `marketplace_app.py` | `/marketplace-app` | GitHub/GitLab marketplace app |
| `pattern_marketplace.py` | `/pattern-marketplace` | Pattern marketplace |
| `policy_marketplace.py` | `/policy-marketplace` | Policy pack marketplace |

### 🔧 Automation & Workflows
| File | Prefix | Description |
|------|--------|-------------|
| `autopilot.py` | `/autopilot` | Agentic autopilot |
| `orchestration.py` | `/orchestration` | Compliance orchestration |
| `playbook.py` | `/playbook` | Compliance playbooks |
| `remediation_workflow.py` | `/remediation` | Remediation workflows |
| `sandbox.py` | `/sandbox` | Compliance sandbox |
| `regulatory_sandbox.py` | `/regulatory-sandbox` | Regulatory sandbox integration |
| `compliance_sandbox.py` | `/compliance-sandbox` | Training sandbox environments |

### 🏢 Platform & Enterprise
| File | Prefix | Description |
|------|--------|-------------|
| `billing.py` | `/billing` | Billing and subscriptions |
| `customer_profiles.py` | `/customer-profiles` | Customer profiles |
| `saas_platform.py` | `/saas-platform` | SaaS platform management |
| `self_hosted.py` | `/self-hosted` | Self-hosted deployment |
| `public_api.py` | `/public-api` | Public API & SDK |
| `webhooks.py` | `/webhooks` | Webhook management |

### 📚 Knowledge & Learning
| File | Prefix | Description |
|------|--------|-------------|
| `graph.py` | `/graph` | Knowledge graph |
| `knowledge_graph.py` | `/knowledge-graph` | Knowledge graph explorer |
| `query.py` | `/query` | Query engine |
| `training.py` | `/training` | Compliance training |
| `certification.py` | `/certification` | Training & certification |
| `benchmarking.py` | `/benchmarking` | Accuracy benchmarking |

### 🏗️ Infrastructure & Cloud
| File | Prefix | Description |
|------|--------|-------------|
| `cloud.py` | `/cloud` | Cloud compliance |
| `infrastructure.py` | `/infrastructure` | Infrastructure compliance |

### 🤝 Vendor & Supply Chain
| File | Prefix | Description |
|------|--------|-------------|
| `vendor_risk.py` | `/vendor-risk` | Vendor risk assessment |
| `vendor_assessment.py` | `/vendor-assessment` | Vendor assessment |
| `portfolio.py` | `/portfolios` | Compliance portfolios |
| `federated_intel.py` | `/federated-intel` | Federated intelligence network |

---

## Shared Files

| File | Purpose |
|------|---------|
| `__init__.py` | Router assembly — registers all routers |
| `deps.py` | Shared dependencies (auth, DB, services) |

## Adding a New Route

1. Create `backend/app/api/v1/your_feature.py`
2. Define `router = APIRouter()`
3. Add import + `router.include_router(...)` in `__init__.py`
4. Add entry to this file under the appropriate domain
