"""Service implementation status endpoint.

Exposes a machine-readable view of which backend services are fully
implemented, which are stubs returning synthetic data, and which are
planned but not yet started.  The data mirrors ``backend/app/services/STATUS.md``.
"""

from __future__ import annotations

from enum import Enum

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()


class ServiceStatus(str, Enum):
    IMPLEMENTED = "implemented"
    STUB = "stub"
    PLANNED = "planned"


class ServiceInfo(BaseModel):
    name: str
    status: ServiceStatus
    description: str = ""


class StatusResponse(BaseModel):
    total: int
    implemented: int
    stub: int
    planned: int
    services: list[ServiceInfo]


# ---------------------------------------------------------------------------
# Registry — keep in sync with backend/app/services/STATUS.md
# ---------------------------------------------------------------------------

_SERVICES: list[tuple[str, ServiceStatus, str]] = [
    ("ai_observatory", ServiceStatus.STUB, "Synthetic AI monitoring metrics"),
    ("api_monetization", ServiceStatus.STUB, "Hardcoded API catalog, in-memory pricing"),
    ("architecture_advisor", ServiceStatus.IMPLEMENTED, "Compliance architecture analysis"),
    ("audit", ServiceStatus.IMPLEMENTED, "Hash chain verification, real DB queries"),
    ("audit_autopilot", ServiceStatus.IMPLEMENTED, "Automated audit workflows"),
    ("audit_reports", ServiceStatus.IMPLEMENTED, "Report generation with DB storage"),
    ("audit_workspace", ServiceStatus.IMPLEMENTED, "Self-service audit preparation workspace"),
    ("autopilot", ServiceStatus.IMPLEMENTED, "Automated compliance workflows"),
    ("benchmarking", ServiceStatus.IMPLEMENTED, "Compliance benchmarking"),
    ("billing", ServiceStatus.IMPLEMENTED, "Billing integration"),
    ("blockchain_audit", ServiceStatus.IMPLEMENTED, "Blockchain audit trail"),
    ("board_reports", ServiceStatus.IMPLEMENTED, "AI-powered executive compliance reports"),
    ("certification", ServiceStatus.IMPLEMENTED, "Certification management"),
    ("chaos_engineering", ServiceStatus.STUB, "Hardcoded experiments, in-memory"),
    ("chat", ServiceStatus.IMPLEMENTED, "Chat service with DB persistence"),
    ("chatbot", ServiceStatus.IMPLEMENTED, "Chatbot with DB-backed conversations"),
    ("cicd", ServiceStatus.IMPLEMENTED, "CI/CD compliance checks"),
    ("cloud", ServiceStatus.STUB, "Static cloud posture rules, in-memory"),
    ("compliance_cloning", ServiceStatus.STUB, "Hardcoded reference repos, in-memory"),
    ("compliance_intel", ServiceStatus.STUB, "Synthetic intelligence data"),
    (
        "compliance_knowledge_graph",
        ServiceStatus.IMPLEMENTED,
        "Navigable compliance relationship graph with NL queries",
    ),
    ("compliance_sandbox", ServiceStatus.IMPLEMENTED, "Compliance sandbox with DB"),
    ("compliance_training", ServiceStatus.STUB, "Synthetic training progress data"),
    (
        "control_testing",
        ServiceStatus.IMPLEMENTED,
        "Automated continuous control testing with evidence",
    ),
    ("copilot_chat", ServiceStatus.IMPLEMENTED, "Copilot chat integration"),
    ("cost_attribution", ServiceStatus.STUB, "Synthetic cost attribution"),
    (
        "cost_calculator",
        ServiceStatus.IMPLEMENTED,
        "Predictive cost estimator with industry benchmarks",
    ),
    ("cross_border_transfer", ServiceStatus.IMPLEMENTED, "Cross-border data transfer compliance"),
    ("dao_governance", ServiceStatus.STUB, "In-memory proposals with seed data"),
    ("data_flow", ServiceStatus.IMPLEMENTED, "Data flow mapping and analysis"),
    ("debt", ServiceStatus.STUB, "Hardcoded debt items, in-memory"),
    (
        "dependency_scanner",
        ServiceStatus.IMPLEMENTED,
        "License, security, and compliance risk scanning",
    ),
    ("diff_alerts", ServiceStatus.IMPLEMENTED, "Regulation diff alerts"),
    ("digital_twin", ServiceStatus.STUB, "Synthetic digital twin simulation"),
    ("drift_detection", ServiceStatus.IMPLEMENTED, "Configuration drift detection"),
    ("enterprise", ServiceStatus.STUB, "SAML mock, in-memory assertions"),
    ("entity_rollup", ServiceStatus.IMPLEMENTED, "Multi-entity aggregated compliance scoring"),
    ("evidence", ServiceStatus.IMPLEMENTED, "Evidence management"),
    ("evidence_collector", ServiceStatus.IMPLEMENTED, "Automated evidence collection"),
    ("evidence_vault", ServiceStatus.IMPLEMENTED, "Secure evidence vault"),
    ("explainability", ServiceStatus.STUB, "In-memory reasoning engine"),
    ("federated_intel", ServiceStatus.STUB, "In-memory network simulation"),
    ("game_engine", ServiceStatus.IMPLEMENTED, "Gamification engine"),
    ("generation", ServiceStatus.IMPLEMENTED, "AI code generation via CopilotClient"),
    ("github", ServiceStatus.IMPLEMENTED, "GitHub API integration"),
    ("gitlab", ServiceStatus.IMPLEMENTED, "GitLab API integration"),
    (
        "gitops_pipeline",
        ServiceStatus.IMPLEMENTED,
        "GitOps compliance pipeline with pre-commit hooks",
    ),
    ("graph", ServiceStatus.STUB, "Deprecated; in-memory"),
    ("health_benchmarking", ServiceStatus.IMPLEMENTED, "Health benchmarking"),
    ("health_score", ServiceStatus.STUB, "Synthetic health score metrics"),
    (
        "horizon_scanner",
        ServiceStatus.IMPLEMENTED,
        "Regulatory horizon scanning with impact predictions",
    ),
    ("iac_scanner", ServiceStatus.IMPLEMENTED, "Infrastructure-as-Code scanner"),
    ("ide", ServiceStatus.IMPLEMENTED, "IDE integration service"),
    ("ide_agent", ServiceStatus.IMPLEMENTED, "IDE agent service"),
    ("impact_heatmap", ServiceStatus.STUB, "Synthetic heatmap values"),
    ("impact_simulator", ServiceStatus.IMPLEMENTED, "Impact simulation"),
    ("impact_timeline", ServiceStatus.IMPLEMENTED, "Impact timeline tracking"),
    ("incident_playbook", ServiceStatus.IMPLEMENTED, "Incident response playbooks"),
    ("incident_remediation", ServiceStatus.STUB, "In-memory incidents with seed data"),
    ("industry_packs", ServiceStatus.IMPLEMENTED, "Industry compliance packs"),
    ("infrastructure", ServiceStatus.STUB, "Static Terraform/K8s rules, in-memory"),
    ("intelligence", ServiceStatus.IMPLEMENTED, "Compliance intelligence feeds"),
    ("knowledge_graph", ServiceStatus.STUB, "Synthetic graph edge weights"),
    ("legal", ServiceStatus.PLANNED, "Not yet started"),
    ("mapping", ServiceStatus.STUB, "AI prompts defined, no client integration"),
    ("marketplace", ServiceStatus.IMPLEMENTED, "Marketplace integration"),
    ("marketplace_app", ServiceStatus.IMPLEMENTED, "Marketplace app management"),
    ("model_cards", ServiceStatus.STUB, "In-memory card generation"),
    ("monitoring", ServiceStatus.IMPLEMENTED, "Comprehensive monitoring"),
    ("multi_llm", ServiceStatus.IMPLEMENTED, "Multi-LLM orchestration"),
    ("news_ticker", ServiceStatus.IMPLEMENTED, "Compliance news feed"),
    ("nl_query", ServiceStatus.IMPLEMENTED, "Natural language query engine"),
    ("notification", ServiceStatus.IMPLEMENTED, "Notification delivery"),
    ("orchestration", ServiceStatus.STUB, "In-memory repo management"),
    ("org_hierarchy", ServiceStatus.IMPLEMENTED, "Organization hierarchy"),
    ("pair_programming", ServiceStatus.IMPLEMENTED, "Pair programming compliance"),
    ("parsing", ServiceStatus.IMPLEMENTED, "Code parsing service"),
    ("pattern_marketplace", ServiceStatus.IMPLEMENTED, "Pattern marketplace"),
    ("playbook", ServiceStatus.IMPLEMENTED, "Compliance playbooks"),
    ("policy", ServiceStatus.PLANNED, "Deprecated redirect"),
    ("policy_as_code", ServiceStatus.STUB, "In-memory Rego generation"),
    ("policy_marketplace", ServiceStatus.STUB, "Hardcoded policy packs, in-memory"),
    ("policy_sdk", ServiceStatus.IMPLEMENTED, "Compliance-as-code SDK"),
    ("portfolio", ServiceStatus.IMPLEMENTED, "Compliance portfolio management"),
    ("posture_scoring", ServiceStatus.IMPLEMENTED, "Security posture scoring"),
    ("pr_bot", ServiceStatus.STUB, "Bot logic present but no GitHub API connection"),
    ("pr_copilot", ServiceStatus.IMPLEMENTED, "PR copilot integration"),
    ("pr_review", ServiceStatus.IMPLEMENTED, "PR compliance review"),
    ("prediction", ServiceStatus.IMPLEMENTED, "Compliance prediction"),
    ("prediction_market", ServiceStatus.STUB, "Hardcoded markets, in-memory"),
    ("predictions", ServiceStatus.STUB, "Synthetic probability data"),
    ("public_api", ServiceStatus.IMPLEMENTED, "Public API management"),
    ("query", ServiceStatus.PLANNED, "Deprecated redirect"),
    ("query_engine", ServiceStatus.IMPLEMENTED, "NL compliance query engine"),
    ("radar", ServiceStatus.PLANNED, "Not yet started"),
    ("regulation_diff", ServiceStatus.STUB, "Hardcoded regulation versions"),
    ("regulation_test_gen", ServiceStatus.STUB, "Synthetic test case generation"),
    ("remediation_workflow", ServiceStatus.IMPLEMENTED, "Remediation workflows"),
    (
        "residency_map",
        ServiceStatus.IMPLEMENTED,
        "Data residency jurisdiction mapping and violation detection",
    ),
    ("risk_quantification", ServiceStatus.IMPLEMENTED, "Risk quantification engine"),
    ("saas_platform", ServiceStatus.IMPLEMENTED, "SaaS platform management"),
    ("sandbox", ServiceStatus.STUB, "In-memory simulation engine"),
    ("sbom", ServiceStatus.IMPLEMENTED, "Software Bill of Materials"),
    ("scoring", ServiceStatus.IMPLEMENTED, "Compliance scoring"),
    ("self_hosted", ServiceStatus.IMPLEMENTED, "Self-hosted deployment service"),
    ("sentiment_analyzer", ServiceStatus.STUB, "Synthetic sentiment analysis"),
    ("simulator", ServiceStatus.IMPLEMENTED, "Compliance simulator"),
    ("starter_kits", ServiceStatus.IMPLEMENTED, "Starter kit templates"),
    ("stress_testing", ServiceStatus.STUB, "Synthetic stress test results"),
    ("telemetry", ServiceStatus.STUB, "Synthetic telemetry metrics"),
    ("templates", ServiceStatus.IMPLEMENTED, "Template management"),
    ("testing", ServiceStatus.IMPLEMENTED, "Compliance testing framework"),
    ("training", ServiceStatus.IMPLEMENTED, "Compliance training platform"),
    ("vendor", ServiceStatus.STUB, "Deprecated; in-memory"),
    ("vendor_assessment", ServiceStatus.IMPLEMENTED, "Vendor compliance assessment"),
    ("vendor_risk", ServiceStatus.STUB, "In-memory dependency scanning"),
    ("zero_trust_scanner", ServiceStatus.STUB, "Synthetic scan findings"),
]


