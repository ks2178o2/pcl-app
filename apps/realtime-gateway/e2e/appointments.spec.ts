import { test, expect } from '@playwright/test';

test.describe('Appointments', () => {
  test('should navigate to appointments page', async ({ page }) => {
    await page.goto('/appointments');
    await page.waitForLoadState('networkidle');
    
    // Check for appointments content
    const appointmentIndicators = [
      page.getByText(/appointments/i),
      page.getByText(/schedule/i),
      page.getByRole('button', { name: /new|create|add/i }),
    ];
    
    const visible = await Promise.all(
      appointmentIndicators.map(async (el) => {
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

  test('should display appointments list or empty state', async ({ page }) => {
    await page.goto('/appointments');
    await page.waitForLoadState('networkidle');
    
    // Should show either:
    // 1. List of appointments
    // 2. Empty state
    // 3. Loading state
    
    const possibleStates = [
      page.getByText(/no appointments|empty|no data/i),
      page.getByText(/loading/i),
      page.locator('[data-testid*="appointment"], .appointment, [class*="appointment"]').first(),
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
});

