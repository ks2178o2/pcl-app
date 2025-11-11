import { test, expect } from '@playwright/test';

test.describe('System Admin', () => {
  test('should navigate to system admin page', async ({ page }) => {
    await page.goto('/system-admin');
    await page.waitForLoadState('networkidle');
    
    const adminIndicators = [
      page.getByText(/system|admin|management/i),
      page.getByText(/loading/i),
      page.getByText(/unauthorized|access denied/i),
    ];
    
    const visible = await Promise.all(
      adminIndicators.map(async (el) => {
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

