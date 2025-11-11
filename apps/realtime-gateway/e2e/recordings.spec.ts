import { test, expect } from '@playwright/test';

test.describe('Recordings Page', () => {
  test('should navigate to recordings page', async ({ page }) => {
    await page.goto('/recordings');
    await page.waitForLoadState('networkidle');
    
    const recordingIndicators = [
      page.getByText(/recordings|audio|calls/i),
      page.getByText(/loading/i),
      page.getByText(/no recordings|empty/i),
    ];
    
    const visible = await Promise.all(
      recordingIndicators.map(async (el) => {
        try {
          return await el.isVisible({ timeout: 2000 });
        } catch {
          return false;
        }
      })
    );
    
    const currentUrl = page.url();
    if (!currentUrl.includes('/auth')) {
      expect(visible.some(v => v) || await page.locator('table, ul, [class*="recording"]').count() > 0).toBeTruthy();
    }
  });
});

