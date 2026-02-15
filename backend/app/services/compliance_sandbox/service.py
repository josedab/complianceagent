"""Compliance Sandbox service for training environments."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import structlog

from app.services.compliance_sandbox.models import (
    DifficultyLevel,
    SandboxBadge,
    SandboxEnvironment,
    SandboxProgress,
    SandboxResources,
    SandboxResult,
    SandboxScenario,
    SandboxStatus,
    ViolationScenario,
    ViolationType,
    WhatIfImpact,
    WhatIfScenario,
)


logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Pre-built scenarios
# ---------------------------------------------------------------------------

_SCENARIOS: list[SandboxScenario] = [
    SandboxScenario(
        id="gdpr-data-protection-101",
        title="GDPR Data Protection Fundamentals",
        description=(
            "A SaaS user-management microservice that stores personal data with "
            "several GDPR violations. Find and fix issues related to data exposure, "
            "missing consent, and excessive data retention."
        ),
        regulation="GDPR",
        difficulty=DifficultyLevel.BEGINNER,
        estimated_minutes=30,
        learning_objectives=[
            "Identify unprotected PII in API responses",
            "Implement proper data consent mechanisms",
            "Apply data minimisation principles",
        ],
        prerequisites=["Basic Python knowledge", "REST API familiarity"],
        tags=["gdpr", "data-privacy", "beginner"],
        violations=[
            ViolationScenario(
                id="gdpr-v1-data-exposure",
                type=ViolationType.DATA_EXPOSURE,
                title="User PII exposed in API response",
                description="The /users endpoint returns full SSN and date of birth without masking.",
                file_path="services/user_service.py",
                code_snippet=(
                    'def get_user(user_id):\n'
                    '    user = db.query(User).get(user_id)\n'
                    '    return {"name": user.name, "email": user.email,\n'
                    '            "ssn": user.ssn, "dob": user.dob}'
                ),
                hint="Sensitive fields like SSN should be masked or excluded from API responses.",
                solution_snippet=(
                    'def get_user(user_id):\n'
                    '    user = db.query(User).get(user_id)\n'
                    '    return {"name": user.name, "email": user.email,\n'
                    '            "ssn": mask_ssn(user.ssn), "dob": None}'
                ),
                points=10,
                regulation_article="GDPR Art. 5(1)(c) - Data Minimisation",
            ),
            ViolationScenario(
                id="gdpr-v2-missing-consent",
                type=ViolationType.MISSING_CONSENT,
                title="No consent tracking for marketing emails",
                description="Users are added to marketing lists without explicit opt-in consent.",
                file_path="services/marketing_service.py",
                code_snippet=(
                    "def register_user(email, name):\n"
                    "    user = create_user(email, name)\n"
                    "    add_to_marketing_list(email)\n"
                    "    return user"
                ),
                hint="GDPR requires freely given, specific, informed consent before processing for marketing.",
                solution_snippet=(
                    'def register_user(email, name, marketing_consent=False):\n'
                    '    user = create_user(email, name)\n'
                    '    if marketing_consent:\n'
                    '        record_consent(user.id, "marketing", datetime.utcnow())\n'
                    '        add_to_marketing_list(email)\n'
                    '    return user'
                ),
                points=15,
                regulation_article="GDPR Art. 7 - Conditions for Consent",
            ),
            ViolationScenario(
                id="gdpr-v3-retention",
                type=ViolationType.EXCESSIVE_RETENTION,
                title="No data retention policy enforced",
                description="Deleted user records are soft-deleted but never purged from the database.",
                file_path="services/user_service.py",
                code_snippet=(
                    "def delete_user(user_id):\n"
                    "    user = db.query(User).get(user_id)\n"
                    "    user.is_deleted = True\n"
                    "    db.commit()"
                ),
                hint="Implement a retention window and hard-delete personal data after the period expires.",
                solution_snippet=(
                    "def delete_user(user_id):\n"
                    "    user = db.query(User).get(user_id)\n"
                    "    user.is_deleted = True\n"
                    "    user.deletion_scheduled_at = datetime.utcnow() + timedelta(days=30)\n"
                    "    db.commit()\n"
                    "\n"
                    "def purge_expired_users():\n"
                    "    expired = db.query(User).filter(\n"
                    "        User.deletion_scheduled_at <= datetime.utcnow()\n"
                    "    ).all()\n"
                    "    for u in expired:\n"
                    "        db.delete(u)\n"
                    "    db.commit()"
                ),
                points=15,
                regulation_article="GDPR Art. 5(1)(e) - Storage Limitation",
            ),
        ],
    ),
    SandboxScenario(
        id="hipaa-health-data-security",
        title="HIPAA Health Data Security",
        description=(
            "A patient records API with PHI handling violations. Fix encryption, "
            "access control, and audit logging issues to meet HIPAA requirements."
        ),
        regulation="HIPAA",
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_minutes=45,
        learning_objectives=[
            "Encrypt PHI at rest and in transit",
            "Implement role-based access controls for health data",
            "Add HIPAA-compliant audit logging",
        ],
        prerequisites=["Python experience", "Understanding of encryption basics"],
        tags=["hipaa", "healthcare", "encryption", "audit"],
        violations=[
            ViolationScenario(
                id="hipaa-v1-encryption",
                type=ViolationType.MISSING_ENCRYPTION,
                title="Patient records stored in plaintext",
                description="Medical diagnoses and treatment notes are stored without encryption.",
                file_path="models/patient.py",
                code_snippet=(
                    'class Patient(Base):\n'
                    '    __tablename__ = "patients"\n'
                    '    id = Column(Integer, primary_key=True)\n'
                    '    name = Column(String)\n'
                    '    diagnosis = Column(String)  # PHI stored in plaintext\n'
                    '    treatment_notes = Column(Text)  # PHI stored in plaintext'
                ),
                hint="Use column-level encryption (e.g., AES-256) for PHI fields.",
                solution_snippet=(
                    'class Patient(Base):\n'
                    '    __tablename__ = "patients"\n'
                    '    id = Column(Integer, primary_key=True)\n'
                    '    name = Column(String)\n'
                    '    diagnosis = Column(EncryptedString(key=PHI_KEY))\n'
                    '    treatment_notes = Column(EncryptedText(key=PHI_KEY))'
                ),
                points=20,
                regulation_article="HIPAA §164.312(a)(2)(iv) - Encryption",
            ),
            ViolationScenario(
                id="hipaa-v2-access-control",
                type=ViolationType.MISSING_ACCESS_CONTROL,
                title="No role-based access for patient records",
                description="Any authenticated user can view all patient records without role checks.",
                file_path="api/patients.py",
                code_snippet=(
                    '@app.get("/patients/{patient_id}")\n'
                    'def get_patient(patient_id: int, current_user: User):\n'
                    '    return db.query(Patient).get(patient_id)'
                ),
                hint="Check that the current user has the appropriate role (e.g., physician, nurse) for the requested patient.",
                solution_snippet=(
                    '@app.get("/patients/{patient_id}")\n'
                    'def get_patient(patient_id: int, current_user: User):\n'
                    '    if not has_patient_access(current_user, patient_id):\n'
                    '        raise HTTPException(403, "Insufficient access")\n'
                    '    log_access(current_user.id, patient_id)\n'
                    '    return db.query(Patient).get(patient_id)'
                ),
                points=20,
                regulation_article="HIPAA §164.312(a)(1) - Access Control",
            ),
            ViolationScenario(
                id="hipaa-v3-audit-log",
                type=ViolationType.MISSING_AUDIT_LOG,
                title="No audit trail for PHI access",
                description="Access to patient records is not logged for compliance auditing.",
                file_path="api/patients.py",
                code_snippet=(
                    '@app.get("/patients")\n'
                    'def list_patients(current_user: User):\n'
                    '    return db.query(Patient).all()'
                ),
                hint="Every access to PHI must be logged with who, what, when, and why.",
                solution_snippet=(
                    '@app.get("/patients")\n'
                    'def list_patients(current_user: User):\n'
                    '    patients = db.query(Patient).all()\n'
                    '    audit_log.record(\n'
                    '        user_id=current_user.id,\n'
                    '        action="list_patients",\n'
                    '        resource_count=len(patients),\n'
                    '        timestamp=datetime.utcnow(),\n'
                    '    )\n'
                    '    return patients'
                ),
                points=15,
                regulation_article="HIPAA §164.312(b) - Audit Controls",
            ),
        ],
    ),
    SandboxScenario(
        id="pci-dss-payment-security",
        title="PCI-DSS Payment Data Security",
        description=(
            "An e-commerce checkout service with payment card data handling "
            "violations. Fix tokenisation, authentication, and logging issues."
        ),
        regulation="PCI-DSS",
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_minutes=40,
        learning_objectives=[
            "Implement card data tokenisation",
            "Strengthen authentication for payment operations",
            "Secure cardholder data in logs and databases",
        ],
        prerequisites=["Web development experience", "Payment processing basics"],
        tags=["pci-dss", "payments", "tokenisation", "security"],
        violations=[
            ViolationScenario(
                id="pci-v1-unprotected-pan",
                type=ViolationType.UNPROTECTED_PII,
                title="Full card number stored in database",
                description="The payment table stores the full 16-digit PAN in a plaintext column.",
                file_path="models/payment.py",
                code_snippet=(
                    'class Payment(Base):\n'
                    '    __tablename__ = "payments"\n'
                    '    id = Column(Integer, primary_key=True)\n'
                    '    card_number = Column(String(16))  # full PAN\n'
                    '    amount = Column(Numeric)'
                ),
                hint="Replace full PAN storage with a tokenised reference from the payment processor.",
                solution_snippet=(
                    'class Payment(Base):\n'
                    '    __tablename__ = "payments"\n'
                    '    id = Column(Integer, primary_key=True)\n'
                    '    card_token = Column(String(64))  # tokenised reference\n'
                    '    card_last_four = Column(String(4))\n'
                    '    amount = Column(Numeric)'
                ),
                points=25,
                regulation_article="PCI-DSS Req. 3.4 - Render PAN Unreadable",
            ),
            ViolationScenario(
                id="pci-v2-weak-auth",
                type=ViolationType.WEAK_AUTH,
                title="No MFA for admin payment dashboard",
                description="The payment admin panel uses only password authentication.",
                file_path="api/admin.py",
                code_snippet=(
                    '@app.post("/admin/login")\n'
                    'def admin_login(username: str, password: str):\n'
                    '    user = authenticate(username, password)\n'
                    '    return create_session(user)'
                ),
                hint="PCI-DSS requires multi-factor authentication for administrative access.",
                solution_snippet=(
                    '@app.post("/admin/login")\n'
                    'def admin_login(username: str, password: str, mfa_code: str):\n'
                    '    user = authenticate(username, password)\n'
                    '    if not verify_mfa(user, mfa_code):\n'
                    '        raise HTTPException(401, "MFA verification failed")\n'
                    '    return create_session(user)'
                ),
                points=20,
                regulation_article="PCI-DSS Req. 8.3 - Multi-Factor Authentication",
            ),
        ],
    ),
    SandboxScenario(
        id="gdpr-breach-notification",
        title="GDPR Breach Notification & DPIA",
        description=(
            "A data-processing service that lacks proper breach notification "
            "procedures and Data Protection Impact Assessments. Implement the "
            "missing compliance controls."
        ),
        regulation="GDPR",
        difficulty=DifficultyLevel.ADVANCED,
        estimated_minutes=50,
        learning_objectives=[
            "Implement 72-hour breach notification workflow",
            "Create a Data Protection Impact Assessment process",
            "Set up automated breach detection and alerting",
        ],
        prerequisites=["Intermediate Python", "GDPR fundamentals", "Notification systems"],
        tags=["gdpr", "breach-notification", "dpia", "advanced"],
        violations=[
            ViolationScenario(
                id="gdpr-bn-v1",
                type=ViolationType.MISSING_BREACH_NOTIFICATION,
                title="No breach notification mechanism",
                description="When a data breach is detected there is no process to notify the supervisory authority within 72 hours.",
                file_path="services/security_service.py",
                code_snippet=(
                    'def handle_breach(breach_details):\n'
                    '    log.error("Data breach detected", details=breach_details)\n'
                    '    # TODO: notify authorities'
                ),
                hint="Implement an automated notification pipeline that alerts the DPO and submits to the supervisory authority within 72 hours.",
                solution_snippet=(
                    'def handle_breach(breach_details):\n'
                    '    log.error("Data breach detected", details=breach_details)\n'
                    '    breach_record = create_breach_record(breach_details)\n'
                    '    notify_dpo(breach_record)\n'
                    '    schedule_authority_notification(\n'
                    '        breach_record, deadline_hours=72\n'
                    '    )\n'
                    '    notify_affected_users(breach_record)'
                ),
                points=25,
                regulation_article="GDPR Art. 33 - Notification to Supervisory Authority",
            ),
            ViolationScenario(
                id="gdpr-bn-v2",
                type=ViolationType.MISSING_DPIA,
                title="No Data Protection Impact Assessment",
                description="High-risk data processing activities lack a DPIA prior to deployment.",
                file_path="services/analytics_service.py",
                code_snippet=(
                    "def deploy_profiling_model(model, user_dataset):\n"
                    "    predictions = model.predict(user_dataset)\n"
                    "    store_predictions(predictions)\n"
                    "    return predictions"
                ),
                hint="High-risk processing (profiling, large-scale monitoring) requires a DPIA before deployment.",
                solution_snippet=(
                    'def deploy_profiling_model(model, user_dataset):\n'
                    '    dpia = create_dpia(\n'
                    '        processing_type="automated_profiling",\n'
                    '        data_categories=["behavioral", "demographic"],\n'
                    '        risk_assessment=assess_risk(user_dataset),\n'
                    '    )\n'
                    '    if not dpia.approved:\n'
                    '        raise ComplianceError("DPIA approval required")\n'
                    '    predictions = model.predict(user_dataset)\n'
                    '    store_predictions(predictions)\n'
                    '    return predictions'
                ),
                points=20,
                regulation_article="GDPR Art. 35 - Data Protection Impact Assessment",
            ),
        ],
    ),
    SandboxScenario(
        id="hipaa-pci-combined",
        title="Multi-Regulation Health Payment System",
        description=(
            "A healthcare billing platform that handles both PHI and payment card "
            "data. Fix violations spanning HIPAA and PCI-DSS simultaneously."
        ),
        regulation="HIPAA,PCI-DSS",
        difficulty=DifficultyLevel.EXPERT,
        estimated_minutes=60,
        learning_objectives=[
            "Apply overlapping HIPAA and PCI-DSS controls",
            "Implement end-to-end encryption for PHI and cardholder data",
            "Design unified audit logging across regulations",
        ],
        prerequisites=["HIPAA fundamentals", "PCI-DSS basics", "Advanced Python"],
        tags=["hipaa", "pci-dss", "multi-regulation", "expert"],
        violations=[
            ViolationScenario(
                id="combo-v1-phi-payment",
                type=ViolationType.DATA_EXPOSURE,
                title="PHI and card data in same unprotected response",
                description="The billing API returns patient diagnosis alongside unmasked card numbers.",
                file_path="api/billing.py",
                code_snippet=(
                    '@app.get("/billing/{patient_id}")\n'
                    'def get_billing(patient_id):\n'
                    '    patient = db.query(Patient).get(patient_id)\n'
                    '    return {\n'
                    '        "diagnosis": patient.diagnosis,\n'
                    '        "card_number": patient.card_number,\n'
                    '        "amount_due": patient.balance,\n'
                    '    }'
                ),
                hint="Separate PHI from payment data and mask or tokenise both appropriately.",
                solution_snippet=(
                    '@app.get("/billing/{patient_id}")\n'
                    'def get_billing(patient_id, current_user: User):\n'
                    '    if not has_billing_access(current_user, patient_id):\n'
                    '        raise HTTPException(403, "Access denied")\n'
                    '    patient = db.query(Patient).get(patient_id)\n'
                    '    audit_log.record(current_user.id, "view_billing", patient_id)\n'
                    '    return {\n'
                    '        "diagnosis": "[REDACTED]",\n'
                    '        "card_last_four": patient.card_last_four,\n'
                    '        "amount_due": patient.balance,\n'
                    '    }'
                ),
                points=30,
                regulation_article="HIPAA §164.502 / PCI-DSS Req. 3.3",
            ),
            ViolationScenario(
                id="combo-v2-unified-audit",
                type=ViolationType.MISSING_AUDIT_LOG,
                title="No unified audit trail for PHI + payment access",
                description="Access events are not consistently logged across health and payment operations.",
                file_path="services/billing_service.py",
                code_snippet=(
                    "def process_payment(patient_id, amount):\n"
                    "    patient = get_patient(patient_id)\n"
                    "    charge_card(patient.card_token, amount)\n"
                    "    update_balance(patient_id, amount)"
                ),
                hint="Create a unified audit log that captures both PHI access and payment processing events.",
                solution_snippet=(
                    'def process_payment(patient_id, amount, current_user):\n'
                    '    patient = get_patient(patient_id)\n'
                    '    audit_log.record(\n'
                    '        user_id=current_user.id,\n'
                    '        actions=["phi_access", "payment_processing"],\n'
                    '        resource_id=patient_id,\n'
                    '        details={"amount": amount},\n'
                    '    )\n'
                    '    charge_card(patient.card_token, amount)\n'
                    '    update_balance(patient_id, amount)'
                ),
                points=25,
                regulation_article="HIPAA §164.312(b) / PCI-DSS Req. 10.1",
            ),
        ],
    ),
]

_SCENARIO_MAP: dict[str, SandboxScenario] = {s.id: s for s in _SCENARIOS}

# ---------------------------------------------------------------------------
# Available badges
# ---------------------------------------------------------------------------

_BADGES: list[SandboxBadge] = [
    SandboxBadge(id="first-fix", name="First Fix", description="Fixed your first compliance violation", icon="🔧", criteria="Complete 1 violation fix"),
    SandboxBadge(id="gdpr-guardian", name="GDPR Guardian", description="Completed a GDPR scenario with 100% score", icon="🛡️", criteria="Score 100% on any GDPR scenario"),
    SandboxBadge(id="hipaa-hero", name="HIPAA Hero", description="Completed a HIPAA scenario with 100% score", icon="🏥", criteria="Score 100% on any HIPAA scenario"),
    SandboxBadge(id="speed-runner", name="Speed Runner", description="Completed a scenario in under half the estimated time", icon="⚡", criteria="Finish before 50% of estimated time"),
    SandboxBadge(id="no-hints", name="No Hints Needed", description="Completed a scenario without using any hints", icon="🧠", criteria="Complete a scenario with 0 hints used"),
    SandboxBadge(id="multi-reg", name="Multi-Regulation Master", description="Completed the multi-regulation expert scenario", icon="🏆", criteria="Complete the hipaa-pci-combined scenario"),
]

_BADGE_MAP: dict[str, SandboxBadge] = {b.id: b for b in _BADGES}

# ---------------------------------------------------------------------------
# In-memory stores (production would use a database)
# ---------------------------------------------------------------------------

_sandboxes: dict[UUID, SandboxEnvironment] = {}
_results: dict[UUID, SandboxResult] = {}
_user_badges: dict[UUID, list[SandboxBadge]] = {}
_violation_fixes: dict[UUID, set[str]] = {}


class ComplianceSandboxService:
    """Manages ephemeral sandbox environments for compliance training."""

    def __init__(self, db):
        self.db = db

    # -- Scenarios -----------------------------------------------------------

    async def list_scenarios(
        self,
        difficulty: DifficultyLevel | None = None,
        regulation: str | None = None,
    ) -> list[SandboxScenario]:
        """List available sandbox scenarios with optional filters."""
        scenarios = list(_SCENARIOS)
        if difficulty is not None:
            scenarios = [s for s in scenarios if s.difficulty == difficulty]
        if regulation is not None:
            reg_lower = regulation.lower()
            scenarios = [s for s in scenarios if reg_lower in s.regulation.lower()]
        logger.info("scenarios_listed", count=len(scenarios), difficulty=difficulty, regulation=regulation)
        return scenarios

    async def get_scenario(self, scenario_id: str) -> SandboxScenario | None:
        """Get a specific scenario by ID."""
        return _SCENARIO_MAP.get(scenario_id)

    # -- Sandbox lifecycle ---------------------------------------------------

    async def create_sandbox(
        self,
        org_id: UUID,
        user_id: UUID,
        scenario_id: str,
    ) -> SandboxEnvironment:
        """Provision a new sandbox environment for a scenario."""
        scenario = _SCENARIO_MAP.get(scenario_id)
        if scenario is None:
            raise ValueError(f"Scenario not found: {scenario_id}")

        now = datetime.utcnow()
        resources = SandboxResources(max_duration_minutes=scenario.estimated_minutes + 30)
        sandbox = SandboxEnvironment(
            id=uuid4(),
            org_id=org_id,
            user_id=user_id,
            scenario_id=scenario_id,
            status=SandboxStatus.RUNNING,
            created_at=now,
            expires_at=now + timedelta(minutes=resources.max_duration_minutes),
            resources=resources,
            connection_info={"workspace_url": f"/sandbox/{scenario_id}/workspace", "terminal_url": f"/sandbox/{scenario_id}/terminal"},
            progress=SandboxProgress(total_violations=len(scenario.violations)),
        )

        _sandboxes[sandbox.id] = sandbox
        _violation_fixes[sandbox.id] = set()

        logger.info(
            "sandbox_created",
            sandbox_id=str(sandbox.id),
            scenario_id=scenario_id,
            user_id=str(user_id),
            expires_at=sandbox.expires_at.isoformat(),
        )
        return sandbox

    async def get_sandbox(self, sandbox_id: UUID) -> SandboxEnvironment | None:
        """Get sandbox environment status."""
        sandbox = _sandboxes.get(sandbox_id)
        if sandbox and sandbox.expires_at < datetime.utcnow() and sandbox.status == SandboxStatus.RUNNING:
            sandbox.status = SandboxStatus.EXPIRED
        return sandbox

    async def list_user_sandboxes(
        self,
        user_id: UUID,
        status: SandboxStatus | None = None,
    ) -> list[SandboxEnvironment]:
        """List sandbox environments belonging to a user."""
        sandboxes = [s for s in _sandboxes.values() if s.user_id == user_id]
        if status is not None:
            sandboxes = [s for s in sandboxes if s.status == status]
        return sorted(sandboxes, key=lambda s: s.created_at, reverse=True)

    async def terminate_sandbox(self, sandbox_id: UUID) -> bool:
        """Terminate a running sandbox environment."""
        sandbox = _sandboxes.get(sandbox_id)
        if sandbox is None:
            return False
        sandbox.status = SandboxStatus.COMPLETED
        logger.info("sandbox_terminated", sandbox_id=str(sandbox_id))
        return True

    # -- Violation checking --------------------------------------------------

    async def check_violation(
        self,
        sandbox_id: UUID,
        violation_id: str,
        submitted_code: str,
    ) -> dict[str, Any]:
        """Check whether a submitted code fix resolves a violation."""
        sandbox = _sandboxes.get(sandbox_id)
        if sandbox is None:
            raise ValueError("Sandbox not found")

        scenario = _SCENARIO_MAP.get(sandbox.scenario_id)
        if scenario is None:
            raise ValueError("Scenario not found")

        violation = next((v for v in scenario.violations if v.id == violation_id), None)
        if violation is None:
            raise ValueError(f"Violation not found: {violation_id}")

        # Simple heuristic: check that the submitted code is different from the
        # original snippet and contains key elements from the solution.
        solution_keywords = _extract_keywords(violation.solution_snippet)
        submitted_lower = submitted_code.lower()
        matches = sum(1 for kw in solution_keywords if kw in submitted_lower)
        match_ratio = matches / max(len(solution_keywords), 1)

        passed = match_ratio >= 0.5 and submitted_code.strip() != violation.code_snippet.strip()
        points_earned = violation.points if passed else 0

        if passed:
            fixes = _violation_fixes.setdefault(sandbox_id, set())
            fixes.add(violation_id)
            sandbox.progress.completed_violations = len(fixes)
            sandbox.progress.score += points_earned

        elapsed = (datetime.utcnow() - sandbox.created_at).total_seconds() / 60.0
        sandbox.progress.time_elapsed_minutes = round(elapsed, 1)

        logger.info(
            "violation_checked",
            sandbox_id=str(sandbox_id),
            violation_id=violation_id,
            passed=passed,
            match_ratio=round(match_ratio, 2),
        )

        return {
            "violation_id": violation_id,
            "passed": passed,
            "points_earned": points_earned,
            "feedback": f"✅ Correct! +{points_earned} points" if passed else "❌ Not quite. Review the regulation article and try again.",
            "regulation_article": violation.regulation_article,
        }

    async def submit_solution(self, sandbox_id: UUID) -> SandboxResult:
        """Submit the final solution and calculate results."""
        sandbox = _sandboxes.get(sandbox_id)
        if sandbox is None:
            raise ValueError("Sandbox not found")

        scenario = _SCENARIO_MAP.get(sandbox.scenario_id)
        if scenario is None:
            raise ValueError("Scenario not found")

        fixed = _violation_fixes.get(sandbox_id, set())
        all_ids = {v.id for v in scenario.violations}
        max_score = sum(v.points for v in scenario.violations)
        elapsed = (datetime.utcnow() - sandbox.created_at).total_seconds() / 60.0
        completion_pct = round(len(fixed) / max(len(all_ids), 1) * 100, 1)

        badge_earned = self._evaluate_badge(sandbox, scenario, fixed, elapsed)

        result = SandboxResult(
            id=uuid4(),
            sandbox_id=sandbox_id,
            scenario_id=sandbox.scenario_id,
            score=sandbox.progress.score,
            max_score=max_score,
            completion_pct=completion_pct,
            time_minutes=round(elapsed, 1),
            violations_fixed=sorted(fixed),
            violations_missed=sorted(all_ids - fixed),
            feedback=self._generate_feedback(completion_pct, elapsed, scenario.estimated_minutes),
            badge_earned=badge_earned,
        )

        sandbox.status = SandboxStatus.COMPLETED
        sandbox.progress.completed_at = datetime.utcnow()
        _results[result.id] = result

        logger.info(
            "sandbox_submitted",
            sandbox_id=str(sandbox_id),
            score=result.score,
            max_score=result.max_score,
            completion_pct=result.completion_pct,
            badge_earned=badge_earned,
        )
        return result

    async def get_hint(self, sandbox_id: UUID, violation_id: str) -> str:
        """Get a hint for a specific violation."""
        sandbox = _sandboxes.get(sandbox_id)
        if sandbox is None:
            raise ValueError("Sandbox not found")

        scenario = _SCENARIO_MAP.get(sandbox.scenario_id)
        if scenario is None:
            raise ValueError("Scenario not found")

        violation = next((v for v in scenario.violations if v.id == violation_id), None)
        if violation is None:
            raise ValueError(f"Violation not found: {violation_id}")

        sandbox.progress.hints_used += 1
        logger.info(
            "hint_requested",
            sandbox_id=str(sandbox_id),
            violation_id=violation_id,
            total_hints=sandbox.progress.hints_used,
        )
        return violation.hint

    # -- Gamification --------------------------------------------------------

    async def cleanup_expired(self) -> int:
        """Clean up expired sandbox environments."""
        now = datetime.utcnow()
        expired_ids = [
            sid for sid, s in _sandboxes.items()
            if s.expires_at < now and s.status == SandboxStatus.RUNNING
        ]
        for sid in expired_ids:
            _sandboxes[sid].status = SandboxStatus.EXPIRED
        logger.info("expired_sandboxes_cleaned", count=len(expired_ids))
        return len(expired_ids)

    async def get_user_badges(self, user_id: UUID) -> list[SandboxBadge]:
        """Get badges earned by a user."""
        return _user_badges.get(user_id, [])

    async def get_leaderboard(self, limit: int = 20) -> list[dict]:
        """Get the sandbox leaderboard."""
        user_scores: dict[str, dict[str, Any]] = {}
        for result in _results.values():
            sandbox = _sandboxes.get(result.sandbox_id)
            if sandbox is None:
                continue
            uid = str(sandbox.user_id)
            if uid not in user_scores:
                user_scores[uid] = {"user_id": uid, "total_score": 0, "scenarios_completed": 0, "badges_count": 0}
            user_scores[uid]["total_score"] += result.score
            user_scores[uid]["scenarios_completed"] += 1
            user_scores[uid]["badges_count"] = len(_user_badges.get(sandbox.user_id, []))

        leaderboard = sorted(user_scores.values(), key=lambda x: x["total_score"], reverse=True)
        return leaderboard[:limit]

    # -- What-If Simulation --------------------------------------------------

    async def list_whatif_scenarios(self) -> list[WhatIfScenario]:
        """List available what-if regulatory change scenarios."""
        return [
            WhatIfScenario(
                id="whatif-us-federal-privacy", title="US Federal Privacy Act Passes",
                description="Simulate impact of a comprehensive US federal privacy law replacing state patchwork.",
                change_type="new_regulation", jurisdiction="US Federal", regulation="ADPPA",
                effective_date="2027-01-01", probability=0.65,
            ),
            WhatIfScenario(
                id="whatif-eu-ai-enforcement", title="EU AI Act Strict Enforcement",
                description="Simulate impact of aggressive EU AI Act enforcement with high-risk classification.",
                change_type="enforcement", jurisdiction="EU", regulation="EU AI Act",
                effective_date="2026-08-01", probability=0.85,
            ),
            WhatIfScenario(
                id="whatif-gdpr-amendment", title="GDPR Amendment: AI-Specific Rules",
                description="Simulate GDPR amendment adding specific requirements for AI-driven personal data processing.",
                change_type="amendment", jurisdiction="EU", regulation="GDPR",
                effective_date="2027-06-01", probability=0.45,
            ),
            WhatIfScenario(
                id="whatif-ccpa-expansion", title="CCPA Biometric Data Expansion",
                description="Simulate CCPA expanding to cover biometric data with strict consent requirements.",
                change_type="amendment", jurisdiction="California", regulation="CCPA/CPRA",
                effective_date="2026-07-01", probability=0.70,
            ),
        ]

    async def run_whatif_simulation(
        self, scenario_id: str, repo: str = "",
    ) -> WhatIfImpact:
        """Run a what-if simulation and return impact assessment."""
        scenarios = await self.list_whatif_scenarios()
        scenario = next((s for s in scenarios if s.id == scenario_id), None)
        if not scenario:
            raise ValueError(f"What-if scenario not found: {scenario_id}")

        # Simulate impact analysis
        impact_data = {
            "whatif-us-federal-privacy": {
                "risk": 8.5, "hours": 320, "cost": 48000, "gaps": 12,
                "modules": [
                    {"name": "auth/consent", "impact": "high", "changes_required": 8},
                    {"name": "data/storage", "impact": "high", "changes_required": 6},
                    {"name": "api/privacy", "impact": "medium", "changes_required": 4},
                    {"name": "reporting/compliance", "impact": "low", "changes_required": 2},
                ],
                "recs": [
                    "Implement unified consent management across all data processing",
                    "Add data minimization enforcement at API layer",
                    "Create federal privacy notice templates",
                ],
            },
            "whatif-eu-ai-enforcement": {
                "risk": 9.0, "hours": 480, "cost": 72000, "gaps": 18,
                "modules": [
                    {"name": "ai/models", "impact": "critical", "changes_required": 12},
                    {"name": "ai/training", "impact": "high", "changes_required": 8},
                    {"name": "docs/model-cards", "impact": "high", "changes_required": 6},
                    {"name": "monitoring/ai", "impact": "medium", "changes_required": 4},
                ],
                "recs": [
                    "Complete AI system risk classification inventory",
                    "Implement model cards for all high-risk AI systems",
                    "Add human oversight mechanisms to automated decisions",
                ],
            },
        }

        defaults = {
            "risk": 6.0, "hours": 160, "cost": 24000, "gaps": 8,
            "modules": [
                {"name": "core/compliance", "impact": "medium", "changes_required": 4},
                {"name": "api/endpoints", "impact": "medium", "changes_required": 3},
            ],
            "recs": ["Review current compliance posture", "Engage legal counsel for interpretation"],
        }

        data = impact_data.get(scenario_id, defaults)

        # Generate heatmap data
        heatmap = [
            {"area": m["name"], "current_risk": 3.0, "projected_risk": m["changes_required"] * 1.2,
             "delta": m["changes_required"] * 1.2 - 3.0}
            for m in data["modules"]
        ]

        return WhatIfImpact(
            scenario_id=scenario_id,
            overall_risk_score=data["risk"],
            affected_modules=data["modules"],
            estimated_effort_hours=data["hours"],
            estimated_cost_usd=data["cost"],
            compliance_gap_count=data["gaps"],
            recommendations=data["recs"],
            heatmap=heatmap,
        )

    # -- Private helpers -----------------------------------------------------

    def _evaluate_badge(
        self,
        sandbox: SandboxEnvironment,
        scenario: SandboxScenario,
        fixed: set[str],
        elapsed_minutes: float,
    ) -> str | None:
        """Evaluate whether a badge should be awarded and store it."""
        all_ids = {v.id for v in scenario.violations}
        user_id = sandbox.user_id
        user_badge_list = _user_badges.setdefault(user_id, [])
        earned_ids = {b.id for b in user_badge_list}

        badge_id: str | None = None

        # First Fix
        if "first-fix" not in earned_ids and len(fixed) >= 1:
            badge_id = "first-fix"

        # Perfect score on GDPR
        if "gdpr-guardian" not in earned_ids and "gdpr" in scenario.regulation.lower() and fixed == all_ids:
            badge_id = "gdpr-guardian"

        # Perfect score on HIPAA
        if "hipaa-hero" not in earned_ids and "hipaa" in scenario.regulation.lower() and fixed == all_ids:
            badge_id = "hipaa-hero"

        # Speed runner
        if "speed-runner" not in earned_ids and elapsed_minutes < scenario.estimated_minutes * 0.5:
            badge_id = "speed-runner"

        # No hints
        if "no-hints" not in earned_ids and sandbox.progress.hints_used == 0 and fixed == all_ids:
            badge_id = "no-hints"

        # Multi-reg master
        if "multi-reg" not in earned_ids and scenario.id == "hipaa-pci-combined" and fixed == all_ids:
            badge_id = "multi-reg"

        if badge_id and badge_id in _BADGE_MAP:
            badge = SandboxBadge(
                id=_BADGE_MAP[badge_id].id,
                name=_BADGE_MAP[badge_id].name,
                description=_BADGE_MAP[badge_id].description,
                icon=_BADGE_MAP[badge_id].icon,
                criteria=_BADGE_MAP[badge_id].criteria,
                earned_at=datetime.utcnow(),
            )
            user_badge_list.append(badge)

        return badge_id

    @staticmethod
    def _generate_feedback(completion_pct: float, elapsed: float, estimated: int) -> str:
        """Generate human-readable feedback based on results."""
        if completion_pct == 100:
            if elapsed < estimated * 0.5:
                return "🏆 Outstanding! You fixed all violations in record time!"
            return "🎉 Excellent work! You identified and fixed every violation."
        if completion_pct >= 75:
            return "👏 Great job! You caught most of the violations. Review the missed ones to strengthen your knowledge."
        if completion_pct >= 50:
            return "👍 Good progress! You're on the right track. Try revisiting the hints for the remaining violations."
        return "📚 Keep learning! Review the regulation articles and try again to improve your score."


def _extract_keywords(solution: str) -> list[str]:
    """Extract meaningful keywords from a solution snippet for matching."""
    noise = {"def", "return", "self", "the", "and", "for", "not", "if", "else", "in", "is", "a", "to", "of"}
    words: list[str] = []
    for token in solution.lower().replace("(", " ").replace(")", " ").replace(",", " ").replace(":", " ").split():
        cleaned = token.strip("\"' ")
        if len(cleaned) > 2 and cleaned not in noise and not cleaned.startswith("#"):
            words.append(cleaned)
    # De-duplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for w in words:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique
