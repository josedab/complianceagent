# E2E Test Setup Guide

This directory will contain end-to-end tests using Playwright.

## Setup (Not Yet Implemented)

### Prerequisites

```bash
# Install Playwright
cd frontend
npm install -D @playwright/test
npx playwright install
```

### Configuration

Create `playwright.config.ts` in the frontend root:

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### Running Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI
npx playwright test --ui

# Run specific test file
npx playwright test tests/e2e/auth.spec.ts
```

## Planned Test Suites

1. **Authentication** (`auth.spec.ts`)
   - User registration
   - Login/logout flow
   - Token refresh
   - SSO integration

2. **Dashboard** (`dashboard.spec.ts`)
   - Compliance overview loading
   - Navigation between sections
   - Data visualization rendering

3. **Compliance Workflow** (`compliance.spec.ts`)
   - Add repository
   - Trigger analysis
   - View compliance gaps
   - Generate code fix

4. **Regulations** (`regulations.spec.ts`)
   - Browse regulations
   - Filter by framework/jurisdiction
   - View requirements

## Test Data

Test fixtures will be located in `tests/e2e/fixtures/`:
- `users.json` - Test user credentials
- `repositories.json` - Test repository data
- `regulations.json` - Sample regulation data

## CI Integration

E2E tests run in the `ci.yml` workflow after unit tests pass.
