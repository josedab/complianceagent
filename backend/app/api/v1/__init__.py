"""API v1 router.

Route modules are organized by domain. See DOMAINS.md for the full map.
"""

from fastapi import APIRouter

# ---------------------------------------------------------------------------
# 🔐 Auth & Identity
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 📋 Compliance Core
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 🤖 AI & Intelligence
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 🔍 Analysis & Monitoring
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 🌐 Next-Gen Features
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 🛠️ Developer Tools
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 📊 Audit & Evidence
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 📈 Marketplace & Ecosystem
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 🔧 Automation & Workflows
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 🏢 Platform & Enterprise
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 📚 Knowledge & Learning
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 🏗️ Infrastructure & Cloud
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 🤝 Vendor & Supply Chain
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 📊 Platform Status
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 🎮 Public Playground (no auth)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 🚀 Next-Gen Strategic Features (Round 3)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 🧬 Next-Gen v2 Features
# ---------------------------------------------------------------------------
from app.api.v1 import (
    agent_swarm,
    agents_marketplace,
    ai_observatory,
    ai_safety,
    alerts,
    api_gateway,
    api_keys,
    api_monetization,
    arch_advisor,
    architecture_advisor,
    audit,
    audit_autopilot,
    audit_reports,
    audit_workspace,
    auth,
    auto_healing,
    auto_remediation,
    autonomous_os,
    autopilot,
    benchmarking,
    billing,
    blockchain_audit,
    board_reports,
    cert_autopilot,
    cert_pipeline,
    certification,
    chaos_engineering,
    chat,
    chatbot,
    cicd,
    cicd_runtime,
    client_sdk,
    cloud,
    code_review_agent,
    compliance,
    compliance_api_standard,
    compliance_badge,
    compliance_cloning,
    compliance_copilot,
    compliance_data_lake,
    compliance_data_network,
    compliance_debt,
    compliance_editor,
    compliance_export,
    compliance_gnn,
    compliance_intel,
    compliance_knowledge_graph,
    compliance_learning,
    compliance_observability,
    compliance_sandbox,
    compliance_sdk,
    compliance_streaming,
    compliance_testing,
    compliance_training,
    contract_analyzer,
    control_testing,
    copilot_chat,
    cost_attribution,
    cost_benefit_analyzer,
    cost_calculator,
    cost_engine,
    cross_border_transfer,
    cross_cloud_mesh,
    cross_org_benchmark,
    cross_repo_graph,
    customer_profiles,
    dao_governance,
    data_flow,
    data_mesh_federation,
    debt_securitization,
    dependency_scanner,
    digital_marketplace,
    digital_passport,
    digital_twin,
    digital_twin_enhanced,
    draft_reg_simulator,
    drift_detection,
    entity_rollup,
    esg_sustainability,
    evidence,
    evidence_collector,
    evidence_generation,
    evidence_vault,
    explainability,
    federated_intel,
    game_engine,
    gamification_engine,
    gh_marketplace_app,
    github_app,
    gitops_pipeline,
    graph,
    graph_explorer,
    harmonization_engine,
    health_benchmarking,
    health_score,
    horizon_scanner,
    iac_policy_engine,
    iac_scanner,
    ide,
    ide_agent,
    ide_extension,
    impact_heatmap,
    impact_simulator,
    impact_timeline,
    incident_playbook,
    incident_remediation,
    incident_war_room,
    industry_packs,
    infrastructure,
    intelligence,
    knowledge_assistant,
    knowledge_fabric,
    knowledge_graph,
    legal_copilot,
    localization_engine,
    mappings,
    marketplace,
    marketplace_app,
    marketplace_revenue,
    mcp_server,
    mobile_backend,
    model_cards,
    multi_llm,
    multi_llm_parser,
    multi_org_orchestrator,
    multi_scm,
    news_ticker,
    nl_compliance_query,
    nl_query,
    orchestration,
    org_hierarchy,
    organizations,
    pair_programming,
    pattern_marketplace,
    pia_generator,
    pipeline_builder,
    playbook,
    playground,
    plugin_ecosystem,
    policy_as_code,
    policy_dsl,
    policy_marketplace,
    policy_sdk,
    portfolio,
    posture_scoring,
    pr_bot,
    pr_copilot,
    pr_review,
    prediction_market,
    predictions,
    public_api,
    query,
    realtime_feed,
    realtime_posture,
    reg_change_stream,
    reg_prediction,
    reg_simulator,
    regulation_diff,
    regulation_diff_viz,
    regulation_test_gen,
    regulations,
    regulatory_filing,
    regulatory_intel_feed,
    regulatory_sandbox,
    regulatory_simulation,
    remediation_workflow,
    repositories,
    requirements,
    residency_map,
    risk_quantification,
    saas_onboarding,
    saas_platform,
    sandbox,
    sbom,
    scenario_planner,
    scoring,
    self_healing_mesh,
    self_hosted,
    sentiment_analyzer,
    simulator,
    sso,
    starter_kits,
    status,
    stress_testing,
    telemetry,
    telemetry_mesh,
    templates,
    testing,
    training,
    training_simulator,
    trust_network,
    twin_simulation,
    users,
    vendor_assessment,
    vendor_risk,
    webhooks,
    webhooks_outgoing,
    white_label_platform,
    workflow_automation,
    zero_trust_scanner,
)
from app.api.v1 import (
    settings as settings_router,
)

