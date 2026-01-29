# Contributing to ComplianceAgent

First off, thank you for considering contributing to ComplianceAgent! 🎉

This document provides guidelines for contributing to the project. Following these guidelines helps communicate that you respect the time of the developers managing and developing this open source project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Commit Messages](#commit-messages)
- [Architecture Overview](#architecture-overview)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker and Docker Compose
- Git
- [uv](https://github.com/astral-sh/uv) (recommended for Python dependency management)

### Quick Start

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/complianceagent.git
   cd complianceagent
   ```

2. **Install dependencies**
   ```bash
   make install
   ```

3. **Install pre-commit hooks**
   ```bash
   make install-hooks
   ```

4. **Start development infrastructure**
   ```bash
   make dev
   ```

5. **Run the application**
   ```bash
   # Terminal 1: Backend
   make run-backend
   
   # Terminal 2: Frontend
   make run-frontend
   
   # Terminal 3 (optional): Workers
   make run-workers
   ```

6. **Verify everything works**
   ```bash
   make test
   make lint
   ```

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

When creating a bug report, please include:
- A clear and descriptive title
- Steps to reproduce the behavior
- Expected vs actual behavior
- Screenshots if applicable
- Environment details (OS, Python version, etc.)

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.yml).

### 💡 Suggesting Features

Feature suggestions are welcome! Please:
- Check if the feature has already been requested
- Describe your use case clearly
- Explain why this feature would be useful

Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.yml).

### 📖 Improving Documentation

Documentation improvements are always welcome:
- Fix typos or clarify existing documentation
- Add examples or tutorials
- Improve API documentation
- Translate documentation

### 🔧 Contributing Code

#### Good First Issues

Look for issues labeled [`good first issue`](https://github.com/josedab/complianceagent/labels/good%20first%20issue) - these are specifically chosen for newcomers.

#### Areas Needing Help

- Additional regulatory framework implementations (PCI-DSS, SOX, etc.)
- Frontend accessibility improvements
- Test coverage improvements
- Performance optimizations
- CI/CD improvements

## Development Setup

### Backend Setup

```bash
cd backend

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Run backend
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Running Tests

```bash
# All tests
make test

# Backend only
make test-backend

# Frontend only
make test-frontend

# With coverage
cd backend && pytest --cov=app --cov-report=html
```

### Code Quality Tools

```bash
# Lint all code
make lint

# Format code
make format

# Type checking
make type-check

# Security scanning
make security-check

# Run all checks (pre-commit)
make pre-commit
```

## Development Workflow

### Branch Naming

Use descriptive branch names with prefixes:

- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test improvements
- `ci/` - CI/CD changes
- `chore/` - Maintenance tasks

Examples:
- `feat/add-pci-dss-framework`
- `fix/auth-token-expiry`
- `docs/improve-api-examples`

### Making Changes

1. **Create a branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes**
   - Write clean, readable code
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   make test
   make lint
   make type-check
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

5. **Push and create PR**
   ```bash
   git push origin feat/your-feature-name
   ```

## Pull Request Process

### Before Submitting

1. ✅ All tests pass (`make test`)
2. ✅ Code is formatted (`make format`)
3. ✅ Linting passes (`make lint`)
4. ✅ Type checking passes (`make type-check`)
5. ✅ Documentation is updated if needed
6. ✅ Commits follow conventional commit format

### PR Guidelines

- Fill out the PR template completely
- Link related issues
- Provide a clear description of changes
- Add screenshots for UI changes
- Request review from maintainers

### Review Process

1. Automated checks must pass
2. At least one maintainer review required
3. Address any review comments
4. Maintainer will merge when ready

### After Merge

- Delete your branch
- Pull the latest main branch
- Update your fork

## Style Guidelines

### Python (Backend)

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting.

```python
# Good: Type hints everywhere
def process_regulation(
    regulation_id: UUID,
    options: ProcessOptions | None = None,
) -> ProcessingResult:
    """Process a regulation and extract requirements.
    
    Args:
        regulation_id: The unique identifier of the regulation.
        options: Optional processing configuration.
    
    Returns:
        The processing result with extracted requirements.
    
    Raises:
        RegulationNotFoundError: If the regulation doesn't exist.
    """
    ...

# Good: Use Pydantic for data models
class RegulationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    jurisdiction: str
    effective_date: date
```

Key guidelines:
- Use type hints for all function signatures
- Write docstrings for public functions/classes
- Prefer composition over inheritance
- Use async/await consistently
- Follow PEP 8 naming conventions

### TypeScript (Frontend)

```typescript
// Good: Typed props and explicit return types
interface RegulationCardProps {
  regulation: Regulation;
  onSelect: (id: string) => void;
  isLoading?: boolean;
}

export function RegulationCard({
  regulation,
  onSelect,
  isLoading = false,
}: RegulationCardProps): JSX.Element {
  // ...
}
```

Key guidelines:
- Use TypeScript strict mode
- Define interfaces for props and API responses
- Use React Server Components where appropriate
- Follow React best practices

### Documentation

- Use clear, concise language
- Include code examples
- Keep examples up to date
- Document edge cases

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `ci`: CI/CD changes
- `chore`: Maintenance tasks
- `perf`: Performance improvements

### Examples

```
feat(regulations): add EU AI Act parser

Add support for parsing EU AI Act documents from EUR-Lex.
Includes extraction of obligations and risk classifications.

Closes #123
```

```
fix(auth): handle expired refresh tokens gracefully

- Add automatic token refresh on 401 responses
- Redirect to login when refresh fails
- Add user-friendly error message

Fixes #456
```

## Architecture Overview

### Project Structure

```
complianceagent/
├── backend/           # Python FastAPI application
│   ├── app/
│   │   ├── api/       # API routes
│   │   ├── core/      # Configuration, security
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # Business logic
│   │   ├── agents/    # AI agent orchestration
│   │   └── workers/   # Celery background tasks
│   └── tests/
├── frontend/          # Next.js application
│   └── src/
│       ├── app/       # App Router pages
│       ├── components/# React components
│       └── lib/       # Utilities
├── docker/            # Docker configuration
├── infrastructure/    # Terraform/AWS
└── docs/             # Documentation
```

### Key Components

1. **Regulatory Monitoring** (`services/monitoring/`)
   - Web crawlers for regulatory sources
   - Change detection and alerts

2. **AI Processing** (`agents/`, `services/parsing/`)
   - Copilot SDK integration
   - Legal text parsing and extraction

3. **Codebase Mapping** (`services/mapping/`)
   - Repository analysis
   - Compliance gap detection

4. **Code Generation** (`services/generation/`)
   - AI-powered code suggestions
   - PR creation

### Database Schema

See `backend/alembic/versions/` for the current schema.

Key entities:
- `organizations` - Multi-tenant support
- `regulations` - Regulatory documents
- `requirements` - Extracted compliance requirements
- `codebase_mappings` - Code-to-requirement mappings
- `audit_trails` - Immutable audit logs

## Questions?

- Check the [documentation](README.md)
- Start a [discussion](https://github.com/josedab/complianceagent/discussions)
- Ask in the relevant issue

Thank you for contributing! 🙏
