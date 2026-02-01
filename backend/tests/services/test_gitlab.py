"""Tests for GitLab integration service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.gitlab import (
    GitLabClient,
    GitLabAnalyzer,
    GitLabRepository,
    GitLabFile,
    ComplianceFile,
    ComplianceFileType,
    RepositoryStructure,
)

pytestmark = pytest.mark.asyncio


class TestGitLabClient:
    """Test suite for GitLabClient."""

    @pytest.fixture
    def mock_response(self):
        """Create mock HTTP response."""
        response = MagicMock()
        response.status_code = 200
        return response

    @pytest.fixture
    def gitlab_client(self):
        """Create GitLab client instance."""
        return GitLabClient(
            token="test_token_123",
            base_url="https://gitlab.example.com",
        )

    def test_client_initialization(self, gitlab_client):
        """Test client initialization."""
        assert gitlab_client.token == "test_token_123"
        assert gitlab_client.base_url == "https://gitlab.example.com"
        assert gitlab_client.api_url == "https://gitlab.example.com/api/v4"

    def test_headers(self, gitlab_client):
        """Test request headers include token."""
        headers = gitlab_client._get_headers()
        
        assert headers["PRIVATE-TOKEN"] == "test_token_123"
        assert headers["Content-Type"] == "application/json"

    def test_headers_without_token(self):
        """Test headers without token."""
        client = GitLabClient()
        headers = client._get_headers()
        
        assert "PRIVATE-TOKEN" not in headers
        assert headers["Content-Type"] == "application/json"

    @patch("httpx.AsyncClient.request")
    async def test_get_project(self, mock_request, gitlab_client):
        """Test getting project details."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 12345,
            "name": "test-project",
            "path": "test-project",
            "path_with_namespace": "acme/test-project",
            "default_branch": "main",
            "visibility": "private",
            "description": "A test project",
            "web_url": "https://gitlab.example.com/acme/test-project",
            "ssh_url_to_repo": "git@gitlab.example.com:acme/test-project.git",
            "http_url_to_repo": "https://gitlab.example.com/acme/test-project.git",
        }
        mock_request.return_value = mock_response

        async with gitlab_client:
            project = await gitlab_client.get_project("acme/test-project")

        assert project.id == 12345
        assert project.name == "test-project"
        assert project.full_path == "acme/test-project"
        assert project.default_branch == "main"

    @patch("httpx.AsyncClient.request")
    async def test_get_project_languages(self, mock_request, gitlab_client):
        """Test getting project languages."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Python": 65.5,
            "JavaScript": 25.3,
            "HTML": 9.2,
        }
        mock_request.return_value = mock_response

        async with gitlab_client:
            languages = await gitlab_client.get_project_languages(12345)

        assert languages["Python"] == 65.5
        assert languages["JavaScript"] == 25.3

    @patch("httpx.AsyncClient.request")
    async def test_get_repository_tree(self, mock_request, gitlab_client):
        """Test getting repository file tree."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"path": "README.md", "name": "README.md", "type": "blob", "mode": "100644"},
            {"path": "src", "name": "src", "type": "tree", "mode": "040000"},
            {"path": "src/main.py", "name": "main.py", "type": "blob", "mode": "100644"},
        ]
        mock_request.return_value = mock_response

        async with gitlab_client:
            tree = await gitlab_client.get_repository_tree(12345, recursive=True)

        assert len(tree) == 3
        assert tree[0].path == "README.md"
        assert tree[0].type == "blob"
        assert tree[1].type == "tree"

    @patch("httpx.AsyncClient.request")
    async def test_get_file_content(self, mock_request, gitlab_client):
        """Test getting file content."""
        import base64
        
        content = "def main():\n    print('Hello')"
        encoded = base64.b64encode(content.encode()).decode()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "file_name": "main.py",
            "file_path": "src/main.py",
            "content": encoded,
            "encoding": "base64",
        }
        mock_request.return_value = mock_response

        async with gitlab_client:
            file_content = await gitlab_client.get_file_content(12345, "src/main.py")

        assert file_content == content

    @patch("httpx.AsyncClient.request")
    async def test_list_branches(self, mock_request, gitlab_client):
        """Test listing branches."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"name": "main", "protected": True},
            {"name": "develop", "protected": False},
            {"name": "feature/compliance", "protected": False},
        ]
        mock_request.return_value = mock_response

        async with gitlab_client:
            branches = await gitlab_client.list_branches(12345)

        assert len(branches) == 3
        assert branches[0]["name"] == "main"
        assert branches[0]["protected"] is True

    @patch("httpx.AsyncClient.request")
    async def test_list_commits(self, mock_request, gitlab_client):
        """Test listing commits."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "abc123",
                "title": "Initial commit",
                "author_name": "Test User",
                "created_at": "2026-01-28T10:00:00Z",
            },
            {
                "id": "def456",
                "title": "Add compliance checks",
                "author_name": "Test User",
                "created_at": "2026-01-27T10:00:00Z",
            },
        ]
        mock_request.return_value = mock_response

        async with gitlab_client:
            commits = await gitlab_client.list_commits(12345)

        assert len(commits) == 2
        assert commits[0]["id"] == "abc123"

    @patch("httpx.AsyncClient.request")
    async def test_create_merge_request(self, mock_request, gitlab_client):
        """Test creating merge request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "iid": 42,
            "title": "Compliance fix",
            "state": "opened",
            "web_url": "https://gitlab.example.com/acme/test-project/-/merge_requests/42",
        }
        mock_request.return_value = mock_response

        async with gitlab_client:
            mr = await gitlab_client.create_merge_request(
                project_id=12345,
                source_branch="compliance-fix",
                target_branch="main",
                title="Compliance fix",
                description="Fixes compliance gaps",
            )

        assert mr["iid"] == 42
        assert mr["state"] == "opened"

    @patch("httpx.AsyncClient.request")
    async def test_handle_404_error(self, mock_request, gitlab_client):
        """Test handling 404 not found error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_request.return_value = mock_response

        async with gitlab_client:
            with pytest.raises(ValueError, match="not found"):
                await gitlab_client.get_project("nonexistent/project")

    @patch("httpx.AsyncClient.request")
    async def test_handle_401_error(self, mock_request, gitlab_client):
        """Test handling 401 unauthorized error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_request.return_value = mock_response

        async with gitlab_client:
            with pytest.raises(ValueError, match="Authentication failed"):
                await gitlab_client.get_project(12345)


class TestGitLabAnalyzer:
    """Test suite for GitLabAnalyzer."""

    @pytest.fixture
    def mock_gitlab_client(self):
        """Create mock GitLab client."""
        client = AsyncMock()
        
        client.get_project = AsyncMock(return_value=GitLabRepository(
            id=12345,
            name="test-project",
            path="test-project",
            full_path="acme/test-project",
            default_branch="main",
            visibility="private",
            description="Test project",
            web_url="https://gitlab.example.com/acme/test-project",
            ssh_url="git@gitlab.example.com:acme/test-project.git",
            http_url="https://gitlab.example.com/acme/test-project.git",
        ))
        
        client.get_project_languages = AsyncMock(return_value={
            "Python": 70.0,
            "JavaScript": 30.0,
        })
        
        client.get_repository_tree = AsyncMock(return_value=[
            GitLabFile("README.md", "README.md", 1024, "blob", "100644"),
            GitLabFile("src/main.py", "main.py", 2048, "blob", "100644"),
            GitLabFile("src/auth/login.py", "login.py", 1500, "blob", "100644"),
            GitLabFile("src/data/user_handler.py", "user_handler.py", 3000, "blob", "100644"),
            GitLabFile("tests/test_main.py", "test_main.py", 500, "blob", "100644"),
            GitLabFile(".gitlab-ci.yml", ".gitlab-ci.yml", 800, "blob", "100644"),
            GitLabFile("Dockerfile", "Dockerfile", 400, "blob", "100644"),
        ])
        
        client.get_file_content = AsyncMock(return_value="# Test content")
        
        return client

    @pytest.fixture
    def analyzer(self, mock_gitlab_client):
        """Create GitLab analyzer instance."""
        return GitLabAnalyzer(client=mock_gitlab_client)

    async def test_analyze_repository(self, analyzer, mock_gitlab_client):
        """Test full repository analysis."""
        structure = await analyzer.analyze_repository("acme/test-project")

        assert structure.languages == {"Python": 70.0, "JavaScript": 30.0}
        assert structure.total_files == 7
        assert structure.has_tests is True
        assert structure.has_ci is True
        assert structure.has_docker is True

    async def test_detect_frameworks(self, analyzer):
        """Test framework detection."""
        file_paths = [
            "main.py",
            "requirements.txt",
            "app/main.py",
            "fastapi",
            "uvicorn",
        ]

        frameworks = analyzer._detect_frameworks(file_paths)

        assert "FastAPI" in frameworks

    async def test_find_compliance_files(self, analyzer, mock_gitlab_client):
        """Test finding compliance-relevant files."""
        tree = await mock_gitlab_client.get_repository_tree()
        
        compliance_files = await analyzer._find_compliance_files(
            12345,
            tree,
            "main",
        )

        # Should find auth/login.py (authentication) and user_handler.py (data handler)
        file_types = [f.file_type for f in compliance_files]
        assert ComplianceFileType.AUTHENTICATION in file_types or \
               ComplianceFileType.DATA_HANDLER in file_types

    async def test_analyze_compliance_file_data_handler(self, analyzer, mock_gitlab_client):
        """Test analyzing a data handler file."""
        mock_gitlab_client.get_file_content = AsyncMock(return_value="""
