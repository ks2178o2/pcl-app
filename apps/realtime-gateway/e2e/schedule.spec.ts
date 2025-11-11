import { test, expect } from '@playwright/test';

test.describe('Schedule Detail', () => {
  test('should navigate to schedule page', async ({ page }) => {
    await page.goto('/schedule');
    await page.waitForLoadState('networkidle');
    
    const scheduleIndicators = [
      page.getByText(/schedule|appointment|calendar/i),
      page.getByText(/loading/i),
    ];
    
    const visible = await Promise.all(
      scheduleIndicators.map(async (el) => {
        try {
          return await el.isVisible({ timeout: 2000 });
        } catch {
          return false;
        }
      })
    );
    
    const currentUrl = page.url();
    if (!currentUrl.includes('/auth')) {
      expect(visible.some(v => v) || await page.locator('table, [class*="calendar"], [class*="schedule"]').count() > 0).toBeTruthy();
    }
  });
});

