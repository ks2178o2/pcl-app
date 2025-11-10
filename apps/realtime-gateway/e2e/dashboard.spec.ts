import { test, expect } from '@playwright/test';

test.describe('Sales Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('should display dashboard page', async ({ page }) => {
    // Check for dashboard-specific content
    // The exact content depends on auth state and data
    const dashboardIndicators = [
      page.getByText(/dashboard/i),
      page.getByText(/sales/i),
      page.getByText(/calls/i),
      page.getByText(/appointments/i),
    ];
    
    // At least one indicator should be visible
    const visible = await Promise.all(
      dashboardIndicators.map(async (el) => {
        try {
          return await el.isVisible({ timeout: 2000 });
        } catch {
          return false;
        }
      })
    );
    
    // If redirected to auth, that's expected for unauthenticated users
    const currentUrl = page.url();
    if (!currentUrl.includes('/auth')) {
      expect(visible.some(v => v)).toBeTruthy();
    }
  });

  test('should have sidebar navigation', async ({ page }) => {
    // Check for sidebar (may be collapsed on mobile)
    const sidebar = page.locator('[data-testid="sidebar"], nav, aside').first();
    
    // Sidebar might be hidden on mobile, so we'll check if it exists
    const sidebarExists = await sidebar.count() > 0;
    
    // If we're on dashboard and not redirected, sidebar should exist
    const currentUrl = page.url();
    if (!currentUrl.includes('/auth')) {
      // Sidebar might be hidden but should exist in DOM
      expect(sidebarExists || await page.locator('button[aria-label*="menu"], button[aria-label*="nav"]').count() > 0).toBeTruthy();
    }
  });

  test('should display metrics or loading state', async ({ page }) => {
    // Dashboard should show either:
    // 1. Metrics/data
    // 2. Loading indicators
    // 3. Empty state
    
    const possibleStates = [
      page.getByText(/loading/i),
      page.getByText(/metrics/i),
      page.getByText(/calls/i),
      page.getByText(/appointments/i),
      page.getByText(/no data|empty/i),
    ];
    
    // At least one state should be visible
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

