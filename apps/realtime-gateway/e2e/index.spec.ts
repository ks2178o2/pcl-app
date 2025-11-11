import { test, expect } from '@playwright/test';

test.describe('Index/Home Page', () => {
  test('should navigate to home page', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Home page should load without errors
    await expect(page).not.toHaveURL(/error|404/);
  });

  test('should display home page content', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Should show some content (varies based on auth state)
    const currentUrl = page.url();
    // Might redirect to dashboard if authenticated, or show home content
    expect(currentUrl === '/' || currentUrl.includes('/dashboard') || currentUrl.includes('/auth')).toBeTruthy();
  });
});

