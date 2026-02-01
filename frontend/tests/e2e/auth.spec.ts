/**
 * E2E Test: Authentication Flow
 *
 * Tests the complete authentication workflow including:
 * - User registration
 * - Login with credentials
 * - Token refresh
 * - Logout
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend running at http://localhost:3000
 * - Test database seeded (make seed-test-db)
 */

import { test, expect } from '@playwright/test';

// Test credentials
const TEST_USER = {
  email: 'e2e-test@example.com',
  password: 'TestPassword123!',
  fullName: 'E2E Test User',
};

test.describe('Authentication', () => {
  test.describe('Registration', () => {
    test.skip('should register a new user', async ({ page }) => {
      // TODO: Implement when registration page is ready
      await page.goto('/auth/register');

      await page.fill('[name="email"]', TEST_USER.email);
      await page.fill('[name="password"]', TEST_USER.password);
      await page.fill('[name="fullName"]', TEST_USER.fullName);
      await page.click('button[type="submit"]');

      // Should redirect to dashboard or verification page
      await expect(page).toHaveURL(/\/(dashboard|verify)/);
    });

    test.skip('should show validation errors for invalid input', async ({ page }) => {
      await page.goto('/auth/register');

      // Submit with invalid email
      await page.fill('[name="email"]', 'invalid-email');
      await page.fill('[name="password"]', '123'); // Too short
      await page.click('button[type="submit"]');

      // Should show validation errors
      await expect(page.locator('.error-message')).toBeVisible();
    });
  });

  test.describe('Login', () => {
    test.skip('should login with valid credentials', async ({ page }) => {
      await page.goto('/auth/login');

      await page.fill('[name="email"]', TEST_USER.email);
      await page.fill('[name="password"]', TEST_USER.password);
      await page.click('button[type="submit"]');

      // Should redirect to dashboard
      await expect(page).toHaveURL('/dashboard');

      // Should show user info in header
      await expect(page.locator('[data-testid="user-menu"]')).toContainText(TEST_USER.fullName);
    });

    test.skip('should show error for invalid credentials', async ({ page }) => {
      await page.goto('/auth/login');

      await page.fill('[name="email"]', 'wrong@example.com');
      await page.fill('[name="password"]', 'WrongPassword123!');
      await page.click('button[type="submit"]');

      // Should show error message
      await expect(page.locator('.error-message')).toContainText(/invalid|incorrect/i);

      // Should stay on login page
      await expect(page).toHaveURL('/auth/login');
    });
  });

  test.describe('Session Management', () => {
    test.skip('should persist session across page reloads', async ({ page }) => {
      // Login first
      await page.goto('/auth/login');
      await page.fill('[name="email"]', TEST_USER.email);
      await page.fill('[name="password"]', TEST_USER.password);
      await page.click('button[type="submit"]');
      await expect(page).toHaveURL('/dashboard');

      // Reload page
      await page.reload();

      // Should still be on dashboard (session persisted)
      await expect(page).toHaveURL('/dashboard');
    });

    test.skip('should redirect to login when session expires', async ({ page, context }) => {
      // Login first
      await page.goto('/auth/login');
      await page.fill('[name="email"]', TEST_USER.email);
      await page.fill('[name="password"]', TEST_USER.password);
      await page.click('button[type="submit"]');
      await expect(page).toHaveURL('/dashboard');

      // Clear cookies to simulate session expiry
      await context.clearCookies();

      // Try to navigate to a protected page
      await page.goto('/dashboard/settings');

      // Should redirect to login
      await expect(page).toHaveURL(/\/auth\/login/);
    });
  });

  test.describe('Logout', () => {
    test.skip('should logout and clear session', async ({ page }) => {
      // Login first
      await page.goto('/auth/login');
      await page.fill('[name="email"]', TEST_USER.email);
      await page.fill('[name="password"]', TEST_USER.password);
      await page.click('button[type="submit"]');
      await expect(page).toHaveURL('/dashboard');

      // Click logout
      await page.click('[data-testid="user-menu"]');
      await page.click('[data-testid="logout-button"]');

      // Should redirect to login
      await expect(page).toHaveURL('/auth/login');

      // Trying to access dashboard should redirect to login
      await page.goto('/dashboard');
      await expect(page).toHaveURL(/\/auth\/login/);
    });
  });
});
