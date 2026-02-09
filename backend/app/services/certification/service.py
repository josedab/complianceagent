"""AI Compliance Training Certification Program service."""

import hashlib
import secrets
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.certification.models import (
    Certificate,
    CertificateStatus,
    Course,
    CourseLevel,
    CourseProgress,
    Enrollment,
    LearningPath,
    Module,
    ModuleType,
    Question,
    QuestionType,
    TutorConversation,
)


logger = structlog.get_logger()


class CertificationService:
    """Service for AI compliance training certification program."""

    def __init__(self, db: AsyncSession, copilot_client: Any = None):
        self.db = db
        self.copilot_client = copilot_client
        self._courses: dict[UUID, Course] = {}
        self._enrollments: dict[str, Enrollment] = {}
        self._certificates: dict[UUID, Certificate] = {}
        self._tutor_conversations: list[TutorConversation] = []
        self._initialize_courses()

    # --- Public API ---

    async def list_courses(
        self,
        level: CourseLevel | None = None,
        regulation: str | None = None,
    ) -> list[Course]:
        """List available certification courses."""
        courses = list(self._courses.values())

        if level:
            courses = [c for c in courses if c.level == level]
        if regulation:
            courses = [c for c in courses if c.regulation == regulation]

        return courses

    async def get_course(self, course_id: UUID) -> Course | None:
        """Get a course by ID."""
        return self._courses.get(course_id)

    async def enroll(self, user_id: UUID, course_id: UUID) -> Enrollment:
        """Enroll a user in a course."""
        course = self._courses.get(course_id)
        if not course:
            raise ValueError("Course not found")

        key = f"{user_id}:{course_id}"
        if key in self._enrollments:
            return self._enrollments[key]

        first_module = course.modules[0].title if course.modules else ""
        enrollment = Enrollment(
            user_id=user_id,
            course_id=course_id,
            current_module=first_module,
        )
        self._enrollments[key] = enrollment
        course.enrolled_count += 1

        logger.info("user_enrolled", user_id=str(user_id), course_id=str(course_id))
        return enrollment

    async def get_enrollment(self, user_id: UUID, course_id: UUID) -> Enrollment | None:
        """Get a user's enrollment in a course."""
        return self._enrollments.get(f"{user_id}:{course_id}")

    async def complete_module(
        self,
        user_id: UUID,
        course_id: UUID,
        module_id: UUID,
        answers: dict,
    ) -> dict:
        """Complete a module and record results."""
        key = f"{user_id}:{course_id}"
        enrollment = self._enrollments.get(key)
        if not enrollment:
            raise ValueError("Not enrolled in this course")

        course = self._courses.get(course_id)
        if not course:
            raise ValueError("Course not found")

        module = next((m for m in course.modules if m.id == module_id), None)
        if not module:
            raise ValueError("Module not found")

        module_id_str = str(module_id)
        if module_id_str not in enrollment.completed_modules:
            enrollment.completed_modules.append(module_id_str)

        enrollment.progress_pct = (
            len(enrollment.completed_modules) / len(course.modules) * 100
        )

        # Advance to next module
        current_order = module.order
        next_module = next(
            (m for m in course.modules if m.order == current_order + 1), None
        )
        if next_module:
            enrollment.current_module = next_module.title

        return {
            "module_id": module_id_str,
            "completed": True,
            "progress_pct": enrollment.progress_pct,
            "next_module": next_module.title if next_module else None,
        }

    async def submit_quiz(
        self,
        user_id: UUID,
        course_id: UUID,
        module_id: UUID,
        answers: list[dict],
    ) -> dict:
        """Submit quiz answers and calculate score."""
        key = f"{user_id}:{course_id}"
        enrollment = self._enrollments.get(key)
        if not enrollment:
            raise ValueError("Not enrolled in this course")

        course = self._courses.get(course_id)
        if not course:
            raise ValueError("Course not found")

        module = next((m for m in course.modules if m.id == module_id), None)
        if not module:
            raise ValueError("Module not found")

        total_points = sum(q.points for q in module.questions) or 1
        earned_points = 0
        results = []

        for answer in answers:
            question = next(
                (q for q in module.questions if str(q.id) == answer.get("question_id")),
                None,
            )
            if not question:
                continue

            is_correct = answer.get("answer") == question.correct_answer
            if is_correct:
                earned_points += question.points

            results.append({
                "question_id": str(question.id),
                "correct": is_correct,
                "explanation": question.explanation,
            })

        score = (earned_points / total_points) * 100
        passed = score >= module.passing_score
        enrollment.quiz_scores[str(module_id)] = score

        if passed and str(module_id) not in enrollment.completed_modules:
            enrollment.completed_modules.append(str(module_id))
            enrollment.progress_pct = (
                len(enrollment.completed_modules) / len(course.modules) * 100
            )

        logger.info(
            "quiz_submitted",
            user_id=str(user_id),
            module_id=str(module_id),
            score=score,
            passed=passed,
        )

        return {
            "score": score,
            "passed": passed,
            "total_points": total_points,
            "earned_points": earned_points,
            "results": results,
        }

    async def ask_tutor(
        self,
        user_id: UUID,
        course_id: UUID,
        module_id: UUID,
        question: str,
    ) -> TutorConversation:
        """Ask the AI tutor a question about course material."""
        course = self._courses.get(course_id)
        if not course:
            raise ValueError("Course not found")

        module = next((m for m in course.modules if m.id == module_id), None)
        context = f"Course: {course.title}"
        if module:
            context += f" | Module: {module.title} | Content: {module.content[:200]}"

        # Generate AI response
        answer = await self._generate_tutor_response(question, context)

        conversation = TutorConversation(
            user_id=user_id,
            course_id=course_id,
            module_id=module_id,
            question=question,
            answer=answer,
            context=context,
        )
        self._tutor_conversations.append(conversation)

        logger.info("tutor_asked", user_id=str(user_id), course=course.title)
        return conversation

    async def take_final_exam(
        self,
        user_id: UUID,
        course_id: UUID,
        answers: list[dict],
    ) -> dict:
        """Take the final certification exam."""
        key = f"{user_id}:{course_id}"
        enrollment = self._enrollments.get(key)
        if not enrollment:
            raise ValueError("Not enrolled in this course")

        course = self._courses.get(course_id)
        if not course:
            raise ValueError("Course not found")

        # Collect all assessment questions
        exam_questions: list[Question] = []
        for module in course.modules:
            if module.type == ModuleType.ASSESSMENT:
                exam_questions.extend(module.questions)

        if not exam_questions:
            # Fall back to all quiz questions
            for module in course.modules:
                if module.type == ModuleType.QUIZ:
                    exam_questions.extend(module.questions)

        total_points = sum(q.points for q in exam_questions) or 1
        earned_points = 0
        results = []

        for answer in answers:
            question = next(
                (q for q in exam_questions if str(q.id) == answer.get("question_id")),
                None,
            )
            if not question:
                continue

            is_correct = answer.get("answer") == question.correct_answer
            if is_correct:
                earned_points += question.points

            results.append({
                "question_id": str(question.id),
                "correct": is_correct,
                "explanation": question.explanation,
            })

        score = (earned_points / total_points) * 100
        passed = score >= 75.0

        enrollment.status = CertificateStatus.PASSED if passed else CertificateStatus.FAILED

        cert = None
        if passed:
            cert = await self.issue_certificate(user_id, course_id, score=score)

        logger.info(
            "final_exam_taken",
            user_id=str(user_id),
            course=course.title,
            score=score,
            passed=passed,
        )

        return {
            "score": score,
            "passed": passed,
            "total_points": total_points,
            "earned_points": earned_points,
            "results": results,
            "certificate": {
                "certificate_number": cert.certificate_number,
                "verification_url": cert.verification_url,
            } if cert else None,
        }

    async def issue_certificate(
        self,
        user_id: UUID,
        course_id: UUID,
        score: float = 0.0,
    ) -> Certificate:
        """Issue a professional certificate."""
        course = self._courses.get(course_id)
        title = course.title if course else "Unknown"

        cert_number = f"CERT-{secrets.token_hex(4).upper()}-{datetime.utcnow().strftime('%Y')}"
        credential_id = hashlib.sha256(
            f"{user_id}:{course_id}:{cert_number}".encode()
        ).hexdigest()[:16]

        certificate = Certificate(
            user_id=user_id,
            course_id=course_id,
            certificate_number=cert_number,
            score=score,
            verification_url=f"/api/v1/certification/certificates/verify/{cert_number}",
            credential_id=credential_id,
        )
        self._certificates[certificate.id] = certificate

        logger.info(
            "certificate_issued",
            user_id=str(user_id),
            course=title,
            certificate_number=cert_number,
        )
        return certificate

    async def verify_certificate(self, certificate_number: str) -> Certificate | None:
        """Verify a certificate by its number."""
        for cert in self._certificates.values():
            if cert.certificate_number == certificate_number:
                if cert.expires_at < datetime.utcnow():
                    cert.status = CertificateStatus.EXPIRED
                return cert
        return None

    async def get_user_certificates(self, user_id: UUID) -> list[Certificate]:
        """Get all certificates for a user."""
        return [
            c for c in self._certificates.values()
            if c.user_id == user_id
        ]

    async def get_learning_paths(self) -> list[LearningPath]:
        """Get curated learning paths."""
        course_ids = list(self._courses.keys())
        return [
            LearningPath(
                title="Privacy Engineering Track",
                description="Master GDPR and data privacy compliance for software engineers.",
                courses=[str(course_ids[0])] if len(course_ids) > 0 else [],
                estimated_hours=20.0,
                target_role="Privacy Engineer",
            ),
            LearningPath(
                title="AI Governance Specialist",
                description="Become an expert in AI regulation and responsible AI development.",
                courses=[str(course_ids[1])] if len(course_ids) > 1 else [],
                estimated_hours=18.0,
                target_role="AI Governance Lead",
            ),
            LearningPath(
                title="Healthcare Compliance Developer",
                description="Build HIPAA-compliant healthcare applications with confidence.",
                courses=[str(course_ids[2])] if len(course_ids) > 2 else [],
                estimated_hours=16.0,
                target_role="Healthcare Software Engineer",
            ),
            LearningPath(
                title="Full-Stack Compliance Engineer",
                description="Comprehensive compliance training covering all major frameworks.",
                courses=[str(cid) for cid in course_ids],
                estimated_hours=50.0,
                target_role="Compliance Engineer",
            ),
        ]

    async def get_progress(self, user_id: UUID, course_id: UUID) -> CourseProgress:
        """Get detailed progress for a user in a course."""
        key = f"{user_id}:{course_id}"
        enrollment = self._enrollments.get(key)
        course = self._courses.get(course_id)

        if not enrollment or not course:
            return CourseProgress(
                user_id=user_id,
                course_id=course_id,
                total_modules=len(course.modules) if course else 0,
            )

        scores = list(enrollment.quiz_scores.values())
        avg_score = sum(scores) / len(scores) if scores else 0.0

        return CourseProgress(
            user_id=user_id,
            course_id=course_id,
            modules_completed=len(enrollment.completed_modules),
            total_modules=len(course.modules),
            avg_quiz_score=avg_score,
            time_spent_minutes=len(enrollment.completed_modules) * 30,
            last_activity=enrollment.started_at,
        )

    async def list_enrollments(self, user_id: UUID) -> list[Enrollment]:
        """List all enrollments for a user."""
        return [
            e for e in self._enrollments.values()
            if e.user_id == user_id
        ]

    # --- Private Helpers ---

    async def _generate_tutor_response(self, question: str, context: str) -> str:
        """Generate an AI tutor response."""
        if self.copilot_client:
            try:
                prompt = (
                    f"You are an expert compliance tutor. Answer the following question "
                    f"based on the course context.\n\nContext: {context}\n\n"
                    f"Question: {question}\n\nProvide a clear, educational answer."
                )
                response = await self.copilot_client.chat(prompt)
                if response:
                    return response
            except Exception:
                logger.warning("tutor_ai_fallback", question=question)

        return (
            f"Great question! Regarding '{question}': This topic is covered in detail "
            f"in the course materials. Key points to remember: 1) Always refer to the "
            f"official regulation text for authoritative guidance. 2) Implementation "
            f"requirements vary by context and jurisdiction. 3) Consult with your "
            f"organization's compliance team for specific interpretations."
        )

    def _initialize_courses(self):
        """Initialize built-in certification courses."""
        gdpr_id = uuid4()
        ai_act_id = uuid4()
        hipaa_id = uuid4()
        soc2_id = uuid4()

        self._courses[gdpr_id] = self._create_gdpr_course(gdpr_id)
        self._courses[ai_act_id] = self._create_ai_act_course(ai_act_id)
        self._courses[hipaa_id] = self._create_hipaa_course(hipaa_id)
        self._courses[soc2_id] = self._create_soc2_course(soc2_id)

    def _create_gdpr_course(self, course_id: UUID) -> Course:
        """Create GDPR for Developers certification course."""
        modules = []
        for i, (title, mtype) in enumerate([
            ("Introduction to GDPR Principles", ModuleType.LESSON),
            ("Data Subject Rights Implementation", ModuleType.LESSON),
            ("Lawful Basis for Processing", ModuleType.QUIZ),
            ("Privacy by Design Patterns", ModuleType.LAB),
            ("Data Protection Impact Assessments", ModuleType.LESSON),
            ("Cross-Border Data Transfers", ModuleType.QUIZ),
            ("Breach Notification Implementation", ModuleType.LAB),
            ("GDPR Certification Exam", ModuleType.ASSESSMENT),
        ]):
            mod = Module(
                course_id=course_id,
                title=title,
                type=mtype,
                content=f"Comprehensive content for {title}.",
                order=i,
                duration_minutes=45 if mtype == ModuleType.LAB else 30,
            )
            if mtype in (ModuleType.QUIZ, ModuleType.ASSESSMENT):
                mod.questions = [
                    Question(
                        module_id=mod.id,
                        type=QuestionType.MULTIPLE_CHOICE,
                        question_text="What is the maximum GDPR fine for serious infringements?",
                        options=["€10 million", "€20 million or 4% of global turnover", "€50 million", "€5 million"],
                        correct_answer="€20 million or 4% of global turnover",
                        explanation="Article 83(5) GDPR specifies fines up to €20M or 4% of total worldwide annual turnover.",
                        points=10,
                    ),
                    Question(
                        module_id=mod.id,
                        type=QuestionType.TRUE_FALSE,
                        question_text="A Data Protection Officer (DPO) is mandatory for all organizations under GDPR.",
                        options=["True", "False"],
                        correct_answer="False",
                        explanation="A DPO is only mandatory under Article 37 for public authorities or organizations performing large-scale systematic monitoring.",
                        points=10,
                    ),
                    Question(
                        module_id=mod.id,
                        type=QuestionType.CODE_REVIEW,
                        question_text="Which code pattern correctly implements the right to erasure?",
                        options=[
                            "DELETE FROM users WHERE id = ?",
                            "UPDATE users SET deleted = true WHERE id = ?",
                            "Anonymize PII fields and retain for audit, then cascade delete from all subsystems",
                            "Remove user from active directory only",
                        ],
                        correct_answer="Anonymize PII fields and retain for audit, then cascade delete from all subsystems",
                        explanation="Right to erasure requires comprehensive removal across all systems while maintaining audit trails through anonymization.",
                        code_snippet="async def handle_erasure_request(user_id: str):\n    # Which approach is GDPR-compliant?",
                        points=15,
                    ),
                ]
            modules.append(mod)

        return Course(
            id=course_id,
            title="GDPR for Developers",
            description="Master GDPR compliance in software development, from data subject rights to privacy-by-design patterns.",
            regulation="GDPR",
            level=CourseLevel.INTERMEDIATE,
            modules=modules,
            estimated_hours=20.0,
            prerequisites=["Basic software development knowledge"],
            learning_objectives=[
                "Implement data subject rights (access, erasure, portability)",
                "Apply privacy-by-design patterns in code",
                "Conduct Data Protection Impact Assessments",
                "Handle cross-border data transfers correctly",
            ],
            is_free=True,
            enrolled_count=1247,
            completion_rate=78.5,
            rating=4.7,
        )

    def _create_ai_act_course(self, course_id: UUID) -> Course:
        """Create EU AI Act Implementation certification course."""
        modules = []
        for i, (title, mtype) in enumerate([
            ("EU AI Act Overview & Risk Classification", ModuleType.LESSON),
            ("High-Risk AI System Requirements", ModuleType.LESSON),
            ("AI Risk Classification Quiz", ModuleType.QUIZ),
            ("Transparency & Documentation Lab", ModuleType.LAB),
            ("Conformity Assessment Procedures", ModuleType.LESSON),
            ("AI Act Certification Exam", ModuleType.ASSESSMENT),
        ]):
            mod = Module(
                course_id=course_id,
                title=title,
                type=mtype,
                content=f"Comprehensive content for {title}.",
                order=i,
                duration_minutes=40 if mtype == ModuleType.LAB else 35,
            )
            if mtype in (ModuleType.QUIZ, ModuleType.ASSESSMENT):
                mod.questions = [
                    Question(
                        module_id=mod.id,
                        type=QuestionType.MULTIPLE_CHOICE,
                        question_text="Which AI systems are classified as 'unacceptable risk' under the EU AI Act?",
                        options=[
                            "Medical diagnostic AI",
                            "Social scoring systems by governments",
                            "Customer service chatbots",
                            "Content recommendation engines",
                        ],
                        correct_answer="Social scoring systems by governments",
                        explanation="Article 5 prohibits AI systems for social scoring by public authorities as unacceptable risk.",
                        points=10,
                    ),
                    Question(
                        module_id=mod.id,
                        type=QuestionType.MULTIPLE_CHOICE,
                        question_text="What documentation is required for high-risk AI systems?",
                        options=[
                            "Source code only",
                            "Technical documentation including training data, architecture, and performance metrics",
                            "User manual only",
                            "Marketing materials",
                        ],
                        correct_answer="Technical documentation including training data, architecture, and performance metrics",
                        explanation="Annex IV requires comprehensive technical documentation covering the full AI lifecycle.",
                        points=10,
                    ),
                    Question(
                        module_id=mod.id,
                        type=QuestionType.FILL_IN,
                        question_text="High-risk AI systems must maintain logs for a minimum of ___ months.",
                        options=[],
                        correct_answer="6",
                        explanation="Article 12 requires automatic logging of events for at least 6 months.",
                        points=10,
                    ),
                ]
            modules.append(mod)

        return Course(
            id=course_id,
            title="EU AI Act Implementation",
            description="Understand and implement the EU AI Act requirements for AI system development and deployment.",
            regulation="EU AI Act",
            level=CourseLevel.ADVANCED,
            modules=modules,
            estimated_hours=18.0,
            prerequisites=["Basic AI/ML knowledge", "Understanding of EU regulatory framework"],
            learning_objectives=[
                "Classify AI systems by risk level per the EU AI Act",
                "Implement mandatory requirements for high-risk AI systems",
                "Prepare conformity assessment documentation",
                "Build transparent and explainable AI systems",
            ],
            is_free=True,
            enrolled_count=892,
            completion_rate=72.3,
            rating=4.8,
        )

    def _create_hipaa_course(self, course_id: UUID) -> Course:
        """Create HIPAA Security Rules certification course."""
        modules = []
        for i, (title, mtype) in enumerate([
            ("HIPAA Fundamentals & PHI Identification", ModuleType.LESSON),
            ("Administrative Safeguards", ModuleType.LESSON),
            ("Technical Safeguards Quiz", ModuleType.QUIZ),
            ("Encryption & Access Control Lab", ModuleType.LAB),
            ("Audit Controls & Integrity", ModuleType.LESSON),
            ("HIPAA Security Certification Exam", ModuleType.ASSESSMENT),
        ]):
            mod = Module(
                course_id=course_id,
                title=title,
                type=mtype,
                content=f"Comprehensive content for {title}.",
                order=i,
                duration_minutes=40 if mtype == ModuleType.LAB else 30,
            )
            if mtype in (ModuleType.QUIZ, ModuleType.ASSESSMENT):
                mod.questions = [
                    Question(
                        module_id=mod.id,
                        type=QuestionType.MULTIPLE_CHOICE,
                        question_text="Which encryption standard does HIPAA recommend for data at rest?",
                        options=["MD5", "AES-256", "SHA-1", "ROT13"],
                        correct_answer="AES-256",
                        explanation="NIST SP 800-111 recommends AES-256 for encryption of ePHI at rest.",
                        points=10,
                    ),
                    Question(
                        module_id=mod.id,
                        type=QuestionType.TRUE_FALSE,
                        question_text="HIPAA requires all covered entities to encrypt ePHI in transit.",
                        options=["True", "False"],
                        correct_answer="True",
                        explanation="The Security Rule requires transmission security safeguards including encryption for ePHI in transit.",
                        points=10,
                    ),
                    Question(
                        module_id=mod.id,
                        type=QuestionType.CODE_REVIEW,
                        question_text="Which logging implementation meets HIPAA audit control requirements?",
                        options=[
                            "console.log('User accessed record')",
                            "Log user ID, timestamp, action, resource, and outcome to immutable audit trail",
                            "Write to local file only",
                            "Log only failed access attempts",
                        ],
                        correct_answer="Log user ID, timestamp, action, resource, and outcome to immutable audit trail",
                        explanation="HIPAA §164.312(b) requires comprehensive audit controls recording who, what, when, and outcome.",
                        code_snippet="def log_phi_access(user, record_id, action):\n    # Which implementation is HIPAA-compliant?",
                        points=15,
                    ),
                ]
            modules.append(mod)

        return Course(
            id=course_id,
            title="HIPAA Security Rules",
            description="Build HIPAA-compliant healthcare applications with proper security safeguards.",
            regulation="HIPAA",
            level=CourseLevel.INTERMEDIATE,
            modules=modules,
            estimated_hours=16.0,
            prerequisites=["Basic security knowledge"],
            learning_objectives=[
                "Identify and protect Protected Health Information (PHI)",
                "Implement administrative, physical, and technical safeguards",
                "Build HIPAA-compliant audit controls",
                "Handle breach notification requirements",
            ],
            is_free=True,
            enrolled_count=1054,
            completion_rate=81.2,
            rating=4.6,
        )

    def _create_soc2_course(self, course_id: UUID) -> Course:
        """Create SOC 2 Compliance Engineering certification course."""
        modules = []
        for i, (title, mtype) in enumerate([
            ("SOC 2 Trust Service Criteria Overview", ModuleType.LESSON),
            ("Security & Availability Controls", ModuleType.LESSON),
            ("Trust Criteria Quiz", ModuleType.QUIZ),
            ("Continuous Monitoring Lab", ModuleType.LAB),
            ("Evidence Collection & Audit Preparation", ModuleType.LESSON),
            ("SOC 2 Certification Exam", ModuleType.ASSESSMENT),
        ]):
            mod = Module(
                course_id=course_id,
                title=title,
                type=mtype,
                content=f"Comprehensive content for {title}.",
                order=i,
                duration_minutes=45 if mtype == ModuleType.LAB else 35,
            )
            if mtype in (ModuleType.QUIZ, ModuleType.ASSESSMENT):
                mod.questions = [
                    Question(
                        module_id=mod.id,
                        type=QuestionType.MULTIPLE_CHOICE,
                        question_text="Which are the five Trust Service Criteria in SOC 2?",
                        options=[
                            "Security, Availability, Processing Integrity, Confidentiality, Privacy",
                            "Security, Backup, Encryption, Access, Monitoring",
                            "Authentication, Authorization, Audit, Access, Accounting",
                            "Confidentiality, Integrity, Availability, Authentication, Non-repudiation",
                        ],
                        correct_answer="Security, Availability, Processing Integrity, Confidentiality, Privacy",
                        explanation="The AICPA defines these five Trust Service Criteria for SOC 2 reporting.",
                        points=10,
                    ),
                    Question(
                        module_id=mod.id,
                        type=QuestionType.TRUE_FALSE,
                        question_text="SOC 2 Type II reports assess controls at a point in time only.",
                        options=["True", "False"],
                        correct_answer="False",
                        explanation="Type II reports assess the operating effectiveness of controls over a period (typically 6-12 months). Type I is point-in-time.",
                        points=10,
                    ),
                    Question(
                        module_id=mod.id,
                        type=QuestionType.MULTIPLE_CHOICE,
                        question_text="What is the minimum recommended observation period for a SOC 2 Type II audit?",
                        options=["1 month", "3 months", "6 months", "12 months"],
                        correct_answer="6 months",
                        explanation="While not mandated, 6 months is the minimum recommended observation period for meaningful Type II assessment.",
                        points=10,
                    ),
                ]
            modules.append(mod)

        return Course(
            id=course_id,
            title="SOC 2 Compliance Engineering",
            description="Engineer SOC 2 compliant systems with continuous monitoring and automated evidence collection.",
            regulation="SOC 2",
            level=CourseLevel.ADVANCED,
            modules=modules,
            estimated_hours=16.0,
            prerequisites=["Cloud infrastructure experience", "Basic security knowledge"],
            learning_objectives=[
                "Understand and implement the five Trust Service Criteria",
                "Build continuous compliance monitoring systems",
                "Automate evidence collection for SOC 2 audits",
                "Prepare for SOC 2 Type II audit readiness",
            ],
            is_free=True,
            enrolled_count=763,
            completion_rate=74.8,
            rating=4.5,
        )
