"""End-to-end test configuration for ComplianceAgent.

Uses Playwright for browser automation testing against a running application.
Run with: pytest tests/e2e/ -v --headed (for visible browser)
Requires: make dev && make run-backend && make run-frontend
"""

import pytest
from playwright.async_api import async_playwright, Browser, Page, BrowserContext


FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"

# Test user credentials (seeded by scripts/seed.py)
TEST_USER_EMAIL = "admin@example.com"
TEST_USER_PASSWORD = "admin123"


@pytest.fixture(scope="session")
async def browser():
    """Create a shared browser instance for all e2e tests."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture
async def context(browser: Browser):
    """Create an isolated browser context per test."""
    context = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        base_url=FRONTEND_URL,
    )
    yield context
    await context.close()


@pytest.fixture
async def page(context: BrowserContext):
    """Create a new page per test."""
    page = await context.new_page()
    yield page
    await page.close()


@pytest.fixture
async def authenticated_page(page: Page):
    """Create a page that is already logged in."""
    await page.goto("/login")
    await page.fill('[name="email"]', TEST_USER_EMAIL)
    await page.fill('[name="password"]', TEST_USER_PASSWORD)
    await page.click('button[type="submit"]')
    # Wait for redirect to dashboard
    await page.wait_for_url("**/dashboard**", timeout=10000)
    yield page
