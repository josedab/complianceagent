---
sidebar_position: 9
title: Contributing
description: How to contribute to ComplianceAgent
---

# Contributing to ComplianceAgent

Thank you for your interest in contributing to ComplianceAgent! This guide will help you get started.

## Ways to Contribute

### 🐛 Report Bugs

Found a bug? Help us fix it:

1. Search [existing issues](https://github.com/complianceagent/complianceagent/issues) to avoid duplicates
2. Create a [new issue](https://github.com/complianceagent/complianceagent/issues/new?template=bug_report.md)
3. Include:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, version, etc.)

### 💡 Request Features

Have an idea for a new feature?

1. Check [existing feature requests](https://github.com/complianceagent/complianceagent/issues?q=is%3Aissue+label%3Aenhancement)
2. Open a [feature request](https://github.com/complianceagent/complianceagent/issues/new?template=feature_request.md)
3. Describe the use case and proposed solution

### 📖 Improve Documentation

Documentation improvements are always welcome:

- Fix typos and clarify wording
- Add examples and use cases
- Translate to other languages
- Improve tutorials and guides

### 🔧 Submit Code

Ready to contribute code? Here's how:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- Make

### Quick Start

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/complianceagent.git
cd complianceagent

# Set up backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Set up frontend
cd ../frontend
npm install

# Start dependencies
docker compose -f docker/docker-compose.dev.yml up -d

# Run backend
cd ../backend
uvicorn app.main:app --reload

# Run frontend (new terminal)
cd frontend
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# With coverage
pytest --cov=app --cov-report=html

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

### Code Quality

```bash
# Backend linting
cd backend
ruff check .
ruff format .
mypy .

# Frontend linting
cd frontend
npm run lint
npm run type-check
```

## Pull Request Process

### 1. Create a Branch

```bash
# Feature branch
git checkout -b feature/your-feature-name

# Bug fix branch
git checkout -b fix/issue-number-description

# Documentation branch
git checkout -b docs/what-you-changed
```

### 2. Make Changes

- Write clean, readable code
- Follow existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Commit Guidelines

We use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format
<type>(<scope>): <description>

# Examples
feat(api): add endpoint for bulk issue updates
fix(scanner): handle empty repositories gracefully
docs(readme): update installation instructions
test(auth): add tests for token refresh
chore(deps): update FastAPI to 0.109
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `chore`: Maintenance
- `refactor`: Code change that neither fixes nor adds features

### 4. Submit PR

1. Push your branch:
```bash
git push origin feature/your-feature-name
```

2. Open a pull request on GitHub

3. Fill out the PR template:
   - Description of changes
   - Related issues
   - Testing performed
   - Screenshots (if UI changes)

### 5. Review Process

- Maintainers will review your PR
- Address any requested changes
- Once approved, a maintainer will merge

## Code Style

### Python (Backend)

```python
# Use type hints
def get_user(user_id: str) -> User | None:
    """Get user by ID.
    
    Args:
        user_id: The unique user identifier.
        
    Returns:
        User object if found, None otherwise.
    """
    return db.query(User).filter(User.id == user_id).first()

# Use async/await for I/O operations
async def scan_repository(repo_id: str) -> ScanResult:
    async with get_db_session() as session:
        repo = await session.get(Repository, repo_id)
        return await scanner.scan(repo)

# Use Pydantic for data validation
class CreateIssueRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    severity: Severity
    framework: str
```

### TypeScript (Frontend)

```typescript
// Use explicit types
interface ComplianceIssue {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  status: IssueStatus;
}

// Use functional components
function IssueCard({ issue }: { issue: ComplianceIssue }) {
  return (
    <Card>
      <CardTitle>{issue.title}</CardTitle>
      <Badge variant={getSeverityVariant(issue.severity)}>
        {issue.severity}
      </Badge>
    </Card>
  );
}

// Use hooks appropriately
function useComplianceStatus(repoId: string) {
  return useQuery({
    queryKey: ['compliance', repoId],
    queryFn: () => api.getComplianceStatus(repoId),
  });
}
```

## Adding a New Framework

Want to add support for a new regulatory framework?

### 1. Create Framework Definition

```yaml
# shared/frameworks/new_framework.yml
id: new_framework
name: "New Framework Name"
short_name: "NFN"
jurisdiction: "EU"
category: "privacy"
effective_date: "2024-01-01"

requirements:
  - id: nfn_1
    title: "Requirement 1"
    article: "Article 1"
    description: "Description of the requirement"
    priority: high
    
    detection_patterns:
      - pattern: "personal_data.*without.*consent"
        language: all
        
    remediation:
      guidance:
        - "Implement consent collection"
        - "Add data subject rights"
      templates:
        - nfn-consent-handler
```

### 2. Add Detection Logic

```python
# backend/app/scanners/frameworks/new_framework.py
from app.scanners.base import FrameworkScanner

class NewFrameworkScanner(FrameworkScanner):
    framework_id = "new_framework"
    
    def get_rules(self) -> list[Rule]:
        return [
            Rule(
                id="nfn_1",
                pattern=r"personal_data.*without.*consent",
                severity="high",
                message="Personal data processing without consent check"
            ),
        ]
```

### 3. Add Templates

```python
# shared/templates/nfn-consent-handler/
# template.py, template.ts, etc.
```

### 4. Add Tests

```python
# backend/tests/scanners/test_new_framework.py
def test_detects_consent_violation():
    code = '''
    def process_user(user):
        save_personal_data(user.email)  # No consent check
    '''
    scanner = NewFrameworkScanner()
    issues = scanner.scan(code)
    assert len(issues) == 1
    assert issues[0].requirement_id == "nfn_1"
```

### 5. Update Documentation

Add documentation in `website/docs/frameworks/new-framework.md`.

## Community

### Code of Conduct

We follow the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you agree to uphold this code.

### Getting Help

- 💬 [GitHub Discussions](https://github.com/complianceagent/complianceagent/discussions) - Questions and discussions
- 🐛 [GitHub Issues](https://github.com/complianceagent/complianceagent/issues) - Bug reports
- 📧 [maintainers@complianceagent.io](mailto:maintainers@complianceagent.io) - Private concerns

### Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md`
- Release notes
- Our website

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for helping make ComplianceAgent better! 🎉
