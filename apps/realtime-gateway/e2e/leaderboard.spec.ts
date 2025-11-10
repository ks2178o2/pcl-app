import { test, expect } from '@playwright/test';

test.describe('Leaderboard', () => {
  test('should navigate to leaderboard page', async ({ page }) => {
    await page.goto('/leaderboard');
    await page.waitForLoadState('networkidle');
    
    const leaderboardIndicators = [
      page.getByText(/leaderboard|ranking|top/i),
      page.getByText(/loading/i),
    ];
    
    const visible = await Promise.all(
      leaderboardIndicators.map(async (el) => {
        try {
          return await el.isVisible({ timeout: 2000 });
        } catch {
          return false;
        }
      })
    );
    
    const currentUrl = page.url();
    if (!currentUrl.includes('/auth')) {
      expect(visible.some(v => v) || await page.locator('table, [class*="leaderboard"]').count() > 0).toBeTruthy();
    }
  });
});

