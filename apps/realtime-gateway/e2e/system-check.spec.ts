import { test, expect } from '@playwright/test';

test.describe('System Check', () => {
  test('should navigate to system check page', async ({ page }) => {
    await page.goto('/system-check');
    await page.waitForLoadState('networkidle');
    
    const systemIndicators = [
      page.getByText(/system|check|status|health/i),
      page.getByText(/loading/i),
    ];
    
    const visible = await Promise.all(
      systemIndicators.map(async (el) => {
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

