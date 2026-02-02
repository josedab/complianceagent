"""Compliance training mode service."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.training.models import (
    Certificate,
    CertificateStatus,
    Question,
    QuestionType,
    Quiz,
    QuizAttempt,
    TrainingModule,
    TrainingProgress,
    UserTrainingProfile,
)


logger = structlog.get_logger()


class TrainingService:
    """Service for compliance training and certification."""
    
    def __init__(self, db: AsyncSession, copilot: Any = None):
        self.db = db
        self.copilot = copilot
        self._modules: dict[UUID, TrainingModule] = {}
        self._progress: dict[str, TrainingProgress] = {}
        self._certificates: dict[UUID, Certificate] = {}
        self._profiles: dict[UUID, UserTrainingProfile] = {}
        self._initialize_modules()
    
    def _initialize_modules(self):
        """Initialize built-in training modules."""
        self._modules[uuid4()] = self._create_gdpr_module()
        self._modules[uuid4()] = self._create_hipaa_module()
        self._modules[uuid4()] = self._create_secure_coding_module()
    
    # --- Module Management ---
    
    async def list_modules(
        self,
        framework: str | None = None,
        difficulty: str | None = None,
    ) -> list[TrainingModule]:
        """List available training modules."""
        modules = list(self._modules.values())
        
        if framework:
            modules = [m for m in modules if m.framework == framework]
        
        if difficulty:
            modules = [m for m in modules if m.difficulty == difficulty]
        
        return modules
    
    async def get_module(self, module_id: UUID) -> TrainingModule | None:
        """Get a training module by ID."""
        return self._modules.get(module_id)
    
    # --- Progress Tracking ---
    
    async def enroll(
        self,
        user_id: UUID,
        module_id: UUID,
    ) -> TrainingProgress:
        """Enroll user in a training module."""
        module = self._modules.get(module_id)
        if not module:
            raise ValueError(f"Module not found: {module_id}")
        
        key = f"{user_id}:{module_id}"
        
        if key in self._progress:
            return self._progress[key]
        
        progress = TrainingProgress(
            user_id=user_id,
            module_id=module_id,
        )
        
        self._progress[key] = progress
        
        logger.info(
            "user_enrolled",
            user_id=str(user_id),
            module_id=str(module_id),
        )
        
        return progress
    
    async def get_progress(
        self,
        user_id: UUID,
        module_id: UUID,
    ) -> TrainingProgress | None:
        """Get user's progress in a module."""
        key = f"{user_id}:{module_id}"
        return self._progress.get(key)
    
    async def update_progress(
        self,
        user_id: UUID,
        module_id: UUID,
        section_completed: int,
    ) -> TrainingProgress:
        """Update user's progress after completing a section."""
        key = f"{user_id}:{module_id}"
        progress = self._progress.get(key)
        
        if not progress:
            progress = await self.enroll(user_id, module_id)
        
        module = self._modules.get(module_id)
        if not module:
            raise ValueError("Module not found")
        
        if section_completed not in progress.sections_completed:
            progress.sections_completed.append(section_completed)
        
        progress.current_section = section_completed + 1
        
        # Calculate progress percentage
        total_sections = len(module.sections)
        if total_sections > 0:
            progress.progress_percentage = (
                len(progress.sections_completed) / total_sections * 100
            )
        
        return progress
    
    async def get_user_profile(
        self,
        user_id: UUID,
        organization_id: UUID | None = None,
    ) -> UserTrainingProfile:
        """Get user's training profile."""
        if user_id not in self._profiles:
            self._profiles[user_id] = UserTrainingProfile(
                user_id=user_id,
                organization_id=organization_id,
            )
        
        profile = self._profiles[user_id]
        
        # Update with current progress
        profile.current_enrollments = [
            p for p in self._progress.values()
            if p.user_id == user_id and not p.is_complete
        ]
        
        profile.certificates = [
            c for c in self._certificates.values()
            if c.user_id == user_id
        ]
        
        return profile
    
    # --- Quiz Management ---
    
    async def start_quiz(
        self,
        user_id: UUID,
        module_id: UUID,
        quiz_index: int = 0,
    ) -> QuizAttempt:
        """Start a quiz attempt."""
        module = self._modules.get(module_id)
        if not module:
            raise ValueError("Module not found")
        
        if quiz_index >= len(module.quizzes):
            raise ValueError("Quiz not found")
        
        quiz = module.quizzes[quiz_index]
        
        # Check attempt limit
        key = f"{user_id}:{module_id}"
        progress = self._progress.get(key)
        attempt_count = len([
            a for a in (progress.quiz_attempts if progress else [])
            if a.quiz_id == quiz.id
        ])
        
        if attempt_count >= quiz.max_attempts:
            raise ValueError("Maximum attempts reached")
        
        attempt = QuizAttempt(
            quiz_id=quiz.id,
            user_id=user_id,
            attempt_number=attempt_count + 1,
        )
        
        return attempt
    
    async def submit_quiz(
        self,
        user_id: UUID,
        module_id: UUID,
        quiz_index: int,
        answers: dict[str, list[int]],
    ) -> QuizAttempt:
        """Submit quiz answers and get results."""
        module = self._modules.get(module_id)
        if not module:
            raise ValueError("Module not found")
        
        quiz = module.quizzes[quiz_index]
        
        # Score the quiz
        total_points = 0
        earned_points = 0
        
        for question in quiz.questions:
            total_points += question.points
            
            user_answers = answers.get(str(question.id), [])
            if sorted(user_answers) == sorted(question.correct_answers):
                earned_points += question.points
        
        score = (earned_points / total_points * 100) if total_points > 0 else 0
        passed = score >= quiz.passing_score
        
        # Create attempt record
        attempt = QuizAttempt(
            quiz_id=quiz.id,
            user_id=user_id,
            completed_at=datetime.utcnow(),
            answers=answers,
            score=score,
            passed=passed,
        )
        
        # Update progress
        key = f"{user_id}:{module_id}"
        progress = self._progress.get(key)
        if progress:
            progress.quiz_attempts.append(attempt)
            if score > progress.best_quiz_score:
                progress.best_quiz_score = score
            
            # Check if module is complete
            if passed and len(progress.sections_completed) >= len(module.sections):
                progress.is_complete = True
                progress.completed_at = datetime.utcnow()
                
                # Issue certificate
                await self._issue_certificate(user_id, module_id, score)
        
        logger.info(
            "quiz_submitted",
            user_id=str(user_id),
            quiz_id=str(quiz.id),
            score=score,
            passed=passed,
        )
        
        return attempt
    
    async def get_quiz_results(
        self,
        user_id: UUID,
        module_id: UUID,
        quiz_index: int,
        attempt_id: UUID,
    ) -> dict:
        """Get detailed quiz results with explanations."""
        module = self._modules.get(module_id)
        if not module:
            raise ValueError("Module not found")
        
        quiz = module.quizzes[quiz_index]
        
        key = f"{user_id}:{module_id}"
        progress = self._progress.get(key)
        
        attempt = None
        if progress:
            for a in progress.quiz_attempts:
                if a.id == attempt_id:
                    attempt = a
                    break
        
        if not attempt:
            raise ValueError("Attempt not found")
        
        # Build detailed results
        results = {
            "attempt_id": str(attempt.id),
            "score": attempt.score,
            "passed": attempt.passed,
            "questions": [],
        }
        
        for question in quiz.questions:
            user_answers = attempt.answers.get(str(question.id), [])
            correct = sorted(user_answers) == sorted(question.correct_answers)
            
            result = {
                "question_id": str(question.id),
                "text": question.text,
                "user_answers": user_answers,
                "correct": correct,
                "points_earned": question.points if correct else 0,
                "points_possible": question.points,
            }
            
            if quiz.show_correct_answers:
                result["correct_answers"] = question.correct_answers
                result["explanation"] = question.explanation
            
            results["questions"].append(result)
        
        return results
    
    # --- Certificate Management ---
    
    async def _issue_certificate(
        self,
        user_id: UUID,
        module_id: UUID,
        score: float,
    ) -> Certificate:
        """Issue a completion certificate."""
        module = self._modules.get(module_id)
        if not module:
            raise ValueError("Module not found")
        
        verification_code = self._generate_verification_code()
        
        certificate = Certificate(
            user_id=user_id,
            module_id=module_id,
            framework=module.framework,
            title=f"{module.title} Certification",
            score=score,
            verification_code=verification_code,
            metadata={
                "module_version": module.version,
                "requirements_covered": module.requirements_covered,
            },
        )
        
        self._certificates[certificate.id] = certificate
        
        # Update user profile
        if user_id in self._profiles:
            self._profiles[user_id].certificates.append(certificate)
            self._profiles[user_id].total_modules_completed += 1
            self._profiles[user_id].framework_scores[module.framework] = score
        
        logger.info(
            "certificate_issued",
            user_id=str(user_id),
            certificate_id=str(certificate.id),
            framework=module.framework,
        )
        
        return certificate
    
    def _generate_verification_code(self) -> str:
        """Generate unique verification code."""
        random_bytes = secrets.token_bytes(16)
        return hashlib.sha256(random_bytes).hexdigest()[:12].upper()
    
    async def verify_certificate(
        self,
        verification_code: str,
    ) -> Certificate | None:
        """Verify a certificate by its code."""
        for cert in self._certificates.values():
            if cert.verification_code == verification_code:
                if cert.status == CertificateStatus.ACTIVE:
                    if cert.expires_at > datetime.utcnow():
                        return cert
                    else:
                        cert.status = CertificateStatus.EXPIRED
                return cert
        return None
    
    async def list_certificates(
        self,
        user_id: UUID | None = None,
        organization_id: UUID | None = None,
    ) -> list[Certificate]:
        """List certificates."""
        certs = list(self._certificates.values())
        
        if user_id:
            certs = [c for c in certs if c.user_id == user_id]
        
        if organization_id:
            certs = [c for c in certs if c.organization_id == organization_id]
        
        return certs
    
    # --- AI-Powered Quiz Generation ---
    
    async def generate_quiz(
        self,
        framework: str,
        topics: list[str],
        num_questions: int = 10,
        difficulty: str = "medium",
    ) -> Quiz:
        """Generate a quiz using AI."""
        if not self.copilot:
            # Return static quiz if no AI available
            return self._create_static_quiz(framework, num_questions)
        
        try:
            prompt = f"""Generate {num_questions} {difficulty} difficulty multiple choice questions 
            about {framework} compliance, covering these topics: {', '.join(topics)}.
            
            For each question, provide:
            1. The question text
            2. Four answer options (A, B, C, D)
            3. The correct answer (0-3 index)
            4. A brief explanation
            
            Format as JSON array."""
            
            response = await self.copilot.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a compliance training expert."},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-4o-mini",
            )
            
            # Parse response and create Quiz
            # (In production, would parse JSON from response)
            return self._create_static_quiz(framework, num_questions)
            
        except Exception as e:
            logger.error("quiz_generation_failed", error=str(e))
            return self._create_static_quiz(framework, num_questions)
    
    def _create_static_quiz(self, framework: str, num_questions: int) -> Quiz:
        """Create a static quiz with predefined questions."""
        questions = self._get_framework_questions(framework)[:num_questions]
        
        return Quiz(
            title=f"{framework} Knowledge Assessment",
            description=f"Test your knowledge of {framework} compliance requirements",
            framework=framework,
            questions=questions,
        )
    
    def _get_framework_questions(self, framework: str) -> list[Question]:
        """Get predefined questions for a framework."""
        if framework == "GDPR":
            return self._gdpr_questions()
        elif framework == "HIPAA":
            return self._hipaa_questions()
        elif framework == "PCI_DSS":
            return self._pci_questions()
        return []
    
    # --- Module Definitions ---
    
    def _create_gdpr_module(self) -> TrainingModule:
        """Create GDPR training module."""
        return TrainingModule(
            title="GDPR Fundamentals for Developers",
            description="Learn the key principles of GDPR and how to implement compliant code",
            framework="GDPR",
            difficulty="beginner",
            estimated_minutes=45,
            learning_objectives=[
                "Understand the 7 principles of GDPR",
                "Identify personal data in code",
                "Implement data subject rights",
                "Apply privacy by design principles",
            ],
            requirements_covered=[
                "Article 5 - Principles",
                "Article 7 - Consent",
                "Article 17 - Right to Erasure",
                "Article 25 - Privacy by Design",
            ],
            sections=[
                {
                    "title": "Introduction to GDPR",
                    "content": "The General Data Protection Regulation (GDPR) is the EU's comprehensive data protection law...",
                    "duration_minutes": 10,
                },
                {
                    "title": "The Seven Principles",
                    "content": "GDPR is built on seven key principles: lawfulness, fairness, transparency...",
                    "duration_minutes": 15,
                },
                {
                    "title": "Consent Management",
                    "content": "Valid consent under GDPR must be freely given, specific, informed, and unambiguous...",
                    "duration_minutes": 10,
                },
                {
                    "title": "Data Subject Rights",
                    "content": "GDPR grants individuals several rights regarding their personal data...",
                    "duration_minutes": 10,
                },
            ],
            quizzes=[
                Quiz(
                    title="GDPR Knowledge Check",
                    description="Test your understanding of GDPR fundamentals",
                    framework="GDPR",
                    questions=self._gdpr_questions(),
                    passing_score=70,
                ),
            ],
        )
    
    def _create_hipaa_module(self) -> TrainingModule:
        """Create HIPAA training module."""
        return TrainingModule(
            title="HIPAA Security for Healthcare Applications",
            description="Learn to build HIPAA-compliant healthcare software",
            framework="HIPAA",
            difficulty="intermediate",
            estimated_minutes=60,
            learning_objectives=[
                "Understand PHI and its requirements",
                "Implement access controls for ePHI",
                "Apply the Security Rule safeguards",
                "Handle BAA requirements",
            ],
            requirements_covered=[
                "164.312(a) - Access Control",
                "164.312(b) - Audit Controls",
                "164.312(e) - Transmission Security",
            ],
            sections=[
                {
                    "title": "HIPAA Overview",
                    "content": "HIPAA (Health Insurance Portability and Accountability Act) sets standards for PHI protection...",
                    "duration_minutes": 15,
                },
                {
                    "title": "The Security Rule",
                    "content": "The Security Rule establishes standards for protecting ePHI...",
                    "duration_minutes": 20,
                },
                {
                    "title": "Technical Safeguards",
                    "content": "Technical safeguards include access control, audit controls, integrity controls...",
                    "duration_minutes": 15,
                },
                {
                    "title": "Business Associates",
                    "content": "A Business Associate Agreement (BAA) is required when sharing PHI with third parties...",
                    "duration_minutes": 10,
                },
            ],
            quizzes=[
                Quiz(
                    title="HIPAA Security Assessment",
                    framework="HIPAA",
                    questions=self._hipaa_questions(),
                    passing_score=75,
                ),
            ],
        )
    
    def _create_secure_coding_module(self) -> TrainingModule:
        """Create secure coding training module."""
        return TrainingModule(
            title="Secure Coding for Compliance",
            description="Learn secure coding practices for regulatory compliance",
            framework="SECURE_CODING",
            difficulty="intermediate",
            estimated_minutes=90,
            learning_objectives=[
                "Identify common security vulnerabilities",
                "Implement secure authentication",
                "Apply input validation best practices",
                "Secure data storage and transmission",
            ],
            requirements_covered=[
                "OWASP Top 10",
                "SOC2 CC6.6",
                "PCI-DSS Req 6.5",
            ],
            sections=[
                {
                    "title": "Security Fundamentals",
                    "content": "Security is not a feature, it's a requirement...",
                    "duration_minutes": 20,
                },
                {
                    "title": "Authentication & Authorization",
                    "content": "Proper authentication verifies identity, authorization controls access...",
                    "duration_minutes": 25,
                },
                {
                    "title": "Input Validation",
                    "content": "Never trust user input. Always validate and sanitize...",
                    "duration_minutes": 20,
                },
                {
                    "title": "Secure Data Handling",
                    "content": "Encrypt sensitive data at rest and in transit...",
                    "duration_minutes": 25,
                },
            ],
            quizzes=[
                Quiz(
                    title="Secure Coding Assessment",
                    framework="SECURE_CODING",
                    questions=self._secure_coding_questions(),
                    passing_score=80,
                ),
            ],
        )
    
    # --- Question Banks ---
    
    def _gdpr_questions(self) -> list[Question]:
        """GDPR quiz questions."""
        return [
            Question(
                question_type=QuestionType.MULTIPLE_CHOICE,
                text="Which of the following is NOT one of the seven GDPR principles?",
                options=[
                    {"id": 0, "text": "Lawfulness, fairness and transparency"},
                    {"id": 1, "text": "Purpose limitation"},
                    {"id": 2, "text": "Data monetization"},
                    {"id": 3, "text": "Storage limitation"},
                ],
                correct_answers=[2],
                explanation="Data monetization is not a GDPR principle. The seven principles are: lawfulness/fairness/transparency, purpose limitation, data minimization, accuracy, storage limitation, integrity/confidentiality, and accountability.",
                framework="GDPR",
                requirement_id="Art5",
            ),
            Question(
                question_type=QuestionType.TRUE_FALSE,
                text="Under GDPR, consent can be implied from user actions such as continuing to use a website.",
                options=[
                    {"id": 0, "text": "True"},
                    {"id": 1, "text": "False"},
                ],
                correct_answers=[1],
                explanation="GDPR requires explicit, affirmative consent. Pre-ticked boxes or implied consent are not valid.",
                framework="GDPR",
                requirement_id="Art7",
            ),
            Question(
                question_type=QuestionType.MULTIPLE_CHOICE,
                text="What is the maximum time allowed to respond to a Data Subject Access Request (DSAR)?",
                options=[
                    {"id": 0, "text": "72 hours"},
                    {"id": 1, "text": "1 week"},
                    {"id": 2, "text": "30 days"},
                    {"id": 3, "text": "90 days"},
                ],
                correct_answers=[2],
                explanation="Organizations must respond to DSARs within one month (approximately 30 days), though this can be extended by two additional months for complex requests.",
                framework="GDPR",
                requirement_id="Art15",
            ),
            Question(
                question_type=QuestionType.CODE_REVIEW,
                text="Is this code GDPR-compliant for deleting user data?",
                code_snippet="""def delete_user(user_id):
    user = User.query.get(user_id)
    user.is_active = False
    db.session.commit()
    return {'status': 'deleted'}""",
                options=[
                    {"id": 0, "text": "Yes, it properly handles deletion"},
                    {"id": 1, "text": "No, it only soft-deletes, not truly erases"},
                    {"id": 2, "text": "No, it lacks authentication"},
                    {"id": 3, "text": "No, it should use DELETE method"},
                ],
                correct_answers=[1],
                explanation="The Right to Erasure (Article 17) requires actual deletion, not just marking as inactive. Personal data must be permanently removed.",
                framework="GDPR",
                requirement_id="Art17",
            ),
            Question(
                question_type=QuestionType.MULTI_SELECT,
                text="Which of the following are valid lawful bases for processing personal data under GDPR? (Select all that apply)",
                options=[
                    {"id": 0, "text": "Consent"},
                    {"id": 1, "text": "Contract performance"},
                    {"id": 2, "text": "Company policy"},
                    {"id": 3, "text": "Legitimate interests"},
                ],
                correct_answers=[0, 1, 3],
                explanation="The six lawful bases are: consent, contract, legal obligation, vital interests, public task, and legitimate interests. Company policy is not a valid lawful basis.",
                framework="GDPR",
                requirement_id="Art6",
            ),
        ]
    
    def _hipaa_questions(self) -> list[Question]:
        """HIPAA quiz questions."""
        return [
            Question(
                question_type=QuestionType.MULTIPLE_CHOICE,
                text="Which of the following is considered Protected Health Information (PHI)?",
                options=[
                    {"id": 0, "text": "A patient's name with their diagnosis"},
                    {"id": 1, "text": "Anonymous health statistics"},
                    {"id": 2, "text": "De-identified research data"},
                    {"id": 3, "text": "General health tips on a website"},
                ],
                correct_answers=[0],
                explanation="PHI is any health information that can be linked to a specific individual. Names combined with health conditions constitute PHI.",
                framework="HIPAA",
                requirement_id="164.501",
            ),
            Question(
                question_type=QuestionType.MULTIPLE_CHOICE,
                text="What is the maximum session timeout for systems containing ePHI?",
                options=[
                    {"id": 0, "text": "No requirement specified"},
                    {"id": 1, "text": "5 minutes"},
                    {"id": 2, "text": "15 minutes of inactivity"},
                    {"id": 3, "text": "8 hours"},
                ],
                correct_answers=[2],
                explanation="HIPAA requires automatic logoff after a reasonable period of inactivity. The generally accepted standard is 15 minutes.",
                framework="HIPAA",
                requirement_id="164.312(a)(2)(iii)",
            ),
            Question(
                question_type=QuestionType.TRUE_FALSE,
                text="A Business Associate Agreement (BAA) is optional for cloud service providers storing ePHI.",
                options=[
                    {"id": 0, "text": "True"},
                    {"id": 1, "text": "False"},
                ],
                correct_answers=[1],
                explanation="BAAs are mandatory for any third party (business associate) that creates, receives, maintains, or transmits PHI on behalf of a covered entity.",
                framework="HIPAA",
                requirement_id="164.308(b)(1)",
            ),
            Question(
                question_type=QuestionType.MULTIPLE_CHOICE,
                text="How long must HIPAA audit logs be retained?",
                options=[
                    {"id": 0, "text": "1 year"},
                    {"id": 1, "text": "3 years"},
                    {"id": 2, "text": "6 years"},
                    {"id": 3, "text": "10 years"},
                ],
                correct_answers=[2],
                explanation="HIPAA requires retention of documentation (including audit logs) for 6 years from the date of creation or the date when it last was in effect.",
                framework="HIPAA",
                requirement_id="164.530(j)",
            ),
        ]
    
    def _pci_questions(self) -> list[Question]:
        """PCI-DSS quiz questions."""
        return [
            Question(
                question_type=QuestionType.TRUE_FALSE,
                text="It is acceptable to store the CVV/CVC code if it is encrypted.",
                options=[
                    {"id": 0, "text": "True"},
                    {"id": 1, "text": "False"},
                ],
                correct_answers=[1],
                explanation="CVV/CVC codes must NEVER be stored after authorization, even if encrypted. This is a strict PCI-DSS requirement.",
                framework="PCI_DSS",
                requirement_id="3.2.2",
            ),
            Question(
                question_type=QuestionType.MULTIPLE_CHOICE,
                text="When displaying a PAN, which digits can be shown unmasked?",
                options=[
                    {"id": 0, "text": "Any 8 digits"},
                    {"id": 1, "text": "First 6 and last 4 only"},
                    {"id": 2, "text": "Last 8 digits only"},
                    {"id": 3, "text": "First 4 digits only"},
                ],
                correct_answers=[1],
                explanation="PCI-DSS allows showing only the first six and last four digits of a PAN. All other digits must be masked.",
                framework="PCI_DSS",
                requirement_id="3.3",
            ),
        ]
    
    def _secure_coding_questions(self) -> list[Question]:
        """Secure coding quiz questions."""
        return [
            Question(
                question_type=QuestionType.CODE_REVIEW,
                text="What vulnerability does this code have?",
                code_snippet="""def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)""",
                options=[
                    {"id": 0, "text": "Buffer overflow"},
                    {"id": 1, "text": "SQL injection"},
                    {"id": 2, "text": "Cross-site scripting"},
                    {"id": 3, "text": "No vulnerability"},
                ],
                correct_answers=[1],
                explanation="This code is vulnerable to SQL injection because user input is directly interpolated into the query string. Use parameterized queries instead.",
                framework="SECURE_CODING",
                requirement_id="OWASP-A03",
            ),
            Question(
                question_type=QuestionType.MULTIPLE_CHOICE,
                text="Which is the most secure way to store user passwords?",
                options=[
                    {"id": 0, "text": "MD5 hash"},
                    {"id": 1, "text": "SHA-256 hash"},
                    {"id": 2, "text": "bcrypt with salt"},
                    {"id": 3, "text": "AES encryption"},
                ],
                correct_answers=[2],
                explanation="bcrypt with salt is designed for password hashing with built-in salt and adaptive cost factor. MD5 and SHA-256 are too fast. Encryption is reversible, which is undesirable for passwords.",
                framework="SECURE_CODING",
                requirement_id="OWASP-A02",
            ),
            Question(
                question_type=QuestionType.MULTIPLE_CHOICE,
                text="What is the primary defense against Cross-Site Scripting (XSS)?",
                options=[
                    {"id": 0, "text": "Rate limiting"},
                    {"id": 1, "text": "Output encoding/escaping"},
                    {"id": 2, "text": "HTTPS only"},
                    {"id": 3, "text": "Strong passwords"},
                ],
                correct_answers=[1],
                explanation="Output encoding/escaping user-supplied data before rendering prevents malicious scripts from executing. Always encode output based on the context (HTML, JavaScript, URL, etc.).",
                framework="SECURE_CODING",
                requirement_id="OWASP-A07",
            ),
        ]
