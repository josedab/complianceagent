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
router.include_router(chatbot.router, prefix="/chatbot", tags=["Compliance Chatbot (Legacy)"])
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
