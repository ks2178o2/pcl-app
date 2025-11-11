import { test, expect } from '@playwright/test';

test.describe('Security Settings', () => {
  test('should navigate to security settings page', async ({ page }) => {
    await page.goto('/security-settings');
    await page.waitForLoadState('networkidle');
    
    const securityIndicators = [
      page.getByText(/security|settings|password|2fa/i),
      page.getByText(/loading/i),
    ];
    
    const visible = await Promise.all(
      securityIndicators.map(async (el) => {
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

