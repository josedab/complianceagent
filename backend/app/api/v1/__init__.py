"""API v1 router.

Route modules are organized by domain. See DOMAINS.md for the full map.
"""

from fastapi import APIRouter

# ---------------------------------------------------------------------------
# 🔐 Auth & Identity
# ---------------------------------------------------------------------------
from app.api.v1 import (
    auth,
    sso,
    users,
    organizations,
    org_hierarchy,
)

# ---------------------------------------------------------------------------
# 📋 Compliance Core
# ---------------------------------------------------------------------------
from app.api.v1 import (
    regulations,
    requirements,
    compliance,
    mappings,
    data_flow,
    policy_as_code,
    policy_sdk,
    templates,
    starter_kits,
    industry_packs,
)

# ---------------------------------------------------------------------------
# 🤖 AI & Intelligence
# ---------------------------------------------------------------------------
from app.api.v1 import (
    chat,
    chatbot,
    copilot_chat,
    nl_query,
    intelligence,
    predictions,
    multi_llm,
    ai_safety,
    explainability,
    model_cards,
    testing,
    architecture_advisor,
)

# ---------------------------------------------------------------------------
# 🔍 Analysis & Monitoring
# ---------------------------------------------------------------------------
from app.api.v1 import (
    health_score,
    scoring,
    posture_scoring,
    health_benchmarking,
    drift_detection,
    digital_twin,
    digital_twin_enhanced,
    impact_simulator,
    impact_timeline,
    impact_heatmap,
    risk_quantification,
    cost_calculator,
    simulator,
    alerts,
    news_ticker,
    telemetry,
    compliance_intel,
)

# ---------------------------------------------------------------------------
# 🛠️ Developer Tools
# ---------------------------------------------------------------------------
from app.api.v1 import (
    ide,
    ide_agent,
    cicd,
    pr_bot,
    pr_review,
    pr_copilot,
    repositories,
    iac_scanner,
    sbom,
)

# ---------------------------------------------------------------------------
# 📊 Audit & Evidence
# ---------------------------------------------------------------------------
from app.api.v1 import (
    audit,
    audit_autopilot,
    audit_reports,
    evidence,
    evidence_collector,
    evidence_vault,
)

# ---------------------------------------------------------------------------
# 📈 Marketplace & Ecosystem
# ---------------------------------------------------------------------------
from app.api.v1 import (
    marketplace,
    marketplace_app,
    pattern_marketplace,
    policy_marketplace,
)

# ---------------------------------------------------------------------------
# 🔧 Automation & Workflows
# ---------------------------------------------------------------------------
from app.api.v1 import (
    autopilot,
    orchestration,
    playbook,
    remediation_workflow,
    sandbox,
    regulatory_sandbox,
    compliance_sandbox,
)

# ---------------------------------------------------------------------------
# 🏢 Platform & Enterprise
# ---------------------------------------------------------------------------
from app.api.v1 import (
    billing,
    customer_profiles,
    saas_platform,
    self_hosted,
    public_api,
    webhooks,
)

# ---------------------------------------------------------------------------
# 📚 Knowledge & Learning
# ---------------------------------------------------------------------------
from app.api.v1 import (
    graph,
    knowledge_graph,
    query,
    training,
    certification,
    benchmarking,
)

# ---------------------------------------------------------------------------
# 🏗️ Infrastructure & Cloud
# ---------------------------------------------------------------------------
from app.api.v1 import (
    cloud,
    infrastructure,
)

# ---------------------------------------------------------------------------
# 🤝 Vendor & Supply Chain
# ---------------------------------------------------------------------------
from app.api.v1 import (
    vendor_risk,
    vendor_assessment,
    portfolio,
    federated_intel,
)

# ===========================================================================
# Router assembly
# ===========================================================================

router = APIRouter()

