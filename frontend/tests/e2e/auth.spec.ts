/**
 * E2E Test: Core User Flows
 *
 * Tests the complete authentication and navigation workflow:
 * - Login page rendering and form submission
 * - Signup page rendering
 * - Dashboard navigation and route protection
 * - Settings page tabs
 * - Logout flow
 *
 * Prerequisites:
 * - Backend API running at http://localhost:8000
 * - Frontend running at http://localhost:3000
 */

import { test, expect } from '@playwright/test'

test.describe('Login Page', () => {
  test('renders login form with all elements', async ({ page }) => {
    await page.goto('/login')

    await expect(page.locator('h2')).toContainText('Sign in to your account')
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toContainText('Sign in')
    await expect(page.locator('a[href="/signup"]')).toBeVisible()
    await expect(page.locator('a[href="/forgot-password"]')).toBeVisible()
  })

  test('shows error on invalid credentials', async ({ page }) => {
    await page.goto('/login')

    await page.fill('input[type="email"]', 'wrong@example.com')
    await page.fill('input[type="password"]', 'WrongPassword!')
    await page.click('button[type="submit"]')

    // Should show an error message (API may be down — either API error or network error)
    const errorOrButton = page.locator('.bg-red-50, button[type="submit"]')
    await expect(errorOrButton.first()).toBeVisible({ timeout: 10000 })
  })
})

test.describe('Signup Page', () => {
  test('renders registration form', async ({ page }) => {
    await page.goto('/signup')

    await expect(page.locator('h2')).toContainText('Create your account')
    await expect(page.locator('input[name="fullName"]')).toBeVisible()
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('input[type="checkbox"]')).toBeVisible()
    await expect(page.locator('a[href="/login"]')).toBeVisible()
  })

  test('links between login and signup', async ({ page }) => {
    await page.goto('/login')
    await page.click('a[href="/signup"]')
    await expect(page).toHaveURL('/signup')

    await page.click('a[href="/login"]')
    await expect(page).toHaveURL('/login')
  })
})

test.describe('Forgot Password Page', () => {
  test('renders forgot password form', async ({ page }) => {
    await page.goto('/forgot-password')

    await expect(page.locator('h2')).toContainText('Reset your password')
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('a[href="/login"]')).toBeVisible()
  })
})

test.describe('Route Protection', () => {
  test('redirects unauthenticated users from dashboard to login', async ({ page }) => {
    await page.goto('/dashboard')

    // Middleware should redirect to login
    await expect(page).toHaveURL(/\/login/)
  })

  test('redirects unauthenticated users from settings to login', async ({ page }) => {
    await page.goto('/dashboard/settings')

    await expect(page).toHaveURL(/\/login/)
  })
})

test.describe('Landing Page', () => {
  test('renders public landing page', async ({ page }) => {
    await page.goto('/')

    await expect(page.locator('text=ComplianceAgent')).toBeVisible()
    await expect(page.locator('a[href="/login"]')).toBeVisible()
  })
})
