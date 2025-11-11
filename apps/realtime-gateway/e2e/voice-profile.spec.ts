import { test, expect } from '@playwright/test';

test.describe('Voice Profile', () => {
  test('should navigate to voice profile page', async ({ page }) => {
    await page.goto('/voice-profile');
    await page.waitForLoadState('networkidle');
    
    const voiceIndicators = [
      page.getByText(/voice|profile|recording/i),
      page.getByText(/loading/i),
    ];
    
    const visible = await Promise.all(
      voiceIndicators.map(async (el) => {
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

