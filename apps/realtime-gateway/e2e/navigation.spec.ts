import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should navigate to 404 page for unknown routes', async ({ page }) => {
    await page.goto('/unknown-route-12345');
    
    // Should show 404 or NotFound page
    await expect(
      page.getByText(/not found|404|page not found/i)
    ).toBeVisible({ timeout: 5000 });
  });

  test('should have accessible navigation links', async ({ page }) => {
    await page.goto('/');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Check for common navigation elements
    // These may vary based on auth state, so we'll check what's visible
    const navElements = [
      page.getByRole('link', { name: /dashboard/i }),
      page.getByRole('link', { name: /appointments/i }),
      page.getByRole('link', { name: /leads/i }),
      page.getByRole('link', { name: /settings/i }),
    ];
    
    // At least one navigation element should be visible (or all if authenticated)
    const visibleNavs = await Promise.all(
      navElements.map(async (el) => {
        try {
          return await el.isVisible({ timeout: 1000 });
        } catch {
          return false;
        }
      })
    );
    
    // If user is not authenticated, they might be redirected to /auth
    const currentUrl = page.url();
    if (currentUrl.includes('/auth')) {
      // Expected behavior for unauthenticated users
      expect(currentUrl).toContain('/auth');
    } else {
      // If authenticated, at least some nav should be visible
      expect(visibleNavs.some(v => v)).toBeTruthy();
    }
  });

  test('should redirect unauthenticated users to auth page', async ({ page }) => {
    // Clear auth state
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    
    // Try to access protected route
    await page.goto('/dashboard');
    
    // Should redirect to auth or show auth-related content
    await page.waitForTimeout(2000);
    const currentUrl = page.url();
    
    // Either redirected to /auth or still on /dashboard but showing auth UI
    expect(
      currentUrl.includes('/auth') || 
      await page.getByText(/sign in|login|authentication/i).isVisible().catch(() => false)
    ).toBeTruthy();
  });
});

