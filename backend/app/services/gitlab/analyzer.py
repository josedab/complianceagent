"""GitLab repository analyzer for compliance scanning."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

from app.services.gitlab.client import GitLabClient


logger = structlog.get_logger()


class ComplianceFileType(Enum):
    """Types of compliance-relevant files."""
    PRIVACY_POLICY = "privacy_policy"
    TERMS_OF_SERVICE = "terms_of_service"
    DATA_HANDLER = "data_handler"
    AUTHENTICATION = "authentication"
    ENCRYPTION = "encryption"
    LOGGING = "logging"
    CONFIGURATION = "configuration"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    API_ENDPOINT = "api_endpoint"
    DATABASE = "database"
    CONSENT = "consent"


@dataclass
class ComplianceFile:
    """A file relevant to compliance analysis."""
    path: str
    file_type: ComplianceFileType
    content: str | None = None
    analysis: dict[str, Any] = field(default_factory=dict)


@dataclass
class RepositoryStructure:
    """Analyzed structure of a repository."""
    languages: dict[str, float]
    frameworks: list[str]
    directories: list[str]
    compliance_files: list[ComplianceFile]
    total_files: int
    has_tests: bool
    has_ci: bool
    has_docker: bool
    has_security_config: bool


FILE_PATTERNS = {
    ComplianceFileType.PRIVACY_POLICY: [
        "privacy", "privacy-policy", "gdpr", "data-protection",
    ],
    ComplianceFileType.TERMS_OF_SERVICE: [
        "terms", "tos", "terms-of-service", "legal",
    ],
    ComplianceFileType.DATA_HANDLER: [
        "user", "customer", "profile", "account", "personal",
        "pii", "data", "handler", "processor",
    ],
    ComplianceFileType.AUTHENTICATION: [
        "auth", "login", "session", "jwt", "oauth", "saml",
        "sso", "identity", "credential", "password",
    ],
    ComplianceFileType.ENCRYPTION: [
        "encrypt", "decrypt", "crypto", "cipher", "hash",
        "secret", "key", "certificate", "ssl", "tls",
    ],
    ComplianceFileType.LOGGING: [
        "log", "audit", "trace", "monitor", "telemetry",
        "analytics", "tracking", "event",
    ],
    ComplianceFileType.CONFIGURATION: [
        "config", "settings", "env", "environment", "secret",
    ],
    ComplianceFileType.INFRASTRUCTURE: [
        "docker", "kubernetes", "k8s", "terraform", "ansible",
        "helm", "deploy", "infrastructure", "iac",
    ],
    ComplianceFileType.SECURITY: [
        "security", "firewall", "cors", "csp", "permission",
        "rbac", "acl", "access", "policy",
    ],
    ComplianceFileType.API_ENDPOINT: [
        "api", "route", "controller", "endpoint", "handler",
        "view", "resource",
    ],
    ComplianceFileType.DATABASE: [
        "database", "db", "model", "schema", "migration",
        "repository", "entity", "orm",
    ],
    ComplianceFileType.CONSENT: [
        "consent", "cookie", "preference", "opt-in", "opt-out",
        "gdpr", "ccpa", "banner",
    ],
}

FRAMEWORK_INDICATORS = {
    "Django": ["django", "settings.py", "urls.py", "wsgi.py"],
    "FastAPI": ["fastapi", "main.py", "uvicorn"],
    "Flask": ["flask", "app.py", "wsgi.py"],
    "Express": ["express", "package.json", "node_modules"],
    "Next.js": ["next.config", "pages", "app"],
    "React": ["react", "package.json", "src/components"],
    "Spring Boot": ["spring", "pom.xml", "application.properties"],
    "Rails": ["rails", "Gemfile", "config/routes.rb"],
    "Laravel": ["laravel", "composer.json", "artisan"],
    ".NET": ["csproj", "Program.cs", "Startup.cs", "appsettings.json"],
}


class GitLabAnalyzer:
    """Analyzes GitLab repositories for compliance-relevant code."""

    def __init__(self, client: GitLabClient):
        self.client = client

    async def analyze_repository(
        self,
        project_id: str | int,
        ref: str | None = None,
    ) -> RepositoryStructure:
        """Perform full repository analysis."""
        logger.info("Analyzing GitLab repository", project_id=project_id, ref=ref)

        # Get project details
        project = await self.client.get_project(project_id)
        logger.info("Found project", name=project.name, full_path=project.full_path)

        # Get languages
        languages = await self.client.get_project_languages(project_id)

        # Get file tree
        ref = ref or project.default_branch
        try:
            tree = await self.client.get_repository_tree(
                project_id,
                ref=ref,
                recursive=True,
            )
        except ValueError:
            logger.warning("Could not get repository tree, using empty tree")
            tree = []

        # Analyze structure
        directories = list({
            f.path.rsplit("/", 1)[0]
            for f in tree
            if "/" in f.path and f.type == "blob"
        })

        # Detect frameworks
        file_paths = [f.path.lower() for f in tree]
        frameworks = self._detect_frameworks(file_paths)

        # Find compliance-relevant files
        compliance_files = await self._find_compliance_files(
            project_id,
            tree,
            ref,
        )

        # Check for common project features
        has_tests = any(
            "test" in p or "spec" in p or "__tests__" in p
            for p in file_paths
        )
        has_ci = any(
            ".gitlab-ci" in p or ".github/workflows" in p or "Jenkinsfile" in p.lower()
            for p in file_paths
        )
        has_docker = any(
            "dockerfile" in p.lower() or "docker-compose" in p.lower()
            for p in file_paths
        )
        has_security_config = any(
            "security" in p.lower() or ".snyk" in p or "dependabot" in p
            for p in file_paths
        )

        return RepositoryStructure(
            languages=languages,
            frameworks=frameworks,
            directories=directories,
            compliance_files=compliance_files,
            total_files=len([f for f in tree if f.type == "blob"]),
            has_tests=has_tests,
            has_ci=has_ci,
            has_docker=has_docker,
            has_security_config=has_security_config,
        )

    def _detect_frameworks(self, file_paths: list[str]) -> list[str]:
        """Detect frameworks based on file patterns."""
        detected = []
        for framework, indicators in FRAMEWORK_INDICATORS.items():
            if any(
                any(ind.lower() in path for ind in indicators)
                for path in file_paths
            ):
                detected.append(framework)
        return detected

    async def _find_compliance_files(
        self,
        project_id: str | int,
        tree: list[Any],
        ref: str,
    ) -> list[ComplianceFile]:
        """Find compliance-relevant files in the repository."""
        compliance_files = []

        for file_obj in tree:
            if file_obj.type != "blob":
                continue

            path_lower = file_obj.path.lower()
            name_lower = file_obj.name.lower()

            for file_type, patterns in FILE_PATTERNS.items():
                if any(p in path_lower or p in name_lower for p in patterns):
                    # Skip node_modules, vendor, etc.
                    if any(skip in path_lower for skip in [
                        "node_modules", "vendor", "venv", ".git",
                        "dist", "build", "__pycache__",
                    ]):
                        continue

                    compliance_files.append(ComplianceFile(
                        path=file_obj.path,
                        file_type=file_type,
                    ))
                    break

        logger.info(
            "Found compliance files",
            count=len(compliance_files),
            types=[f.file_type.value for f in compliance_files[:10]],
        )

        return compliance_files

    async def get_file_content(
        self,
        project_id: str | int,
        file_path: str,
        ref: str | None = None,
    ) -> str:
        """Get content of a specific file."""
        return await self.client.get_file_content(project_id, file_path, ref)

    async def analyze_compliance_file(
        self,
        project_id: str | int,
        compliance_file: ComplianceFile,
        ref: str | None = None,
    ) -> ComplianceFile:
        """Analyze a specific compliance file."""
        try:
            content = await self.get_file_content(
                project_id,
                compliance_file.path,
                ref,
            )
            compliance_file.content = content

            # Basic analysis based on file type
            analysis = {"patterns_found": []}

            if compliance_file.file_type == ComplianceFileType.DATA_HANDLER:
                pii_patterns = [
                    "email", "phone", "address", "ssn", "social_security",
                    "date_of_birth", "dob", "credit_card", "passport",
                    "driver_license", "ip_address", "geolocation",
                ]
                analysis["patterns_found"] = [
                    p for p in pii_patterns
                    if p in content.lower()
                ]
                analysis["has_pii_handling"] = len(analysis["patterns_found"]) > 0

            elif compliance_file.file_type == ComplianceFileType.ENCRYPTION:
                crypto_patterns = [
                    "aes", "rsa", "sha256", "sha512", "bcrypt", "argon2",
                    "pbkdf2", "hmac", "encrypt", "decrypt",
                ]
                analysis["patterns_found"] = [
                    p for p in crypto_patterns
                    if p in content.lower()
                ]
                analysis["has_strong_crypto"] = any(
                    p in analysis["patterns_found"]
                    for p in ["aes", "rsa", "bcrypt", "argon2"]
                )

            elif compliance_file.file_type == ComplianceFileType.AUTHENTICATION:
                auth_patterns = [
                    "password", "token", "jwt", "session", "oauth",
                    "mfa", "2fa", "totp", "sso", "saml",
                ]
                analysis["patterns_found"] = [
                    p for p in auth_patterns
                    if p in content.lower()
                ]
                analysis["has_secure_auth"] = any(
                    p in analysis["patterns_found"]
                    for p in ["mfa", "2fa", "totp", "oauth", "saml"]
                )

            elif compliance_file.file_type == ComplianceFileType.LOGGING:
                logging_patterns = [
                    "audit", "trail", "event", "action", "user_id",
                    "timestamp", "ip_address", "sensitive", "mask",
                ]
                analysis["patterns_found"] = [
                    p for p in logging_patterns
                    if p in content.lower()
                ]
                analysis["has_audit_logging"] = "audit" in content.lower()
                analysis["masks_sensitive"] = "mask" in content.lower() or "redact" in content.lower()

            compliance_file.analysis = analysis

        except Exception as e:
            logger.warning(
                "Failed to analyze file",
                path=compliance_file.path,
                error=str(e),
            )
            compliance_file.analysis = {"error": str(e)}

        return compliance_file

    async def scan_for_sensitive_data(
        self,
        project_id: str | int,
        ref: str | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """Scan repository for potentially exposed sensitive data."""
        sensitive_patterns = {
            "api_keys": [
                r"api[_-]?key\s*[=:]\s*['\"][a-zA-Z0-9]{20,}",
                r"apikey\s*[=:]\s*['\"][a-zA-Z0-9]{20,}",
            ],
            "secrets": [
                r"secret\s*[=:]\s*['\"][a-zA-Z0-9]{10,}",
                r"password\s*[=:]\s*['\"][^'\"]+['\"]",
            ],
            "tokens": [
                r"token\s*[=:]\s*['\"][a-zA-Z0-9_-]{20,}",
                r"bearer\s+[a-zA-Z0-9_-]{20,}",
            ],
            "private_keys": [
                r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
                r"-----BEGIN\s+EC\s+PRIVATE\s+KEY-----",
            ],
            "aws_credentials": [
                r"AKIA[0-9A-Z]{16}",
                r"aws_secret_access_key\s*[=:]\s*['\"][a-zA-Z0-9/+=]{40}",
            ],
            "database_urls": [
                r"postgres://[^:]+:[^@]+@",
                r"mysql://[^:]+:[^@]+@",
                r"mongodb://[^:]+:[^@]+@",
            ],
        }

        import re

        findings: dict[str, list[dict[str, Any]]] = {k: [] for k in sensitive_patterns}

        # Get config files that might contain secrets
        project = await self.client.get_project(project_id)
        ref = ref or project.default_branch

        try:
            tree = await self.client.get_repository_tree(
                project_id,
                ref=ref,
                recursive=True,
            )
        except ValueError:
            return findings

        config_extensions = [
            ".env", ".yaml", ".yml", ".json", ".conf", ".cfg",
            ".properties", ".ini", ".toml",
        ]

        for file_obj in tree:
            if file_obj.type != "blob":
                continue

            # Check config files and common secret locations
            if any(file_obj.path.endswith(ext) for ext in config_extensions):
                try:
                    content = await self.client.get_file_content(
                        project_id,
                        file_obj.path,
                        ref,
                    )

                    for category, patterns in sensitive_patterns.items():
                        for pattern in patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                # Don't include actual secret values
                                findings[category].append({
                                    "file": file_obj.path,
                                    "line_hint": content[:match.start()].count("\n") + 1,
                                    "pattern_matched": pattern[:30] + "...",
                                })

                except Exception:
                    continue

        return findings