class UserHandler:
    def process_user(self, email, phone, address):
        # Handle user data
        self.store_pii(email, phone)
        
    def store_pii(self, email, phone):
        # Store in database
        pass
        """)

        compliance_file = ComplianceFile(
            path="src/data/user_handler.py",
            file_type=ComplianceFileType.DATA_HANDLER,
        )

        result = await analyzer.analyze_compliance_file(
            12345,
            compliance_file,
            "main",
        )

        assert result.content is not None
        assert result.analysis.get("has_pii_handling") is True
        assert "email" in result.analysis.get("patterns_found", [])

    async def test_analyze_compliance_file_encryption(self, analyzer, mock_gitlab_client):
        """Test analyzing an encryption file."""
        mock_gitlab_client.get_file_content = AsyncMock(return_value="""
from cryptography.fernet import Fernet
import bcrypt

def encrypt_data(data):
    key = Fernet.generate_key()
    f = Fernet(key)
    return f.encrypt(data.encode())

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        """)

        compliance_file = ComplianceFile(
            path="src/security/crypto.py",
            file_type=ComplianceFileType.ENCRYPTION,
        )

        result = await analyzer.analyze_compliance_file(
            12345,
            compliance_file,
            "main",
        )

        assert result.analysis.get("has_strong_crypto") is True
        patterns = result.analysis.get("patterns_found", [])
        assert "bcrypt" in patterns or "encrypt" in patterns

    async def test_analyze_compliance_file_authentication(self, analyzer, mock_gitlab_client):
        """Test analyzing an authentication file."""
        mock_gitlab_client.get_file_content = AsyncMock(return_value="""
