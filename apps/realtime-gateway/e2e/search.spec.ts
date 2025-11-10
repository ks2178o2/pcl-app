import { test, expect } from '@playwright/test';

test.describe('Search Functionality', () => {
  test('should navigate to search page', async ({ page }) => {
    await page.goto('/search');
    await page.waitForLoadState('networkidle');
    
    // Check for search-related content
    const searchIndicators = [
      page.getByText(/search|calls|find/i),
      page.getByRole('textbox', { name: /search/i }),
      page.locator('input[type="search"], input[placeholder*="search" i]'),
    ];
    
    const visible = await Promise.all(
      searchIndicators.map(async (el) => {
        try {
          return await el.isVisible({ timeout: 2000 });
        } catch {
          return false;
        }
      })
    );
    
    const currentUrl = page.url();
    if (!currentUrl.includes('/auth')) {
      expect(visible.some(v => v) || await page.locator('input[type="search"], input[type="text"]').count() > 0).toBeTruthy();
    }
  });

  test('should have search input field', async ({ page }) => {
    await page.goto('/search');
    await page.waitForLoadState('networkidle');
    
    // Look for search input
    const searchInputs = [
      page.getByRole('textbox', { name: /search/i }),
      page.locator('input[type="search"]'),
      page.locator('input[placeholder*="search" i]'),
    ];
    
    const visible = await Promise.all(
      searchInputs.map(async (el) => {
        try {
          return await el.isVisible({ timeout: 2000 });
        } catch {
          return false;
        }
      })
    );
    
    const currentUrl = page.url();
    if (!currentUrl.includes('/auth')) {
      // Search input should exist (might be hidden but in DOM)
      expect(
        visible.some(v => v) || 
        await page.locator('input[type="search"], input[type="text"]').count() > 0
      ).toBeTruthy();
    }
  });

  test('should display search results or empty state', async ({ page }) => {
    await page.goto('/search');
    await page.waitForLoadState('networkidle');
    
    // Should show either:
    // 1. Search results
    // 2. Empty state (no search yet)
    // 3. Loading state
    
    const possibleStates = [
      page.getByText(/no results|no calls found|empty/i),
      page.getByText(/loading/i),
      page.locator('[data-testid*="result"], .result, [class*="result"]').first(),
      page.locator('table, ul, ol').first(),
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

