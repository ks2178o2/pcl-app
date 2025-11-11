/**
 * Authentication helpers for Playwright tests
 * These utilities help with common auth operations in E2E tests
 */

import { Page } from '@playwright/test';

/**
 * Clear all authentication state
 */
export async function clearAuth(page: Page) {
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
}

/**
 * Check if user is authenticated (has session in localStorage)
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  return await page.evaluate(() => {
    try {
      const authData = localStorage.getItem('sb-xxdahmkfioqzgqvyabek-auth-token');
      return !!authData;
    } catch {
      return false;
    }
  });
}

/**
 * Wait for authentication state to settle
 */
export async function waitForAuthState(page: Page, authenticated: boolean, timeout = 5000) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    const isAuth = await isAuthenticated(page);
    if (isAuth === authenticated) {
      return;
    }
    await page.waitForTimeout(100);
  }
}

/**
 * Navigate to a route and wait for auth redirect if needed
 */
export async function navigateAndWaitForAuth(page: Page, route: string) {
  await page.goto(route);
  await page.waitForLoadState('networkidle');
  
  // Wait a bit for any auth redirects
  await page.waitForTimeout(1000);
  
  return page.url();
}

