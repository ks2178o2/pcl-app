import { test, expect } from '@playwright/test';

test.describe('Transcription Workflow', () => {
  test('should navigate to transcribe manager page', async ({ page }) => {
    await page.goto('/transcribe');
    await page.waitForLoadState('networkidle');
    
    // Check for transcription-related content
    const transcriptionIndicators = [
      page.getByText(/transcribe|transcription/i),
      page.getByText(/upload|file/i),
      page.getByRole('button', { name: /upload|choose file/i }),
    ];
    
    const visible = await Promise.all(
      transcriptionIndicators.map(async (el) => {
        try {
          return await el.isVisible({ timeout: 2000 });
        } catch {
          return false;
        }
      })
    );
    
    const currentUrl = page.url();
    if (!currentUrl.includes('/auth')) {
      expect(visible.some(v => v) || await page.locator('input[type="file"]').count() > 0).toBeTruthy();
    }
  });

  test('should display transcription tabs', async ({ page }) => {
    await page.goto('/transcribe');
    await page.waitForLoadState('networkidle');
    
    // Look for tabs (upload, history, etc.)
    const tabs = [
      page.getByRole('tab', { name: /upload/i }),
      page.getByRole('tab', { name: /history|list/i }),
      page.getByRole('tab', { name: /transcriptions/i }),
    ];
    
    const visible = await Promise.all(
      tabs.map(async (el) => {
        try {
          return await el.isVisible({ timeout: 2000 });
        } catch {
          return false;
        }
      })
    );
    
    const currentUrl = page.url();
    if (!currentUrl.includes('/auth')) {
      // At least one tab should be visible, or the page should have transcription UI
      expect(visible.some(v => v) || await page.getByText(/transcribe/i).isVisible().catch(() => false)).toBeTruthy();
    }
  });

  test('should have file upload interface', async ({ page }) => {
    await page.goto('/transcribe');
    await page.waitForLoadState('networkidle');
    
    // Check for file upload elements
    const uploadElements = [
      page.locator('input[type="file"]'),
      page.getByRole('button', { name: /upload|choose file|select file/i }),
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
      // File input might be hidden but should exist, or upload button should be visible
      expect(
        visible.some(v => v) || 
        await page.locator('input[type="file"]').count() > 0
      ).toBeTruthy();
    }
  });

  test('should display transcription history or empty state', async ({ page }) => {
    await page.goto('/transcribe');
    await page.waitForLoadState('networkidle');
    
    // Should show either:
    // 1. List of transcriptions
    // 2. Empty state
    // 3. Loading state
    
    const possibleStates = [
      page.getByText(/no transcriptions|empty|no files/i),
      page.getByText(/loading/i),
      page.locator('[data-testid*="transcription"], .transcription, [class*="transcription"]').first(),
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