def _build_response(
    status_filter: ServiceStatus | None = None,
) -> StatusResponse:
    filtered = [s for s in _SERVICES if s[1] == status_filter] if status_filter else list(_SERVICES)

    services = [
        ServiceInfo(name=name, status=status, description=desc) for name, status, desc in filtered
    ]

    all_statuses = [s[1] for s in _SERVICES]
    return StatusResponse(
        total=len(_SERVICES),
        implemented=sum(1 for s in all_statuses if s == ServiceStatus.IMPLEMENTED),
        stub=sum(1 for s in all_statuses if s == ServiceStatus.STUB),
        planned=sum(1 for s in all_statuses if s == ServiceStatus.PLANNED),
        services=services,
    )


@router.get(
    "/",
    response_model=StatusResponse,
    summary="Get service implementation status",
)
async def get_service_status(
    status: ServiceStatus | None = None,
) -> StatusResponse:
    """Return the implementation status of all backend services.

    Use the optional ``status`` query parameter to filter:
    ``?status=implemented``, ``?status=stub``, or ``?status=planned``.
    """
    return _build_response(status)


# ── Health & Architecture Endpoints ─────────────────────────────────────


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    services_total: int = 0
    routes_total: int = 0
    db_backed_services: int = 0
    in_memory_services: int = 0


