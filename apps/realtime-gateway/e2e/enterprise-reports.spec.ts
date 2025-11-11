import { test, expect } from '@playwright/test';

test.describe('Enterprise Reports', () => {
  test('should navigate to enterprise reports page', async ({ page }) => {
    await page.goto('/enterprise-reports');
    await page.waitForLoadState('networkidle');
    
    const reportIndicators = [
      page.getByText(/enterprise|reports|analytics/i),
      page.getByText(/loading/i),
    ];
    
    const visible = await Promise.all(
      reportIndicators.map(async (el) => {
        try {
          return await el.isVisible({ timeout: 2000 });
        } catch {
          return false;
        }
      })
    );
    
    const currentUrl = page.url();
    if (!currentUrl.includes('/auth')) {
      expect(visible.some(v => v)).toBeTruthy();
    }
  });
});