import jwt
from pyotp import TOTP

def authenticate(username, password, otp=None):
    user = verify_credentials(username, password)
    if user.mfa_enabled and otp:
        totp = TOTP(user.mfa_secret)
        if not totp.verify(otp):
            raise AuthError("Invalid 2FA code")
    return create_jwt_token(user)
        """)

        compliance_file = ComplianceFile(
            path="src/auth/auth.py",
            file_type=ComplianceFileType.AUTHENTICATION,
        )

        result = await analyzer.analyze_compliance_file(
            12345,
            compliance_file,
            "main",
        )

        assert result.analysis.get("has_secure_auth") is True
        patterns = result.analysis.get("patterns_found", [])
        assert "mfa" in patterns or "2fa" in patterns or "totp" in patterns

    async def test_scan_for_sensitive_data(self, analyzer, mock_gitlab_client):
        """Test scanning for sensitive data."""
        mock_gitlab_client.get_repository_tree = AsyncMock(return_value=[
            GitLabFile(".env", ".env", 100, "blob", "100644"),
            GitLabFile("config.yaml", "config.yaml", 200, "blob", "100644"),
        ])
        
        mock_gitlab_client.get_file_content = AsyncMock(return_value="""
# Config file
API_KEY = "sk_test_FAKE_KEY_FOR_TESTING_ONLY"
DATABASE_URL = "postgres://user:password123@localhost/db"
SECRET = "my_super_secret_value"
        """)

        findings = await analyzer.scan_for_sensitive_data(12345)

        # Should find at least some sensitive patterns
        total_findings = sum(len(v) for v in findings.values())
        assert total_findings > 0

    async def test_skip_vendor_directories(self, analyzer, mock_gitlab_client):
        """Test that vendor directories are skipped."""
        mock_gitlab_client.get_repository_tree = AsyncMock(return_value=[
            GitLabFile("src/auth.py", "auth.py", 1000, "blob", "100644"),
            GitLabFile("node_modules/pkg/auth.js", "auth.js", 500, "blob", "100644"),
            GitLabFile("vendor/lib/auth.go", "auth.go", 600, "blob", "100644"),
        ])

        structure = await analyzer.analyze_repository(12345)

        # node_modules and vendor should be skipped for compliance files
        paths = [f.path for f in structure.compliance_files]
        assert not any("node_modules" in p for p in paths)
        assert not any("vendor" in p for p in paths)


class TestComplianceFileType:
    """Test ComplianceFileType enumeration."""

    def test_all_types_defined(self):
        """Test all compliance file types are defined."""
        expected_types = [
            "PRIVACY_POLICY",
            "TERMS_OF_SERVICE",
            "DATA_HANDLER",
            "AUTHENTICATION",
            "ENCRYPTION",
            "LOGGING",
            "CONFIGURATION",
            "INFRASTRUCTURE",
            "SECURITY",
            "API_ENDPOINT",
            "DATABASE",
            "CONSENT",
        ]

        for type_name in expected_types:
            assert hasattr(ComplianceFileType, type_name)

    def test_type_values(self):
        """Test type values are lowercase strings."""
        for file_type in ComplianceFileType:
            assert file_type.value == file_type.name.lower()
