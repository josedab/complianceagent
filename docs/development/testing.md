# Testing Guide

This guide covers the testing strategies, patterns, and best practices for ComplianceAgent.

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Structure](#test-structure)
- [Backend Testing](#backend-testing)
- [Frontend Testing](#frontend-testing)
- [Integration Testing](#integration-testing)
- [End-to-End Testing](#end-to-end-testing)
- [Test Data Management](#test-data-management)
- [CI/CD Integration](#cicd-integration)
- [Coverage Goals](#coverage-goals)

---

## Testing Philosophy

We follow the **Testing Pyramid** approach:

```
         ┌─────────┐
         │  E2E    │  ← Few, slow, high-value
         └────┬────┘
        ┌─────┴─────┐
        │Integration│  ← Moderate, test boundaries
        └─────┬─────┘
    ┌─────────┴─────────┐
    │       Unit        │  ← Many, fast, isolated
    └───────────────────┘
```

**Key Principles:**
- **Test behavior, not implementation** - Tests should survive refactoring
- **Arrange-Act-Assert** - Clear test structure
- **One assertion per test** (when practical) - Clear failure messages
- **Fast feedback** - Keep test suite fast
- **Deterministic** - No flaky tests

---

## Test Structure

```
complianceagent/
├── backend/
│   └── tests/
│       ├── conftest.py           # Shared fixtures
│       ├── test_api_auth.py      # API endpoint tests
│       ├── test_api_regulations.py
│       ├── test_services_*.py    # Service layer tests
│       ├── test_agents_*.py      # AI agent tests
│       ├── test_models_*.py      # Model tests
│       └── integration/          # Integration tests
│           └── test_workflow.py
│
├── frontend/
│   └── tests/
│       ├── components/           # Component tests
│       ├── hooks/               # Hook tests
│       ├── lib/                 # Utility tests
│       └── e2e/                 # E2E tests (Playwright)
```

---

## Backend Testing

### Setup

```bash
cd backend
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# Run specific tests
pytest tests/test_api_auth.py -v
pytest tests/test_api_auth.py::test_login_success -v -s

# Parallel execution
pytest tests/ -n auto
```

### Shared Fixtures

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.main import app
from app.core.security import create_access_token

# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Create test database session."""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture
async def client(db_session):
    """Create test HTTP client with dependency overrides."""
    from app.core.database import get_db
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
    from app.models import User, Organization
    from app.core.security import get_password_hash
    
    org = Organization(name="Test Org", slug="test-org")
    db_session.add(org)
    await db_session.commit()
    
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("TestPassword123"),
        full_name="Test User",
        organization_id=org.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers."""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}
```

### API Endpoint Tests

```python
# tests/test_api_auth.py
import pytest
from httpx import AsyncClient


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "password": "SecurePassword123!",
                "full_name": "New User",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@example.com"
        assert "id" in data
        assert "password" not in data  # Should not expose password
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with existing email fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "SecurePassword123!",
                "full_name": "Duplicate User",
            },
        )
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login returns tokens."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password fails."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "WrongPassword",
            },
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_me_authenticated(self, client: AsyncClient, auth_headers):
        """Test /me endpoint with valid token."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_me_unauthenticated(self, client: AsyncClient):
        """Test /me endpoint without token fails."""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
```

### Service Layer Tests

```python
# tests/test_services_regulation.py
import pytest
from uuid import uuid4
from datetime import date

from app.services.regulation import RegulationService
from app.schemas.regulation import RegulationCreate


class TestRegulationService:
    """Test RegulationService business logic."""
    
    @pytest.fixture
    def service(self, db_session):
        return RegulationService(db_session)
    
    @pytest.fixture
    def regulation_data(self):
        return RegulationCreate(
            name="Test Regulation",
            framework="gdpr",
            jurisdiction="eu",
            effective_date=date(2024, 1, 1),
        )
    
    @pytest.mark.asyncio
    async def test_create_regulation(self, service, regulation_data, test_user):
        """Test creating a regulation."""
        regulation = await service.create(
            data=regulation_data,
            organization_id=test_user.organization_id,
        )
        
        assert regulation.id is not None
        assert regulation.name == "Test Regulation"
        assert regulation.framework == "gdpr"
        assert regulation.organization_id == test_user.organization_id
    
    @pytest.mark.asyncio
    async def test_list_regulations_filtered(self, service, test_user, db_session):
        """Test listing regulations with framework filter."""
        # Create test regulations
        for framework in ["gdpr", "gdpr", "ccpa"]:
            await service.create(
                data=RegulationCreate(
                    name=f"Test {framework.upper()}",
                    framework=framework,
                    jurisdiction="test",
                    effective_date=date(2024, 1, 1),
                ),
                organization_id=test_user.organization_id,
            )
        
        # Filter by framework
        result = await service.list(
            organization_id=test_user.organization_id,
            framework="gdpr",
        )
        
        assert result.total == 2
        assert all(r.framework == "gdpr" for r in result.items)
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_regulation(self, service, test_user):
        """Test getting a non-existent regulation raises error."""
        from app.core.exceptions import NotFoundError
        
        with pytest.raises(NotFoundError):
            await service.get(
                regulation_id=uuid4(),
                organization_id=test_user.organization_id,
            )
```

### AI Agent Tests

```python
# tests/test_agents_copilot.py
import pytest
from unittest.mock import AsyncMock, patch

from app.agents.copilot import CopilotClient


class TestCopilotClient:
    """Test Copilot SDK client."""
    
    @pytest.fixture
    def client(self):
        return CopilotClient(
            api_key="test-key",
            base_url="https://api.test.com",
        )
    
    @pytest.mark.asyncio
    async def test_analyze_legal_text_success(self, client):
        """Test successful legal text analysis."""
        mock_response = {
            "requirements": [
                {
                    "title": "Data Encryption",
                    "obligation_type": "must",
                    "article": "Article 32",
                }
            ]
        }
        
        with patch.object(client, "_call_api", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_response
            
            result = await client.analyze_legal_text(
                content="GDPR Article 32 requires encryption...",
                framework="gdpr",
            )
            
            assert len(result) == 1
            assert result[0].title == "Data Encryption"
            mock_api.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_legal_text_retry_on_failure(self, client):
        """Test retry logic on transient failures."""
        with patch.object(client, "_call_api", new_callable=AsyncMock) as mock_api:
            # Fail twice, succeed on third try
            mock_api.side_effect = [
                Exception("API Error"),
                Exception("API Error"),
                {"requirements": []},
            ]
            
            result = await client.analyze_legal_text(
                content="Test content",
                framework="gdpr",
            )
            
            assert result == []
            assert mock_api.call_count == 3
```

---

## Frontend Testing

### Setup

```bash
cd frontend

# Run all tests
npm test

# Watch mode
npm run test:watch

# Coverage report
npm test -- --coverage
```

### Component Tests

```tsx
// tests/components/regulation-card.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { RegulationCard } from '@/components/regulations/regulation-card';

const mockRegulation = {
  id: '1',
  name: 'GDPR',
  framework: 'gdpr',
  jurisdiction: 'EU',
  status: 'active',
  requirementsCount: 147,
  effectiveDate: '2018-05-25',
};

describe('RegulationCard', () => {
  it('renders regulation name and details', () => {
    render(<RegulationCard regulation={mockRegulation} />);
    
    expect(screen.getByText('GDPR')).toBeInTheDocument();
    expect(screen.getByText(/gdpr.*EU/i)).toBeInTheDocument();
    expect(screen.getByText('147 requirements')).toBeInTheDocument();
  });
  
  it('displays status badge with correct variant', () => {
    render(<RegulationCard regulation={mockRegulation} />);
    
    const badge = screen.getByText('active');
    expect(badge).toHaveClass('bg-green'); // Or appropriate class
  });
  
  it('calls onSelect when clicked', () => {
    const onSelect = jest.fn();
    render(<RegulationCard regulation={mockRegulation} onSelect={onSelect} />);
    
    fireEvent.click(screen.getByRole('article'));
    
    expect(onSelect).toHaveBeenCalledWith('1');
  });
  
  it('does not break when onSelect is not provided', () => {
    render(<RegulationCard regulation={mockRegulation} />);
    
    expect(() => {
      fireEvent.click(screen.getByRole('article'));
    }).not.toThrow();
  });
  
  it('applies custom className', () => {
    render(
      <RegulationCard 
        regulation={mockRegulation} 
        className="custom-class" 
      />
    );
    
    expect(screen.getByRole('article')).toHaveClass('custom-class');
  });
});
```

### Hook Tests

```tsx
// tests/hooks/useRegulations.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useRegulations } from '@/hooks/useRegulations';

// Mock the API module
jest.mock('@/lib/api', () => ({
  api: {
    regulations: {
      list: jest.fn(),
    },
  },
}));

import { api } from '@/lib/api';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('useRegulations', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  it('fetches regulations on mount', async () => {
    const mockData = {
      items: [{ id: '1', name: 'GDPR' }],
      total: 1,
    };
    (api.regulations.list as jest.Mock).mockResolvedValue(mockData);
    
    const { result } = renderHook(() => useRegulations(), {
      wrapper: createWrapper(),
    });
    
    // Initially loading
    expect(result.current.isLoading).toBe(true);
    
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    expect(result.current.data).toEqual(mockData);
    expect(api.regulations.list).toHaveBeenCalledTimes(1);
  });
  
  it('passes filters to API', async () => {
    (api.regulations.list as jest.Mock).mockResolvedValue({ items: [], total: 0 });
    
    renderHook(() => useRegulations({ framework: 'gdpr' }), {
      wrapper: createWrapper(),
    });
    
    await waitFor(() => {
      expect(api.regulations.list).toHaveBeenCalledWith({ framework: 'gdpr' });
    });
  });
});
```

### Utility Tests

```tsx
// tests/lib/utils.test.ts
import { cn, formatDate, truncate } from '@/lib/utils';

describe('cn (className merger)', () => {
  it('merges class names', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });
  
  it('handles conditional classes', () => {
    expect(cn('base', true && 'active', false && 'disabled')).toBe('base active');
  });
  
  it('merges Tailwind classes correctly', () => {
    expect(cn('p-4', 'p-2')).toBe('p-2'); // Later class wins
  });
});

describe('formatDate', () => {
  it('formats ISO date string', () => {
    expect(formatDate('2024-01-15T10:30:00Z')).toBe('Jan 15, 2024');
  });
  
  it('returns empty string for invalid date', () => {
    expect(formatDate('invalid')).toBe('');
  });
});

describe('truncate', () => {
  it('truncates long strings', () => {
    expect(truncate('Hello World', 5)).toBe('Hello...');
  });
  
  it('does not truncate short strings', () => {
    expect(truncate('Hi', 10)).toBe('Hi');
  });
});
```

---

## Integration Testing

```python
# backend/tests/integration/test_compliance_workflow.py
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestComplianceWorkflow:
    """Test complete compliance workflow."""
    
    @pytest.mark.asyncio
    async def test_full_compliance_analysis(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_organization,
    ):
        """Test: Add repo → Analyze → View status → Generate fix."""
        
        # Step 1: Add a repository
        repo_response = await client.post(
            "/api/v1/repositories",
            headers=auth_headers,
            json={
                "full_name": "test/repo",
                "provider": "github",
            },
        )
        assert repo_response.status_code == 201
        repo_id = repo_response.json()["id"]
        
        # Step 2: Trigger analysis
        analysis_response = await client.post(
            f"/api/v1/repositories/{repo_id}/analyze",
            headers=auth_headers,
            json={"frameworks": ["gdpr"]},
        )
        assert analysis_response.status_code == 202
        
        # Step 3: Wait for analysis (in real test, would poll)
        # ...
        
        # Step 4: Check compliance status
        status_response = await client.get(
            "/api/v1/compliance/status",
            headers=auth_headers,
            params={"repository_id": repo_id},
        )
        assert status_response.status_code == 200
        status = status_response.json()
        assert "overall_score" in status
        
        # Step 5: Generate fix for a gap
        if status.get("by_framework", {}).get("gdpr", {}).get("critical_gaps", 0) > 0:
            # Get first mapping with gap
            # ... generate fix
            pass
```

---

## End-to-End Testing

### Playwright Setup

```typescript
// frontend/tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('user can log in and see dashboard', async ({ page }) => {
    // Navigate to login
    await page.goto('/login');
    
    // Fill login form
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'TestPassword123');
    await page.click('button[type="submit"]');
    
    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('h1')).toContainText('Dashboard');
  });
  
  test('shows error for invalid credentials', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('input[name="email"]', 'wrong@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('[role="alert"]')).toContainText('Invalid credentials');
  });
});
```

### Running E2E Tests

```bash
cd frontend

# Install Playwright browsers
npx playwright install

# Run E2E tests
npm run test:e2e

# With UI mode
npm run test:e2e -- --ui

# Specific browser
npm run test:e2e -- --project=chromium
```

---

## Test Data Management

### Factories

```python
# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from app.models import User, Organization, Regulation

class OrganizationFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Organization
    
    name = factory.Sequence(lambda n: f"Organization {n}")
    slug = factory.Sequence(lambda n: f"org-{n}")

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    full_name = factory.Faker("name")
    hashed_password = "hashed_test_password"
    organization = factory.SubFactory(OrganizationFactory)

class RegulationFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Regulation
    
    name = factory.Sequence(lambda n: f"Regulation {n}")
    framework = factory.Iterator(["gdpr", "ccpa", "hipaa"])
    jurisdiction = factory.Iterator(["eu", "us-ca", "us-federal"])
    effective_date = factory.Faker("date_object")
```

---

## CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install uv
          uv pip install -e ".[dev]"
      
      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        run: cd frontend && npm ci
      
      - name: Run tests
        run: cd frontend && npm test -- --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: frontend/coverage/lcov.info
```

---

## Coverage Goals

| Component | Target | Critical Paths |
|-----------|--------|----------------|
| Backend API | 80% | Auth, Compliance |
| Backend Services | 85% | All business logic |
| Backend Agents | 70% | Happy paths |
| Frontend Components | 75% | Interactive components |
| Frontend Hooks | 80% | Data fetching |
| E2E | Key flows | Auth, Analysis, Dashboard |

### Viewing Coverage

```bash
# Backend
cd backend
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Frontend
cd frontend
npm test -- --coverage
open coverage/lcov-report/index.html
```

---

## Best Practices Checklist

- [ ] Tests are independent (no shared state between tests)
- [ ] Tests are deterministic (same result every run)
- [ ] Tests use descriptive names (`test_login_with_invalid_email_returns_400`)
- [ ] Tests follow Arrange-Act-Assert pattern
- [ ] Mocks are reset between tests
- [ ] No hardcoded delays (`time.sleep`) - use proper waiting
- [ ] Tests don't depend on external services (use mocks)
- [ ] Coverage reports are generated in CI
