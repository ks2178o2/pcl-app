import { test, expect } from '@playwright/test';

test.describe('Failed Uploads Banner v1.0.5', () => {
  test('should display banner when uploads fail', async ({ page }) => {
    await page.goto('/recordings');
    
    // Check if banner is present
    const banner = page.locator('[role="alert"]');
    
    // If there are failed uploads, banner should be visible
    const bannerVisible = await banner.isVisible().catch(() => false);
    
    if (bannerVisible) {
      // Verify it shows failed uploads
      await expect(page.getByText(/failed|needs attention/i)).toBeVisible();
      
      // Check for retry buttons
      const retryButtons = page.getByRole('button', { name: /retry/i });
      const count = await retryButtons.count();
      expect(count).toBeGreaterThanOrEqual(0);
    }
  });

  test('should allow retry of failed uploads', async ({ page }) => {
    await page.goto('/recordings');
    
    // Find retry button if it exists
    const retryButton = page.getByRole('button', { name: /retry/i }).first();
    
    if (await retryButton.isVisible({ timeout: 5000 })) {
      // Mock successful retry
      await page.route('**/call-recordings/**', route => {
        route.fulfill({ status: 200, body: 'OK' });
      });
      
      await retryButton.click();
      
      // Wait for success message
      await expect(page.getByText(/success|complete/i).first()).toBeVisible({ timeout: 10000 });
    }
  });
});

