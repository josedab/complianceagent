"""Repository analysis service - analyzes codebases for compliance."""

from datetime import UTC, datetime
from typing import Any

import structlog

from app.models.codebase import Repository
from app.services.github.client import GitHubClient, get_github_client


logger = structlog.get_logger()


class RepositoryAnalyzer:
    """Analyzes repository structure and content."""

    COMPLIANCE_PATTERNS = {
        "data_handling": [
            "**/user*.py", "**/customer*.py", "**/profile*.py",
            "**/data*.py", "**/pii*.py", "**/personal*.py",
        ],
        "consent": [
            "**/consent*.py", "**/gdpr*.py", "**/privacy*.py",
        ],
        "security": [
            "**/auth*.py", "**/security*.py", "**/encrypt*.py",
            "**/crypto*.py", "**/password*.py",
        ],
        "logging": [
            "**/log*.py", "**/audit*.py", "**/track*.py",
        ],
        "api": [
            "**/api/**/*.py", "**/routes/**/*.py",
        ],
    }

    COMPLIANCE_KEYWORDS = {
        "pii": ["personal_data", "pii", "ssn", "email", "phone"],
        "consent": ["consent", "opt_in", "opt_out", "gdpr", "ccpa"],
        "encryption": ["encrypt", "decrypt", "hash", "aes"],
        "deletion": ["delete", "remove", "purge", "anonymize"],
        "retention": ["retention", "expire", "ttl", "archive"],
    }

    def __init__(self, github_client: GitHubClient):
        self.github = github_client

    async def analyze(self, repository: Repository) -> dict[str, Any]:
        """Perform full analysis of a repository."""
        logger.info(f"Analyzing repository: {repository.full_name}")

        owner, repo = repository.full_name.split("/")

        repo_info = await self.github.get_repository(owner, repo)
        tree = await self.github.get_repository_tree(owner, repo)
        structure = self._analyze_structure(tree)
        relevant_files = self._identify_relevant_files(tree)
        languages = self._extract_languages(tree)

        file_samples = {}
        for file_info in relevant_files[:20]:
            try:
                file = await self.github.get_file_content(owner, repo, file_info["path"])
                file_samples[file.path] = file.content
            except Exception as e:
                logger.warning(f"Could not fetch {file_info['path']}: {e}")

        keyword_findings = self._analyze_content(file_samples)

        return {
            "repository": {
                "full_name": repository.full_name,
                "default_branch": repo_info.get("default_branch", "main"),
                "primary_language": repo_info.get("language"),
                "size": repo_info.get("size"),
            },
            "structure": structure,
            "languages": languages,
            "file_count": len(tree),
            "relevant_files": relevant_files,
            "keyword_findings": keyword_findings,
            "analyzed_at": datetime.now(UTC).isoformat(),
        }

    def _analyze_structure(self, tree: list[dict]) -> dict[str, Any]:
        """Analyze repository structure."""
        structure = {"directories": [], "file_types": {}, "key_directories": {}}
        key_dirs = ["src", "app", "lib", "api", "services", "models", "tests"]

        for item in tree:
            if item["type"] == "tree":
                structure["directories"].append(item["path"])
                if item["path"].split("/")[0] in key_dirs:
                    structure["key_directories"][item["path"]] = True
            else:
                ext = item["path"].rsplit(".", 1)[-1] if "." in item["path"] else "none"
                structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1

        return structure

    def _identify_relevant_files(self, tree: list[dict]) -> list[dict]:
        """Identify files likely to contain compliance-relevant code."""
        relevant = []

        for item in tree:
            if item["type"] != "blob":
                continue

            path = item["path"].lower()
            relevance_score = 0
            categories = []

            for category, patterns in self.COMPLIANCE_PATTERNS.items():
                for pattern in patterns:
                    pattern = pattern.lower().replace("**", "").replace("*", "")
                    if pattern in path:
                        relevance_score += 1
                        categories.append(category)
                        break

            for category, keywords in self.COMPLIANCE_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in path:
                        relevance_score += 0.5
                        if category not in categories:
                            categories.append(category)
                        break

            if relevance_score > 0:
                relevant.append({
                    "path": item["path"],
                    "sha": item["sha"],
                    "size": item.get("size", 0),
                    "relevance_score": relevance_score,
                    "categories": categories,
                })

        relevant.sort(key=lambda x: x["relevance_score"], reverse=True)
        return relevant

    def _extract_languages(self, tree: list[dict]) -> list[str]:
        """Extract programming languages from file extensions."""
        extension_map = {
            "py": "Python", "js": "JavaScript", "ts": "TypeScript",
            "tsx": "TypeScript", "java": "Java", "go": "Go",
            "rb": "Ruby", "php": "PHP", "cs": "C#", "rs": "Rust",
        }

        language_counts = {}
        for item in tree:
            if item["type"] == "blob" and "." in item["path"]:
                ext = item["path"].rsplit(".", 1)[-1].lower()
                if ext in extension_map:
                    lang = extension_map[ext]
                    language_counts[lang] = language_counts.get(lang, 0) + 1

        sorted_langs = sorted(language_counts.items(), key=lambda x: x[1], reverse=True)
        return [lang for lang, _ in sorted_langs]

    def _analyze_content(self, file_samples: dict[str, str]) -> dict[str, list[dict]]:
        """Analyze file contents for compliance keywords."""
        findings = {}

        for path, content in file_samples.items():
            content_lower = content.lower()

            for category, keywords in self.COMPLIANCE_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in content_lower:
                        if category not in findings:
                            findings[category] = []

                        lines = content.split("\n")
                        for i, line in enumerate(lines, 1):
                            if keyword in line.lower():
                                findings[category].append({
                                    "file": path,
                                    "line": i,
                                    "keyword": keyword,
                                    "context": line.strip()[:100],
                                })

        return findings


async def analyze_repository(repository: Repository, access_token: str) -> dict[str, Any]:
    """Convenience function to analyze a repository."""
    client = await get_github_client(access_token)
    async with client:
        analyzer = RepositoryAnalyzer(client)
        return await analyzer.analyze(repository)
