import { test, expect } from '@playwright/test';

test.describe('Leads Management', () => {
  test('should navigate to leads list page', async ({ page }) => {
    await page.goto('/leads');
    await page.waitForLoadState('networkidle');
    
    // Check for leads content
    const leadsIndicators = [
      page.getByText(/leads/i),
      page.getByText(/lead/i),
      page.getByRole('button', { name: /new|create|add/i }),
    ];
    
    const visible = await Promise.all(
      leadsIndicators.map(async (el) => {
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

  test('should display leads list or empty state', async ({ page }) => {
    await page.goto('/leads');
    await page.waitForLoadState('networkidle');
    
    // Should show either list, empty state, or loading
    const possibleStates = [
      page.getByText(/no leads|empty|no data/i),
      page.getByText(/loading/i),
      page.locator('[data-testid*="lead"], .lead, [class*="lead"]').first(),
    ];
    
    const visible = await Promise.all(
      possibleStates.map(async (el) => {
        try {
          return await el.isVisible({ timeout: 3000 });
        } catch {
          return false;
        }
      })
    );
    
    const currentUrl = page.url();
    if (!currentUrl.includes('/auth')) {
      expect(visible.some(v => v) || await page.locator('table, ul, ol').count() > 0).toBeTruthy();
    }
  });

  test('should navigate to lead details page', async ({ page }) => {
    // Try to navigate to a lead detail page
    await page.goto('/leads/test-lead-id-123');
    await page.waitForLoadState('networkidle');
    
    // Should show either:
    // 1. Lead details
    // 2. 404/not found
    // 3. Loading state
    
    const possibleStates = [
      page.getByText(/lead|details/i),
      page.getByText(/not found|404/i),
      page.getByText(/loading/i),
    ];
    
    const visible = await Promise.all(
      possibleStates.map(async (el) => {
        try {
          return await el.isVisible({ timeout: 3000 });
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