# -- 🔐 Auth & Identity ----------------------------------------------------
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(sso.router, prefix="/sso", tags=["SSO/SAML"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
router.include_router(org_hierarchy.router, prefix="/org-hierarchy", tags=["Organization Hierarchy"])

# -- 📋 Compliance Core ----------------------------------------------------
router.include_router(regulations.router, prefix="/regulations", tags=["Regulations"])
router.include_router(requirements.router, prefix="/requirements", tags=["Requirements"])
router.include_router(compliance.router, prefix="/compliance", tags=["Compliance"])
router.include_router(mappings.router, prefix="/mappings", tags=["Codebase Mappings"])
router.include_router(data_flow.router, prefix="/data-flow", tags=["Cross-Border Data Flow"])
router.include_router(policy_as_code.router, prefix="/policy-as-code", tags=["Policy-as-Code (Rego/OPA)"])
router.include_router(policy_sdk.router, prefix="/policy-sdk", tags=["Compliance-as-Code Policy SDK"])
router.include_router(templates.router, prefix="/templates", tags=["Compliance Templates"])
router.include_router(starter_kits.router, prefix="/starter-kits", tags=["Regulation Starter Kits"])
router.include_router(industry_packs.router, prefix="/industry-packs", tags=["Industry Starter Packs"])

# -- 🤖 AI & Intelligence --------------------------------------------------
router.include_router(chat.router, prefix="/chat", tags=["Compliance Copilot Chat"])
router.include_router(chatbot.router, prefix="/chatbot", tags=["Compliance Chatbot (Legacy — use /chat)"])
router.include_router(copilot_chat.router, prefix="/copilot-chat", tags=["Compliance Copilot Chat (Non-Technical)"])
router.include_router(nl_query.router, prefix="/nl-query", tags=["Natural Language Query Engine"])
router.include_router(intelligence.router, prefix="/intelligence", tags=["Regulatory Intelligence"])
router.include_router(predictions.router, prefix="/predictions", tags=["Regulatory Predictions"])
router.include_router(multi_llm.router, prefix="/multi-llm", tags=["Multi-LLM Parsing Engine"])
router.include_router(ai_safety.router, prefix="/ai-safety", tags=["AI Safety"])
router.include_router(explainability.router, prefix="/explainability", tags=["AI Explainability (XAI)"])
router.include_router(model_cards.router, prefix="/model-cards", tags=["AI Model Cards (EU AI Act)"])
router.include_router(testing.router, prefix="/testing", tags=["AI Compliance Testing Suite"])
router.include_router(architecture_advisor.router, prefix="/architecture-advisor", tags=["Regulation-to-Architecture Advisor"])

# -- 🔍 Analysis & Monitoring ----------------------------------------------
router.include_router(health_score.router, prefix="/health-score", tags=["Health Score"])
router.include_router(scoring.router, prefix="/scoring", tags=["Compliance Scoring"])
router.include_router(posture_scoring.router, prefix="/posture", tags=["Compliance Posture Scoring"])
router.include_router(health_benchmarking.router, prefix="/health-benchmarking", tags=["Compliance Health Score Benchmarking"])
router.include_router(drift_detection.router, prefix="/drift-detection", tags=["Compliance Drift Detection"])
router.include_router(digital_twin.router, prefix="/digital-twin", tags=["Compliance Digital Twin"])
router.include_router(digital_twin_enhanced.router, prefix="/digital-twin-enhanced", tags=["Enhanced Digital Twin"])
router.include_router(impact_simulator.router, prefix="/impact-simulator", tags=["Regulatory Impact Simulator"])
router.include_router(impact_timeline.router, prefix="/impact-timeline", tags=["Regulatory Impact Timeline"])
router.include_router(impact_heatmap.router, prefix="/impact-heatmap", tags=["Regulatory Impact Heat Maps"])
router.include_router(risk_quantification.router, prefix="/risk-quantification", tags=["Compliance Risk Quantification (CRQ)"])
router.include_router(cost_calculator.router, prefix="/cost-calculator", tags=["Predictive Compliance Cost Calculator"])
router.include_router(simulator.router, prefix="/simulator", tags=["Scenario Simulator"])
router.include_router(alerts.router, prefix="/alerts", tags=["Regulatory Alerts"])
router.include_router(news_ticker.router, prefix="/news-ticker", tags=["Regulatory News Ticker"])
router.include_router(telemetry.router, prefix="/telemetry", tags=["Real-Time Compliance Telemetry"])
router.include_router(compliance_intel.router, prefix="/compliance-intel", tags=["Federated Compliance Intelligence"])

# -- 🛠️ Developer Tools ----------------------------------------------------
router.include_router(ide.router, prefix="/ide", tags=["IDE Integration"])
router.include_router(ide_agent.router, prefix="/ide-agent", tags=["Compliance Co-Pilot IDE Agent"])
router.include_router(cicd.router, prefix="/cicd", tags=["CI/CD Integration"])
router.include_router(pr_bot.router, tags=["PR Bot"])
router.include_router(pr_review.router, prefix="/pr-review", tags=["PR Review Co-Pilot"])
router.include_router(pr_copilot.router, prefix="/pr-copilot", tags=["Compliance PR Co-Pilot"])
router.include_router(repositories.router, prefix="/repositories", tags=["Repositories"])
router.include_router(iac_scanner.router, prefix="/iac-scanner", tags=["Infrastructure-as-Code Compliance Scanner"])
router.include_router(sbom.router, prefix="/sbom", tags=["SBOM Compliance"])

# -- 📊 Audit & Evidence ---------------------------------------------------
router.include_router(audit.router, prefix="/audit", tags=["Audit Trail"])
router.include_router(audit_autopilot.router, prefix="/audit-autopilot", tags=["Audit Preparation Autopilot"])
router.include_router(audit_reports.router, prefix="/audit-reports", tags=["Automatic Audit Report Generation"])
router.include_router(evidence.router, prefix="/evidence", tags=["Evidence Generator"])
router.include_router(evidence_collector.router, prefix="/evidence-collector", tags=["Evidence Collection"])
router.include_router(evidence_vault.router, prefix="/evidence-vault", tags=["Evidence Vault & Auditor Portal"])

# -- 📈 Marketplace & Ecosystem --------------------------------------------
router.include_router(marketplace.router, prefix="/marketplace", tags=["API Marketplace"])
router.include_router(marketplace_app.router, prefix="/marketplace-app", tags=["GitHub/GitLab Marketplace App"])
router.include_router(pattern_marketplace.router, prefix="/pattern-marketplace", tags=["Pattern Marketplace"])
router.include_router(policy_marketplace.router, prefix="/policy-marketplace", tags=["Compliance-as-Code Policy Marketplace"])

# -- 🔧 Automation & Workflows ---------------------------------------------
router.include_router(autopilot.router, prefix="/autopilot", tags=["Agentic Autopilot"])
router.include_router(orchestration.router, prefix="/orchestration", tags=["Compliance Orchestration"])
router.include_router(playbook.router, prefix="/playbook", tags=["Compliance Playbook"])
router.include_router(remediation_workflow.router, prefix="/remediation", tags=["Compliance Remediation Workflows"])
router.include_router(sandbox.router, prefix="/sandbox", tags=["Compliance Sandbox"])
router.include_router(regulatory_sandbox.router, prefix="/regulatory-sandbox", tags=["Regulatory Sandbox Integration"])
router.include_router(compliance_sandbox.router, prefix="/compliance-sandbox", tags=["Compliance Sandbox Environments"])

# -- 🏢 Platform & Enterprise ----------------------------------------------
router.include_router(billing.router, prefix="/billing", tags=["Billing"])
router.include_router(customer_profiles.router, prefix="/customer-profiles", tags=["Customer Profiles"])
router.include_router(saas_platform.router, prefix="/saas-platform", tags=["SaaS Platform"])
router.include_router(self_hosted.router, prefix="/self-hosted", tags=["Self-Hosted Deployment"])
router.include_router(public_api.router, prefix="/public-api", tags=["Public API & SDK"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])

# -- 📚 Knowledge & Learning -----------------------------------------------
router.include_router(graph.router, prefix="/graph", tags=["Knowledge Graph"])
router.include_router(knowledge_graph.router, prefix="/knowledge-graph", tags=["Knowledge Graph Explorer"])
router.include_router(query.router, prefix="/query", tags=["Query Engine"])
router.include_router(training.router, prefix="/training", tags=["Compliance Training"])
router.include_router(certification.router, prefix="/certification", tags=["Compliance Training & Certification"])
router.include_router(benchmarking.router, prefix="/benchmarking", tags=["Accuracy Benchmarking"])

# -- 🏗️ Infrastructure & Cloud ---------------------------------------------
router.include_router(cloud.router, prefix="/cloud", tags=["Cloud Compliance"])
router.include_router(infrastructure.router, tags=["Infrastructure Compliance"])

# -- 🤝 Vendor & Supply Chain ----------------------------------------------
router.include_router(vendor_risk.router, prefix="/vendor-risk", tags=["Vendor Risk"])
router.include_router(vendor_assessment.router, prefix="/vendor-assessment", tags=["Vendor Assessment"])
router.include_router(portfolio.router, prefix="/portfolios", tags=["Compliance Portfolios"])
router.include_router(federated_intel.router, prefix="/federated-intel", tags=["Federated Intelligence Network"])
