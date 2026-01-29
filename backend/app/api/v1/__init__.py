"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import (
    ai_safety,
    audit,
    auth,
    billing,
    chatbot,
    cicd,
    cloud,
    compliance,
    customer_profiles,
    digital_twin,
    evidence,
    graph,
    health_score,
    ide,
    intelligence,
    mappings,
    marketplace,
    orchestration,
    organizations,
    playbook,
    predictions,
    pr_review,
    query,
    regulations,
    repositories,
    requirements,
    sandbox,
    sso,
    templates,
    users,
    vendor_risk,
    webhooks,
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
router.include_router(chatbot.router, prefix="/chat", tags=["Compliance Chatbot"])

# Next-Gen Feature Routers
router.include_router(pr_review.router, prefix="/pr-review", tags=["PR Review Co-Pilot"])
router.include_router(intelligence.router, prefix="/intelligence", tags=["Regulatory Intelligence"])
router.include_router(digital_twin.router, prefix="/digital-twin", tags=["Compliance Digital Twin"])
router.include_router(evidence.router, prefix="/evidence", tags=["Evidence Generator"])
router.include_router(marketplace.router, prefix="/marketplace", tags=["API Marketplace"])
router.include_router(query.router, prefix="/query", tags=["Query Engine"])
router.include_router(vendor_risk.router, prefix="/vendor-risk", tags=["Vendor Risk"])
router.include_router(playbook.router, prefix="/playbook", tags=["Compliance Playbook"])
router.include_router(orchestration.router, prefix="/orchestration", tags=["Compliance Orchestration"])
router.include_router(health_score.router, prefix="/health-score", tags=["Health Score"])