# ===========================================================================
# Router assembly
# ===========================================================================
from app.core.config import settings


router = APIRouter()

# -- 🔐 Auth & Identity ----------------------------------------------------
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(sso.router, prefix="/sso", tags=["SSO/SAML"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
router.include_router(
    org_hierarchy.router, prefix="/org-hierarchy", tags=["Organization Hierarchy"]
)
router.include_router(settings_router.router, prefix="/settings", tags=["User Settings"])
router.include_router(api_keys.router, prefix="/api-keys", tags=["API Key Management"])

# -- 📋 Compliance Core ----------------------------------------------------
router.include_router(regulations.router, prefix="/regulations", tags=["Regulations"])
router.include_router(requirements.router, prefix="/requirements", tags=["Requirements"])
router.include_router(compliance.router, prefix="/compliance", tags=["Compliance"])
router.include_router(mappings.router, prefix="/mappings", tags=["Codebase Mappings"])
router.include_router(data_flow.router, prefix="/data-flow", tags=["Cross-Border Data Flow"])
router.include_router(
    policy_as_code.router, prefix="/policy-as-code", tags=["Policy-as-Code (Rego/OPA)"]
)
router.include_router(
    policy_sdk.router, prefix="/policy-sdk", tags=["Compliance-as-Code Policy SDK"]
)
router.include_router(templates.router, prefix="/templates", tags=["Compliance Templates"])
router.include_router(starter_kits.router, prefix="/starter-kits", tags=["Regulation Starter Kits"])
router.include_router(
    industry_packs.router, prefix="/industry-packs", tags=["Industry Starter Packs"]
)

# -- 🤖 AI & Intelligence --------------------------------------------------
router.include_router(chat.router, prefix="/chat", tags=["Compliance Copilot Chat"])
router.include_router(
    chatbot.router, prefix="/chatbot", tags=["Compliance Chatbot (Deprecated — use /chat)"]
)
router.include_router(
    copilot_chat.router,
    prefix="/copilot-chat",
    tags=["Compliance Copilot Chat (Deprecated — use /chat)"],
)
router.include_router(nl_query.router, prefix="/nl-query", tags=["Natural Language Query Engine"])
router.include_router(intelligence.router, prefix="/intelligence", tags=["Regulatory Intelligence"])
router.include_router(predictions.router, prefix="/predictions", tags=["Regulatory Predictions"])
router.include_router(multi_llm.router, prefix="/multi-llm", tags=["Multi-LLM Parsing Engine"])
router.include_router(ai_safety.router, prefix="/ai-safety", tags=["AI Safety"])
router.include_router(
    explainability.router, prefix="/explainability", tags=["AI Explainability (XAI)"]
)
router.include_router(
    model_cards.router, prefix="/model-cards", tags=["AI Model Cards (EU AI Act)"]
)
router.include_router(testing.router, prefix="/testing", tags=["AI Compliance Testing Suite"])
router.include_router(
    architecture_advisor.router,
    prefix="/architecture-advisor",
    tags=["Regulation-to-Architecture Advisor"],
)

# -- 🔍 Analysis & Monitoring ----------------------------------------------
router.include_router(health_score.router, prefix="/health-score", tags=["Health Score"])
router.include_router(scoring.router, prefix="/scoring", tags=["Compliance Scoring"])
router.include_router(
    posture_scoring.router, prefix="/posture", tags=["Compliance Posture Scoring"]
)
router.include_router(
    health_benchmarking.router,
    prefix="/health-benchmarking",
    tags=["Compliance Health Score Benchmarking"],
)
router.include_router(
    drift_detection.router, prefix="/drift-detection", tags=["Compliance Drift Detection"]
)
router.include_router(digital_twin.router, prefix="/digital-twin", tags=["Compliance Digital Twin"])
router.include_router(
    impact_simulator.router, prefix="/impact-simulator", tags=["Regulatory Impact Simulator"]
)
router.include_router(
    impact_timeline.router, prefix="/impact-timeline", tags=["Regulatory Impact Timeline"]
)
router.include_router(
    impact_heatmap.router, prefix="/impact-heatmap", tags=["Regulatory Impact Heat Maps"]
)
router.include_router(
    risk_quantification.router,
    prefix="/risk-quantification",
    tags=["Compliance Risk Quantification (CRQ)"],
)
router.include_router(
    cost_calculator.router,
    prefix="/cost-calculator",
    tags=["Predictive Compliance Cost Calculator"],
)
router.include_router(simulator.router, prefix="/simulator", tags=["Scenario Simulator"])
router.include_router(alerts.router, prefix="/alerts", tags=["Regulatory Alerts"])
router.include_router(news_ticker.router, prefix="/news-ticker", tags=["Regulatory News Ticker"])
router.include_router(
    telemetry.router, prefix="/telemetry", tags=["Real-Time Compliance Telemetry"]
)
router.include_router(
    compliance_intel.router, prefix="/compliance-intel", tags=["Federated Compliance Intelligence"]
)

# -- 🛠️ Developer Tools ----------------------------------------------------
router.include_router(ide.router, prefix="/ide", tags=["IDE Integration"])
router.include_router(ide_agent.router, prefix="/ide-agent", tags=["Compliance Co-Pilot IDE Agent"])
router.include_router(cicd.router, prefix="/cicd", tags=["CI/CD Integration"])
router.include_router(pr_bot.router, tags=["PR Bot"])
router.include_router(pr_review.router, prefix="/pr-review", tags=["PR Review Co-Pilot"])
router.include_router(pr_copilot.router, prefix="/pr-copilot", tags=["Compliance PR Co-Pilot"])
router.include_router(repositories.router, prefix="/repositories", tags=["Repositories"])
router.include_router(
    iac_scanner.router, prefix="/iac-scanner", tags=["Infrastructure-as-Code Compliance Scanner"]
)
router.include_router(sbom.router, prefix="/sbom", tags=["SBOM Compliance"])
router.include_router(
    incident_remediation.router,
    prefix="/incident-remediation",
    tags=["Incident-to-Compliance Auto-Remediation"],
)

# -- 📊 Audit & Evidence ---------------------------------------------------
router.include_router(audit.router, prefix="/audit", tags=["Audit Trail"])
router.include_router(
    audit_autopilot.router, prefix="/audit-autopilot", tags=["Audit Preparation Autopilot"]
)
router.include_router(
    audit_reports.router, prefix="/audit-reports", tags=["Automatic Audit Report Generation"]
)
router.include_router(evidence.router, prefix="/evidence", tags=["Evidence Generator"])
router.include_router(
    evidence_collector.router, prefix="/evidence-collector", tags=["Evidence Collection"]
)
router.include_router(
    evidence_vault.router, prefix="/evidence-vault", tags=["Evidence Vault & Auditor Portal"]
)

# -- 📈 Marketplace & Ecosystem --------------------------------------------
router.include_router(marketplace.router, prefix="/marketplace", tags=["API Marketplace"])
router.include_router(
    marketplace_app.router, prefix="/marketplace-app", tags=["GitHub/GitLab Marketplace App"]
)
router.include_router(
    pattern_marketplace.router, prefix="/pattern-marketplace", tags=["Pattern Marketplace"]
)
router.include_router(
    policy_marketplace.router,
    prefix="/policy-marketplace",
    tags=["Compliance-as-Code Policy Marketplace"],
)

# -- 🔧 Automation & Workflows ---------------------------------------------
router.include_router(autopilot.router, prefix="/autopilot", tags=["Agentic Autopilot"])
router.include_router(
    orchestration.router, prefix="/orchestration", tags=["Compliance Orchestration"]
)
router.include_router(playbook.router, prefix="/playbook", tags=["Compliance Playbook"])
router.include_router(
    remediation_workflow.router, prefix="/remediation", tags=["Compliance Remediation Workflows"]
)
router.include_router(sandbox.router, prefix="/sandbox", tags=["Compliance Sandbox"])
router.include_router(
    regulatory_sandbox.router, prefix="/regulatory-sandbox", tags=["Regulatory Sandbox Integration"]
)

# -- 🏢 Platform & Enterprise ----------------------------------------------
router.include_router(billing.router, prefix="/billing", tags=["Billing"])
router.include_router(
    customer_profiles.router, prefix="/customer-profiles", tags=["Customer Profiles"]
)
router.include_router(saas_platform.router, prefix="/saas-platform", tags=["SaaS Platform"])
router.include_router(self_hosted.router, prefix="/self-hosted", tags=["Self-Hosted Deployment"])
router.include_router(public_api.router, prefix="/public-api", tags=["Public API & SDK"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
router.include_router(
    webhooks_outgoing.router, prefix="/webhooks/outgoing", tags=["Outgoing Webhooks"]
)

# -- 📚 Knowledge & Learning -----------------------------------------------
router.include_router(graph.router, prefix="/graph", tags=["Knowledge Graph"])
router.include_router(
    knowledge_graph.router, prefix="/knowledge-graph", tags=["Knowledge Graph Explorer"]
)
router.include_router(query.router, prefix="/query", tags=["Query Engine"])
router.include_router(training.router, prefix="/training", tags=["Compliance Training"])
router.include_router(
    certification.router, prefix="/certification", tags=["Compliance Training & Certification"]
)
router.include_router(benchmarking.router, prefix="/benchmarking", tags=["Accuracy Benchmarking"])
router.include_router(
    regulation_diff.router, prefix="/regulation-diff", tags=["Regulation Changelog Diff Viewer"]
)

# -- 🏗️ Infrastructure & Cloud ---------------------------------------------
router.include_router(cloud.router, prefix="/cloud", tags=["Cloud Compliance"])
router.include_router(infrastructure.router, tags=["Infrastructure Compliance"])

# -- 🤝 Vendor & Supply Chain ----------------------------------------------
router.include_router(vendor_risk.router, prefix="/vendor-risk", tags=["Vendor Risk"])
router.include_router(
    vendor_assessment.router, prefix="/vendor-assessment", tags=["Vendor Assessment"]
)
router.include_router(portfolio.router, prefix="/portfolios", tags=["Compliance Portfolios"])
router.include_router(
    federated_intel.router, prefix="/federated-intel", tags=["Federated Intelligence Network"]
)

# -- 📊 Platform Status (always available) -----------------------------------
router.include_router(status.router, prefix="/status", tags=["Platform Status"])

# -- 🎮 Public Playground (no auth required) ---------------------------------
router.include_router(playground.router, prefix="/playground", tags=["Compliance Playground"])

# -- 🚀 Next-Gen Strategic Features ------------------------------------------
router.include_router(
    horizon_scanner.router, prefix="/horizon-scanner", tags=["Regulatory Horizon Scanner"]
)
router.include_router(
    control_testing.router, prefix="/control-testing", tags=["Continuous Control Testing"]
)
router.include_router(
    compliance_knowledge_graph.router,
    prefix="/compliance-graph",
    tags=["Compliance Knowledge Graph"],
)
router.include_router(
    entity_rollup.router, prefix="/entity-rollup", tags=["Multi-Entity Compliance Rollup"]
)
router.include_router(board_reports.router, prefix="/board-reports", tags=["AI Board Reports"])
router.include_router(gitops_pipeline.router, prefix="/gitops", tags=["GitOps Compliance Pipeline"])
router.include_router(residency_map.router, prefix="/residency-map", tags=["Data Residency Map"])
router.include_router(
    dependency_scanner.router, prefix="/dependency-scanner", tags=["Dependency Risk Scanner"]
)
router.include_router(
    audit_workspace.router, prefix="/audit-workspace", tags=["Self-Service Audit Workspace"]
)

# -- 🧬 Next-Gen v2 Platform Features ----------------------------------------
router.include_router(
    auto_healing.router, prefix="/auto-healing", tags=["Auto-Healing Compliance Pipeline"]
)
router.include_router(
    realtime_posture.router, prefix="/realtime-posture", tags=["Real-Time Compliance Posture"]
)
router.include_router(
    cross_repo_graph.router, prefix="/cross-repo-graph", tags=["Cross-Repository Compliance Graph"]
)
router.include_router(
    cost_engine.router, prefix="/cost-engine", tags=["Compliance Cost Attribution"]
)
router.include_router(
    reg_simulator.router, prefix="/reg-simulator", tags=["Regulatory Change Simulator"]
)
router.include_router(
    cert_autopilot.router, prefix="/cert-autopilot", tags=["Certification Autopilot"]
)
router.include_router(
    iac_policy_engine.router, prefix="/iac-policy", tags=["Multi-Cloud IaC Policy Engine"]
)
router.include_router(
    compliance_learning.router,
    prefix="/compliance-learning",
    tags=["Compliance Training & Learning"],
)
router.include_router(
    compliance_data_network.router,
    prefix="/compliance-network",
    tags=["Open Compliance Data Network"],
)

# -- 🌐 Next-Gen & Experimental Features ------------------------------------
# These routes are gated behind ENABLE_EXPERIMENTAL (default: True in dev).
# Set ENABLE_EXPERIMENTAL=false in production to reduce attack surface.
if settings.enable_experimental:
    router.include_router(
        cross_border_transfer.router,
        prefix="/cross-border-transfer",
        tags=["Cross-Border Data Transfer Automation"],
    )
    router.include_router(
        stress_testing.router,
        prefix="/stress-testing",
        tags=["Regulatory Compliance Stress Testing"],
    )
    router.include_router(
        zero_trust_scanner.router,
        prefix="/zero-trust-scanner",
        tags=["Zero-Trust Compliance Architecture Scanner"],
    )
    router.include_router(
        compliance_training.router,
        prefix="/compliance-training",
        tags=["Continuous Compliance Training Copilot"],
    )
    router.include_router(
        ai_observatory.router, prefix="/ai-observatory", tags=["AI Model Compliance Observatory"]
    )
    router.include_router(
        regulation_test_gen.router,
        prefix="/regulation-test-gen",
        tags=["Regulation-to-Test-Case Generator"],
    )
    router.include_router(
        sentiment_analyzer.router,
        prefix="/sentiment-analyzer",
        tags=["Regulatory Change Sentiment Analyzer"],
    )
    router.include_router(
        incident_playbook.router,
        prefix="/incident-playbook",
        tags=["Incident Response Compliance Playbook"],
    )
    router.include_router(
        cost_attribution.router,
        prefix="/cost-attribution",
        tags=["Compliance Cost Attribution Engine"],
    )
    router.include_router(
        blockchain_audit.router,
        prefix="/blockchain-audit",
        tags=["Blockchain-Based Compliance Audit Trail"],
    )
    router.include_router(
        digital_twin_enhanced.router,
        prefix="/digital-twin-enhanced",
        tags=["Enhanced Digital Twin"],
    )
    router.include_router(
        chaos_engineering.router, prefix="/chaos-engineering", tags=["Compliance Chaos Engineering"]
    )
    router.include_router(
        dao_governance.router, prefix="/dao-governance", tags=["Compliance DAO Governance"]
    )
    router.include_router(
        debt_securitization.router,
        prefix="/debt-securitization",
        tags=["Compliance Debt Securitization"],
    )
    router.include_router(
        prediction_market.router,
        prefix="/prediction-market",
        tags=["Compliance Impact Prediction Market"],
    )
    router.include_router(
        pair_programming.router,
        prefix="/pair-programming",
        tags=["Real-Time Compliance Pair Programming"],
    )
    router.include_router(
        game_engine.router, prefix="/game-engine", tags=["Compliance Simulation Game Engine"]
    )
    router.include_router(
        compliance_cloning.router,
        prefix="/compliance-cloning",
        tags=["Cross-Codebase Compliance Cloning"],
    )
    router.include_router(
        compliance_sandbox.router,
        prefix="/compliance-sandbox",
        tags=["Compliance Sandbox Environments"],
    )
    router.include_router(
        api_monetization.router,
        prefix="/api-monetization",
        tags=["Compliance API Monetization Layer"],
    )

# -- 🔮 Next-Gen v3 Features (10 new capabilities) --------------------------
router.include_router(
    mcp_server.router, prefix="/mcp-server", tags=["Compliance MCP Server"]
)
router.include_router(
    github_app.router, prefix="/github-app", tags=["GitHub App One-Click Install"]
)
router.include_router(
    reg_change_stream.router,
    prefix="/reg-change-stream",
    tags=["Real-Time Regulatory Change Stream"],
)
router.include_router(
    compliance_sdk.router, prefix="/compliance-sdk", tags=["Compliance-as-Code SDK"]
)
router.include_router(
    compliance_copilot.router,
    prefix="/compliance-copilot",
    tags=["AI Compliance Co-Pilot"],
)
router.include_router(
    auto_remediation.router,
    prefix="/auto-remediation",
    tags=["Compliance Drift Auto-Remediation"],
)
router.include_router(
    multi_scm.router, prefix="/multi-scm", tags=["Multi-SCM Support"]
)
router.include_router(
    compliance_badge.router,
    prefix="/compliance-badge",
    tags=["Compliance Score Badge & Scorecard"],
)
router.include_router(
    regulation_diff_viz.router,
    prefix="/regulation-diff-viz",
    tags=["Regulation Diff Visualizer"],
)
router.include_router(
    compliance_export.router,
    prefix="/compliance-export",
    tags=["Compliance Data Export & BI Integration"],
)

# -- 🚀 Next-Gen v4 Features (10 new capabilities) --------------------------
router.include_router(
    agents_marketplace.router,
    prefix="/agents-marketplace",
    tags=["Compliance Agents Marketplace"],
)
router.include_router(
    saas_onboarding.router,
    prefix="/saas-onboarding",
    tags=["Zero-Config Compliance SaaS"],
)
router.include_router(
    code_review_agent.router,
    prefix="/code-review-agent",
    tags=["Compliance-Aware Code Review Agent"],
)
router.include_router(
    reg_prediction.router,
    prefix="/reg-prediction",
    tags=["Regulatory Impact Prediction"],
)
router.include_router(
    compliance_observability.router,
    prefix="/compliance-observability",
    tags=["Compliance Observability Pipeline"],
)
router.include_router(
    nl_compliance_query.router,
    prefix="/nl-compliance-query",
    tags=["Natural Language Compliance Queries"],
)
router.include_router(
    twin_simulation.router,
    prefix="/twin-simulation",
    tags=["Compliance Digital Twin Simulation"],
)
router.include_router(
    cross_org_benchmark.router,
    prefix="/cross-org-benchmark",
    tags=["Cross-Organization Compliance Benchmarking"],
)
router.include_router(
    evidence_generation.router,
    prefix="/evidence-generation",
    tags=["Automated Evidence Generation"],
)
router.include_router(
    cost_benefit_analyzer.router,
    prefix="/cost-benefit-analyzer",
    tags=["Compliance Cost-Benefit Analyzer"],
)

# -- 🧠 Next-Gen v5 Features (10 new capabilities) --------------------------
router.include_router(
    knowledge_fabric.router,
    prefix="/knowledge-fabric",
    tags=["Compliance Knowledge Fabric"],
)
router.include_router(
    self_healing_mesh.router,
    prefix="/self-healing-mesh",
    tags=["Self-Healing Compliance Mesh"],
)
router.include_router(
    ide_extension.router,
    prefix="/ide-extension",
    tags=["Compliance Copilot IDE Extension"],
)
router.include_router(
    compliance_data_lake.router,
    prefix="/compliance-data-lake",
    tags=["Multi-Tenant Compliance Data Lake"],
)
router.include_router(
    policy_dsl.router,
    prefix="/policy-dsl",
    tags=["Compliance-as-Code Policy Language"],
)
router.include_router(
    realtime_feed.router,
    prefix="/realtime-feed",
    tags=["Real-Time Regulatory Change Feed"],
)
router.include_router(
    compliance_gnn.router,
    prefix="/compliance-gnn",
    tags=["Compliance Graph Neural Network"],
)
router.include_router(
    cert_pipeline.router,
    prefix="/cert-pipeline",
    tags=["Automated Certification Pipeline"],
)
router.include_router(
    api_gateway.router,
    prefix="/api-gateway",
    tags=["Compliance API Gateway"],
)
router.include_router(
    workflow_automation.router,
    prefix="/workflow-automation",
    tags=["Compliance Workflow Automation"],
)

# -- 💎 Next-Gen v6 Features (10 new capabilities) --------------------------
router.include_router(
    gh_marketplace_app.router,
    prefix="/gh-marketplace-app",
    tags=["Compliance Copilot GitHub App"],
)
router.include_router(
    compliance_streaming.router,
    prefix="/compliance-streaming",
    tags=["Real-Time Compliance Streaming"],
)
router.include_router(
    client_sdk.router,
    prefix="/client-sdk",
    tags=["Compliance Agent SDK"],
)
router.include_router(
    multi_llm_parser.router,
    prefix="/multi-llm-parser",
    tags=["Multi-LLM Compliance Parsing"],
)
router.include_router(
    compliance_testing.router,
    prefix="/compliance-testing",
    tags=["Compliance Testing Framework"],
)
router.include_router(
    arch_advisor.router,
    prefix="/arch-advisor",
    tags=["Regulation-to-Architecture Advisor"],
)
router.include_router(
    incident_war_room.router,
    prefix="/incident-war-room",
    tags=["Compliance Incident War Room"],
)
router.include_router(
    compliance_debt.router,
    prefix="/compliance-debt",
    tags=["Compliance Debt Dashboard"],
)
router.include_router(
    draft_reg_simulator.router,
    prefix="/draft-reg-simulator",
    tags=["Draft Regulation Impact Simulator"],
)
router.include_router(
    gamification_engine.router,
    prefix="/gamification-engine",
    tags=["Compliance Gamification Engine"],
)

# -- 🌐 Next-Gen v7 Features (10 new capabilities) --------------------------
router.include_router(
    data_mesh_federation.router,
    prefix="/data-mesh-federation",
    tags=["Compliance Data Mesh Federation"],
)
router.include_router(
    agent_swarm.router,
    prefix="/agent-swarm",
    tags=["Agentic Compliance Swarm"],
)
router.include_router(
    compliance_editor.router,
    prefix="/compliance-editor",
    tags=["Compliance-Native Code Editor"],
)
router.include_router(
    graph_explorer.router,
    prefix="/graph-explorer",
    tags=["Regulatory Knowledge Graph Explorer"],
)
router.include_router(
    pipeline_builder.router,
    prefix="/pipeline-builder",
    tags=["Compliance CI/CD Pipeline Builder"],
)
router.include_router(
    pia_generator.router,
    prefix="/pia-generator",
    tags=["Privacy Impact Assessment Generator"],
)
router.include_router(
    contract_analyzer.router,
    prefix="/contract-analyzer",
    tags=["Compliance Contract Analyzer"],
)
router.include_router(
    mobile_backend.router,
    prefix="/mobile-backend",
    tags=["Compliance Mobile App Backend"],
)
router.include_router(
    marketplace_revenue.router,
    prefix="/marketplace-revenue",
    tags=["Compliance Marketplace Revenue Engine"],
)
router.include_router(
    localization_engine.router,
    prefix="/localization-engine",
    tags=["Compliance Localization Engine"],
)

# -- 🏛️ Next-Gen v8 Features (10 new capabilities) --------------------------
router.include_router(
    autonomous_os.router,
    prefix="/autonomous-os",
    tags=["Compliance Autonomous Operating System"],
)
router.include_router(
    trust_network.router,
    prefix="/trust-network",
    tags=["Compliance Trust Network"],
)
router.include_router(
    compliance_api_standard.router,
    prefix="/compliance-api-standard",
    tags=["Universal Compliance API Standard"],
)
router.include_router(
    digital_marketplace.router,
    prefix="/digital-marketplace",
    tags=["Compliance Digital Marketplace B2B"],
)
router.include_router(
    regulatory_simulation.router,
    prefix="/regulatory-simulation",
    tags=["Regulatory Simulation Engine"],
)
router.include_router(
    legal_copilot.router,
    prefix="/legal-copilot",
    tags=["Compliance Copilot for Legal"],
)
router.include_router(
    regulatory_intel_feed.router,
    prefix="/regulatory-intel-feed",
    tags=["Real-Time Regulatory Intelligence Feed"],
)
router.include_router(
    white_label_platform.router,
    prefix="/white-label-platform",
    tags=["Compliance-as-a-Service White-Label"],
)
router.include_router(
    cross_cloud_mesh.router,
    prefix="/cross-cloud-mesh",
    tags=["Cross-Cloud Compliance Mesh"],
)
router.include_router(
    esg_sustainability.router,
    prefix="/esg-sustainability",
    tags=["Compliance Sustainability ESG Module"],
)

# -- ⚡ Next-Gen v9 Features (10 new capabilities) --------------------------
router.include_router(telemetry_mesh.router, prefix="/telemetry-mesh", tags=["Compliance Telemetry Mesh"])
router.include_router(knowledge_assistant.router, prefix="/knowledge-assistant", tags=["Compliance Knowledge Assistant"])
router.include_router(digital_passport.router, prefix="/digital-passport", tags=["Regulatory Digital Passport"])
router.include_router(scenario_planner.router, prefix="/scenario-planner", tags=["Compliance Scenario Planner"])
router.include_router(regulatory_filing.router, prefix="/regulatory-filing", tags=["Automated Regulatory Filing"])
router.include_router(cicd_runtime.router, prefix="/cicd-runtime", tags=["Compliance-Aware CI/CD Runtime"])
router.include_router(multi_org_orchestrator.router, prefix="/multi-org-orchestrator", tags=["Multi-Org Compliance Orchestrator"])
router.include_router(training_simulator.router, prefix="/training-simulator", tags=["Compliance Training Simulator"])
router.include_router(harmonization_engine.router, prefix="/harmonization-engine", tags=["Regulatory Harmonization Engine"])
router.include_router(plugin_ecosystem.router, prefix="/plugin-ecosystem", tags=["Compliance Plugin Ecosystem"])
