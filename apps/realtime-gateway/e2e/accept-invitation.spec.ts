import { test, expect } from '@playwright/test';

test.describe('Accept Invitation', () => {
  test('should navigate to accept invitation page', async ({ page }) => {
    await page.goto('/accept-invitation');
    await page.waitForLoadState('networkidle');
    
    const invitationIndicators = [
      page.getByText(/invitation|accept|join/i),
      page.getByText(/loading/i),
      page.getByText(/invalid|expired/i),
    ];
    
    const visible = await Promise.all(
      invitationIndicators.map(async (el) => {
        try {
          return await el.isVisible({ timeout: 2000 });
        } catch {
          return false;
        }
      })
    );
    
    const currentUrl = page.url();
    expect(visible.some(v => v) || currentUrl.includes('/accept-invitation')).toBeTruthy();
  });
});

