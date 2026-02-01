"""Test configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models import User, Organization

# Test database URL (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async database engine for tests."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_organization(db_session: AsyncSession) -> Organization:
    """Create test organization."""
    org = Organization(
        id=uuid4(),
        name="Test Organization",
        slug="test-org",
        plan="professional",
        settings={"industry": "technology"},
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession, test_organization: Organization) -> User:
    """Create test user."""
    from app.models.organization import OrganizationMember, MemberRole

    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    # Create organization membership
    membership = OrganizationMember(
        id=uuid4(),
        organization_id=test_organization.id,
        user_id=user.id,
        role=MemberRole.ADMIN,
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def auth_headers(test_user: User, test_organization: Organization) -> dict[str, str]:
    """Create authentication headers for test user."""
    token = create_access_token(
        data={"sub": str(test_user.id), "org": str(test_organization.id)}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_copilot_client() -> MagicMock:
    """Create mock Copilot client."""
    client = MagicMock()
    client.chat = AsyncMock(return_value="Mock AI response")
    client.analyze_legal_text = AsyncMock(return_value={
        "requirements": [
            {
                "obligation_type": "must",
                "subject": "data controller",
                "action": "provide information",
                "scope": {"data_types": ["personal data"]},
                "confidence": 0.95,
            }
        ]
    })
    client.map_to_code = AsyncMock(return_value={
        "mappings": [
            {
                "file": "src/api/users.py",
                "function": "get_user_data",
                "compliance_status": "compliant",
                "confidence": 0.88,
            }
        ]
    })
    client.generate_code = AsyncMock(return_value={
        "code": "def handle_dsar(user_id: str):\n    pass",
        "explanation": "DSAR handler implementation",
        "tests": "def test_dsar():\n    pass",
    })
    return client


@pytest.fixture
def mock_github_client() -> MagicMock:
    """Create mock GitHub client."""
    client = MagicMock()
    client.get_repository = AsyncMock(return_value={
        "id": 12345,
        "full_name": "test/repo",
        "default_branch": "main",
    })
    client.get_file_content = AsyncMock(return_value="# Test file content")
    client.list_files = AsyncMock(return_value=[
        {"path": "src/main.py", "type": "file"},
        {"path": "src/api/users.py", "type": "file"},
    ])
    client.create_branch = AsyncMock(return_value={"ref": "refs/heads/compliance-fix"})
    client.create_pull_request = AsyncMock(return_value={
        "number": 123,
        "html_url": "https://github.com/test/repo/pull/123",
    })
    return client
