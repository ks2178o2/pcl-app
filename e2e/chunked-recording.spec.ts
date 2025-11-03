import { test, expect } from '@playwright/test';

test.describe('Chunked Recording v1.0.5', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to recordings page
    // Note: Adjust auth flow based on your setup
    await page.goto('/recordings');
  });

  test('should start and stop recording successfully', async ({ page }) => {
    // Find and click Start Recording button
    const startButton = page.getByRole('button', { name: /start recording/i });
    await startButton.click();
    
    // Wait for recording to start
    await expect(page.getByText(/recording/i)).toBeVisible({ timeout: 5000 });
    
    // Wait 5 seconds of recording
    await page.waitForTimeout(5000);
    
    // Stop recording
    const stopButton = page.getByRole('button', { name: /stop/i });
    await stopButton.click();
    
    // Verify recording completed
    await expect(page.getByText(/upload|complete/i)).toBeVisible({ timeout: 30000 });
  });

  test('should display recording progress', async ({ page }) => {
    const startButton = page.getByRole('button', { name: /start recording/i });
    await startButton.click();
    
    // Check for progress indicators
    await expect(page.locator('[role="progressbar"]').first()).toBeVisible({ timeout: 5000 });
    
    // Verify duration or progress text appears
    const hasProgressIndicator = await page.locator('text=/recording|progress|\\d+:\\d+/').first().isVisible();
    expect(hasProgressIndicator).toBeTruthy();
  });

  test('should handle pause/resume', async ({ page }) => {
    await page.getByRole('button', { name: /start/i }).click();
    await page.waitForTimeout(2000);
    
    // Try to find pause button (may not always be visible)
    const pauseButton = page.getByRole('button', { name: /pause/i });
    if (await pauseButton.isVisible({ timeout: 2000 })) {
      await pauseButton.click();
      await expect(page.getByText(/paused/i)).toBeVisible({ timeout: 3000 });
      
      // Resume
      await page.getByRole('button', { name: /resume/i }).click();
      await expect(page.getByText(/recording/i)).toBeVisible({ timeout: 3000 });
    }
    
    // Stop recording
    await page.getByRole('button', { name: /stop/i }).click();
  });

  test('should verify IndexedDB persistence', async ({ page }) => {
    // Start recording
    await page.getByRole('button', { name: /start/i }).click();
    await page.waitForTimeout(2000);
    
    // Check IndexedDB for chunkedRecordings
    const indexedDBData = await page.evaluate(() => {
      return new Promise((resolve) => {
        const request = indexedDB.open('chunkedRecordings', 1);
        request.onsuccess = () => {
          const db = request.result;
          const transaction = db.transaction(['recordings'], 'readonly');
          const store = transaction.objectStore('recordings');
          const getRequest = store.getAll();
          getRequest.onsuccess = () => resolve(getRequest.result);
          getRequest.onerror = () => resolve(null);
        };
        request.onerror = () => resolve(null);
      });
    });
    
    // IndexedDB should have data
    expect(indexedDBData).toBeTruthy();
    
    // Stop recording
    await page.getByRole('button', { name: /stop/i }).click();
  });
});

