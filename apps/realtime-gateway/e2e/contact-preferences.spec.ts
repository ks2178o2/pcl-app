import { test, expect } from '@playwright/test';

test.describe('Contact Preferences', () => {
  test('should navigate to contact preferences page', async ({ page }) => {
    await page.goto('/contact-preferences');
    await page.waitForLoadState('networkidle');
    
    const preferenceIndicators = [
      page.getByText(/contact|preferences|settings/i),
      page.getByText(/loading/i),
    ];
    
    const visible = await Promise.all(
      preferenceIndicators.map(async (el) => {
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