class ArchitectureOverview(BaseModel):
    total_services: int = 0
    db_backed: list[str] = []
    in_memory: list[str] = []
    http_calling: list[str] = []
    service_generations: dict[str, int] = {}


# Services known to use real DB queries (self.db.execute/self.db.add)
_DB_BACKED = [
    "audit",
    "audit_reports",
    "audit_autopilot",
    "autopilot",
    "benchmarking",
    "billing",
    "blockchain_audit",
    "certification",
    "chat",
    "chatbot",
]

# Services known to make real HTTP calls
_HTTP_CALLING = ["github", "gitlab", "monitoring", "notification"]

_V3_V9_SERVICES = {
    "v3": [
        "mcp_server",
        "github_app",
        "reg_change_stream",
        "compliance_sdk",
        "compliance_copilot",
        "auto_remediation",
        "multi_scm",
        "compliance_badge",
        "regulation_diff_viz",
        "compliance_export",
    ],
    "v4": [
        "agents_marketplace",
        "saas_onboarding",
        "code_review_agent",
        "reg_prediction",
        "compliance_observability",
        "nl_compliance_query",
        "twin_simulation",
        "cross_org_benchmark",
        "evidence_generation",
        "cost_benefit_analyzer",
    ],
    "v5": [
        "knowledge_fabric",
        "self_healing_mesh",
        "ide_extension",
        "compliance_data_lake",
        "policy_dsl",
        "realtime_feed",
        "compliance_gnn",
        "cert_pipeline",
        "api_gateway",
        "workflow_automation",
    ],
    "v6": [
        "gh_marketplace_app",
        "compliance_streaming",
        "client_sdk",
        "multi_llm_parser",
        "compliance_testing",
        "arch_advisor",
        "incident_war_room",
        "compliance_debt",
        "draft_reg_simulator",
        "gamification_engine",
    ],
    "v7": [
        "data_mesh_federation",
        "agent_swarm",
        "compliance_editor",
        "graph_explorer",
        "pipeline_builder",
        "pia_generator",
        "contract_analyzer",
        "mobile_backend",
        "marketplace_revenue",
        "localization_engine",
    ],
    "v8": [
        "autonomous_os",
        "trust_network",
        "compliance_api_standard",
        "digital_marketplace",
        "regulatory_simulation",
        "legal_copilot",
        "regulatory_intel_feed",
        "white_label_platform",
        "cross_cloud_mesh",
        "esg_sustainability",
    ],
    "v9": [
        "telemetry_mesh",
        "knowledge_assistant",
        "digital_passport",
        "scenario_planner",
        "regulatory_filing",
        "cicd_runtime",
        "multi_org_orchestrator",
        "training_simulator",
        "harmonization_engine",
        "plugin_ecosystem",
    ],
}


