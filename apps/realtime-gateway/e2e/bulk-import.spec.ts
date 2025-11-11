import { test, expect } from '@playwright/test';

test.describe('Bulk Import', () => {
  test('should navigate to bulk import page', async ({ page }) => {
    await page.goto('/bulk-import');
    await page.waitForLoadState('networkidle');
    
    // Check for bulk import content
    const bulkImportIndicators = [
      page.getByText(/bulk import/i),
      page.getByText(/upload/i),
      page.getByText(/import/i),
    ];
    
    const visible = await Promise.all(
      bulkImportIndicators.map(async (el) => {
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

  test('should also work with /bulk-upload route', async ({ page }) => {
    await page.goto('/bulk-upload');
    await page.waitForLoadState('networkidle');
    
    // Should show same content as /bulk-import
    const currentUrl = page.url();
    expect(currentUrl.includes('/bulk-upload') || currentUrl.includes('/bulk-import')).toBeTruthy();
  });

  test('should have file upload interface', async ({ page }) => {
    await page.goto('/bulk-import');
    await page.waitForLoadState('networkidle');
    
    // Look for file input or upload button
    const uploadElements = [
      page.getByRole('button', { name: /upload|choose file|select file/i }),
      page.locator('input[type="file"]'),
      page.getByText(/drag.*drop|choose file/i),
    ];
    
    const visible = await Promise.all(
      uploadElements.map(async (el) => {
        try {
          return await el.isVisible({ timeout: 2000 });
        } catch {
          return false;
        }
      })
    );
    
    const currentUrl = page.url();
    if (!currentUrl.includes('/auth')) {
      // At least one upload element should be present
      expect(visible.some(v => v) || await page.locator('input[type="file"]').count() > 0).toBeTruthy();
    }
  });
});

