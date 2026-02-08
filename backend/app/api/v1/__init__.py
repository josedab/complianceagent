"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import (
    ai_safety,
    alerts,
    audit,
    auth,
    autopilot,
    billing,
    chat,
    chatbot,
    cicd,
    cloud,
    compliance,
    customer_profiles,
    data_flow,
    digital_twin,
    evidence,
    evidence_collector,
    explainability,
    graph,
    health_score,
    ide,
    infrastructure,
    intelligence,
    knowledge_graph,
    mappings,
    marketplace,
    model_cards,
    orchestration,
    organizations,
    playbook,
    policy_as_code,
    portfolio,
    pr_bot,
    predictions,
    pr_review,
    query,
    regulations,
    repositories,
    requirements,
    sandbox,
    sbom,
    scoring,
    simulator,
    sso,
    starter_kits,
    templates,
    training,
    users,
    vendor_assessment,
    vendor_risk,
    webhooks,
)

# Phase 3: Market Leadership Features
from app.api.v1 import (
    federated_intel,
    digital_twin_enhanced,
    regulatory_sandbox,
)

# Phase 4: Next-Gen Features (v1.1.0+)
from app.api.v1 import (
    ide_agent,
    pattern_marketplace,
    risk_quantification,
)

# Phase 5: SaaS Platform (v1.2.0+)
from app.api.v1 import saas_platform

# Phase 6: Next-Gen Strategic Features (v2.0.0)
from app.api.v1 import (
    benchmarking,
    marketplace_app,
    pr_copilot,
    industry_packs,
    drift_detection,
    multi_llm,
    evidence_vault,
    public_api,
    impact_simulator,
)

# Phase 7: Next-Gen Features v3.0.0
from app.api.v1 import (
    telemetry,
    nl_query,
    remediation_workflow,
    posture_scoring,
    org_hierarchy,
    policy_sdk,
    audit_autopilot,
    impact_timeline,
    compliance_intel,
    self_hosted,
)