@router.get("/health", response_model=HealthResponse, summary="Platform health check")
async def health_check() -> HealthResponse:
    """Quick health check returning service counts and status."""
    all_v3v9 = sum(len(v) for v in _V3_V9_SERVICES.values())
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        services_total=128 + all_v3v9,  # core + v3-v9
        routes_total=200,
        db_backed_services=len(_DB_BACKED),
        in_memory_services=all_v3v9 + 29,  # v3-v9 + stubs
    )


@router.get("/architecture", response_model=ArchitectureOverview, summary="Architecture overview")
async def architecture_overview() -> ArchitectureOverview:
    """Show which services are DB-backed vs in-memory."""
    all_in_memory = []
    for services in _V3_V9_SERVICES.values():
        all_in_memory.extend(services)
    return ArchitectureOverview(
        total_services=128 + len(all_in_memory),
        db_backed=_DB_BACKED,
        in_memory=all_in_memory,
        http_calling=_HTTP_CALLING,
        service_generations={k: len(v) for k, v in _V3_V9_SERVICES.items()},
    )


class RuntimeServiceCheck(BaseModel):
    """Result of a runtime service import check."""

    name: str
    importable: bool
    module: str
    tier: str = "unknown"
    error: str | None = None


class RuntimeHealthResponse(BaseModel):
    """Runtime health check of all registered services."""

    total_checked: int
    healthy: int
    unhealthy: int
    services: list[RuntimeServiceCheck]


@router.get(
    "/services/runtime",
    response_model=RuntimeHealthResponse,
    summary="Runtime service health",
)
async def runtime_service_health() -> RuntimeHealthResponse:
    """Check which services are importable at runtime.

    Performs a live import check for each core service module,
    surfacing any import errors that would prevent the service
    from being used.
    """
    import importlib

    from app.core.feature_flags import registry

    checks: list[RuntimeServiceCheck] = []

    for name, svc_status, _desc in _SERVICES:
        module_path = f"app.services.{name}"
        flag = registry.get(name)
        tier = flag.tier.value if flag else "unknown"

        try:
            importlib.import_module(module_path)
            checks.append(
                RuntimeServiceCheck(
                    name=name,
                    importable=True,
                    module=module_path,
                    tier=tier,
                )
            )
        except Exception as exc:
            checks.append(
                RuntimeServiceCheck(
                    name=name,
                    importable=False,
                    module=module_path,
                    tier=tier,
                    error=str(exc)[:200],
                )
            )

    healthy = sum(1 for c in checks if c.importable)
    return RuntimeHealthResponse(
        total_checked=len(checks),
        healthy=healthy,
        unhealthy=len(checks) - healthy,
        services=checks,
    )
