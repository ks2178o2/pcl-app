import { test, expect } from '@playwright/test';

test.describe('Activity Log', () => {
  test('should navigate to activity log page', async ({ page }) => {
    await page.goto('/activity');
    await page.waitForLoadState('networkidle');
    
    const activityIndicators = [
      page.getByText(/activity|log|history/i),
      page.getByText(/loading/i),
      page.getByText(/no activity|empty/i),
    ];
    
    const visible = await Promise.all(
      activityIndicators.map(async (el) => {
        try {
          return await el.isVisible({ timeout: 2000 });
        } catch {
          return false;
        }
      })
    );
    
    const currentUrl = page.url();
    if (!currentUrl.includes('/auth')) {
      expect(visible.some(v => v) || await page.locator('table, ul, ol').count() > 0).toBeTruthy();
    }
  });
});