router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(regulations.router, prefix="/regulations", tags=["Regulations"])
router.include_router(requirements.router, prefix="/requirements", tags=["Requirements"])
router.include_router(
    customer_profiles.router, prefix="/customer-profiles", tags=["Customer Profiles"]
)
router.include_router(repositories.router, prefix="/repositories", tags=["Repositories"])
router.include_router(mappings.router, prefix="/mappings", tags=["Codebase Mappings"])
router.include_router(compliance.router, prefix="/compliance", tags=["Compliance"])
router.include_router(audit.router, prefix="/audit", tags=["Audit Trail"])
router.include_router(billing.router, prefix="/billing", tags=["Billing"])
router.include_router(sso.router, prefix="/sso", tags=["SSO/SAML"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
router.include_router(ide.router, prefix="/ide", tags=["IDE Integration"])
router.include_router(ai_safety.router, prefix="/ai-safety", tags=["AI Safety"])
router.include_router(cicd.router, prefix="/cicd", tags=["CI/CD Integration"])
router.include_router(predictions.router, prefix="/predictions", tags=["Regulatory Predictions"])

# Refactored Feature Routers (split from features.py)
router.include_router(templates.router, prefix="/templates", tags=["Compliance Templates"])
router.include_router(cloud.router, prefix="/cloud", tags=["Cloud Compliance"])
router.include_router(graph.router, prefix="/graph", tags=["Knowledge Graph"])
router.include_router(sandbox.router, prefix="/sandbox", tags=["Compliance Sandbox"])
router.include_router(chatbot.router, prefix="/chatbot", tags=["Compliance Chatbot (Legacy — use /chat)"])
router.include_router(chat.router, prefix="/chat", tags=["Compliance Copilot Chat"])

# Next-Gen Feature Routers
router.include_router(pr_review.router, prefix="/pr-review", tags=["PR Review Co-Pilot"])
router.include_router(pr_bot.router, tags=["PR Bot"])
router.include_router(intelligence.router, prefix="/intelligence", tags=["Regulatory Intelligence"])
router.include_router(digital_twin.router, prefix="/digital-twin", tags=["Compliance Digital Twin"])
router.include_router(evidence.router, prefix="/evidence", tags=["Evidence Generator"])
router.include_router(marketplace.router, prefix="/marketplace", tags=["API Marketplace"])
router.include_router(query.router, prefix="/query", tags=["Query Engine"])
router.include_router(vendor_risk.router, prefix="/vendor-risk", tags=["Vendor Risk"])
router.include_router(playbook.router, prefix="/playbook", tags=["Compliance Playbook"])
router.include_router(orchestration.router, prefix="/orchestration", tags=["Compliance Orchestration"])
router.include_router(health_score.router, prefix="/health-score", tags=["Health Score"])
router.include_router(scoring.router, prefix="/scoring", tags=["Compliance Scoring"])
router.include_router(alerts.router, prefix="/alerts", tags=["Regulatory Alerts"])
router.include_router(portfolio.router, prefix="/portfolios", tags=["Compliance Portfolios"])
router.include_router(simulator.router, prefix="/simulator", tags=["Scenario Simulator"])
router.include_router(evidence_collector.router, prefix="/evidence-collector", tags=["Evidence Collection"])
router.include_router(vendor_assessment.router, prefix="/vendor-assessment", tags=["Vendor Assessment"])
router.include_router(knowledge_graph.router, prefix="/knowledge-graph", tags=["Knowledge Graph Explorer"])
router.include_router(starter_kits.router, prefix="/starter-kits", tags=["Regulation Starter Kits"])
router.include_router(training.router, prefix="/training", tags=["Compliance Training"])
router.include_router(infrastructure.router, tags=["Infrastructure Compliance"])

# Killer Features (v0.4.0+)
router.include_router(explainability.router, prefix="/explainability", tags=["AI Explainability (XAI)"])
router.include_router(sbom.router, prefix="/sbom", tags=["SBOM Compliance"])
router.include_router(policy_as_code.router, prefix="/policy-as-code", tags=["Policy-as-Code (Rego/OPA)"])
router.include_router(data_flow.router, prefix="/data-flow", tags=["Cross-Border Data Flow"])
router.include_router(model_cards.router, prefix="/model-cards", tags=["AI Model Cards (EU AI Act)"])
router.include_router(autopilot.router, prefix="/autopilot", tags=["Agentic Autopilot"])

# Phase 3: Market Leadership Features (v1.0.0)
router.include_router(federated_intel.router, prefix="/federated-intel", tags=["Federated Intelligence Network"])
router.include_router(digital_twin_enhanced.router, prefix="/digital-twin-enhanced", tags=["Enhanced Digital Twin"])
router.include_router(regulatory_sandbox.router, prefix="/regulatory-sandbox", tags=["Regulatory Sandbox Integration"])

# Phase 4: Next-Gen Features (v1.1.0+)
router.include_router(ide_agent.router, prefix="/ide-agent", tags=["Compliance Co-Pilot IDE Agent"])
router.include_router(pattern_marketplace.router, prefix="/pattern-marketplace", tags=["Pattern Marketplace"])
router.include_router(risk_quantification.router, prefix="/risk-quantification", tags=["Compliance Risk Quantification (CRQ)"])

# Phase 5: SaaS Platform
router.include_router(saas_platform.router, prefix="/saas-platform", tags=["SaaS Platform"])

# Phase 6: Next-Gen Strategic Features (v2.0.0)
router.include_router(benchmarking.router, prefix="/benchmarking", tags=["Accuracy Benchmarking"])
router.include_router(marketplace_app.router, prefix="/marketplace-app", tags=["GitHub/GitLab Marketplace App"])
router.include_router(pr_copilot.router, prefix="/pr-copilot", tags=["Compliance PR Co-Pilot"])
router.include_router(industry_packs.router, prefix="/industry-packs", tags=["Industry Starter Packs"])
router.include_router(drift_detection.router, prefix="/drift-detection", tags=["Compliance Drift Detection"])
router.include_router(multi_llm.router, prefix="/multi-llm", tags=["Multi-LLM Parsing Engine"])
router.include_router(evidence_vault.router, prefix="/evidence-vault", tags=["Evidence Vault & Auditor Portal"])
router.include_router(public_api.router, prefix="/public-api", tags=["Public API & SDK"])
router.include_router(impact_simulator.router, prefix="/impact-simulator", tags=["Regulatory Impact Simulator"])

# Phase 7: Next-Gen Features v3.0.0
router.include_router(telemetry.router, prefix="/telemetry", tags=["Real-Time Compliance Telemetry"])
router.include_router(nl_query.router, prefix="/nl-query", tags=["Natural Language Query Engine"])
router.include_router(remediation_workflow.router, prefix="/remediation", tags=["Compliance Remediation Workflows"])
router.include_router(posture_scoring.router, prefix="/posture", tags=["Compliance Posture Scoring"])
router.include_router(org_hierarchy.router, prefix="/org-hierarchy", tags=["Organization Hierarchy"])
router.include_router(policy_sdk.router, prefix="/policy-sdk", tags=["Compliance-as-Code Policy SDK"])
router.include_router(audit_autopilot.router, prefix="/audit-autopilot", tags=["Audit Preparation Autopilot"])
router.include_router(impact_timeline.router, prefix="/impact-timeline", tags=["Regulatory Impact Timeline"])
router.include_router(compliance_intel.router, prefix="/compliance-intel", tags=["Federated Compliance Intelligence"])
router.include_router(self_hosted.router, prefix="/self-hosted", tags=["Self-Hosted Deployment"])
