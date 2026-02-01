# ComplianceAgent Examples

This directory contains example code demonstrating how to integrate with ComplianceAgent.

## Available Examples

### Python SDK Example

**File**: `python_sdk_example.py`

A comprehensive example showing how to use the ComplianceAgent API from Python.

**Features demonstrated**:
- Client initialization and authentication
- Health checks
- Listing regulations and repositories
- Creating regulations and adding repositories
- Triggering compliance scans
- Generating and applying compliance fixes
- Audit trail access
- IDE integration endpoints

**Prerequisites**:
```bash
pip install httpx python-dotenv
```

**Usage**:
```bash
# Set environment variables
export COMPLIANCEAGENT_API_URL=http://localhost:8000
export COMPLIANCEAGENT_API_KEY=your-api-key

# Or create a .env file
echo "COMPLIANCEAGENT_API_URL=http://localhost:8000" > .env
echo "COMPLIANCEAGENT_API_KEY=your-api-key" >> .env

# Run the example
python python_sdk_example.py
```

## CI/CD Integration

Use the Python client in your CI/CD pipeline:

```python
# ci_compliance_check.py
import asyncio
import sys
from python_sdk_example import ComplianceAgentClient


async def check_compliance():
    async with ComplianceAgentClient() as client:
        # Get repository status
        status = await client.get_repository_status("your-repo-id")

        if status["compliance_percentage"] < 100:
            print(f"Compliance: {status['compliance_percentage']}%")
            print("Non-compliant items:")
            for issue in status.get("issues", []):
                print(f"  - {issue['requirement']}: {issue['file']}")
            sys.exit(1)

        print("✓ Repository is fully compliant")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(check_compliance())
```

### GitHub Actions Integration

```yaml
# .github/workflows/compliance.yml
name: Compliance Check

on: [push, pull_request]

jobs:
  compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install httpx python-dotenv

      - name: Run compliance check
        env:
          COMPLIANCEAGENT_API_URL: ${{ secrets.COMPLIANCEAGENT_API_URL }}
          COMPLIANCEAGENT_API_KEY: ${{ secrets.COMPLIANCEAGENT_API_KEY }}
        run: python ci_compliance_check.py
```

## More Examples Coming Soon

- TypeScript/JavaScript SDK example
- CLI tool example
- Webhook handler example
- VS Code extension integration
