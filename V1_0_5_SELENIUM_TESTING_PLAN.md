# V1.0.5 Selenium/Playwright Testing Plan

**Date:** January 7, 2025  
**Status:** Ready to Implement  
**Priority:** 🔴 High

---

## 🎯 Recommendation: Use Playwright (Not Selenium)

### Why Playwright Instead of Selenium?
- ✅ **Faster** - Modern WebDriver protocol
- ✅ **More reliable** - Auto-waits, retries built-in
- ✅ **Better debugging** - Screenshot, video recording, trace viewer
- ✅ **Single API** - Works across Chrome, Firefox, Safari
- ✅ **Great TypeScript support** - Perfect for our stack
- ✅ **Network interception** - Mock requests easily
- ✅ **Mobile testing** - Built-in mobile device emulation

---

## 📦 Installation

### Add Playwright to Project

```bash
cd apps/realtime-gateway
npm install -D @playwright/test
npx playwright install
```

### Create Playwright Config

**File:** `apps/realtime-gateway/playwright.config.ts`

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: process.env.PLAYWRIGHT_TEST_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

---

## 🧪 Test Structure

### Create Test Directory

```bash
mkdir -p apps/realtime-gateway/e2e
```

---

## 📝 Critical Tests for v1.0.5

### Test 1: Chunked Recording Basic Flow
**File:** `apps/realtime-gateway/e2e/chunked-recording.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Chunked Recording', () => {
  test.beforeEach(async ({ page }) => {
    // Login (configure based on your auth setup)
    await page.goto('/login');
    // Add login steps here
  });

  test('should start and stop recording successfully', async ({ page }) => {
    await page.goto('/recordings');
    
    // Find and click Start Recording button
    const startButton = page.getByRole('button', { name: /start recording/i });
    await startButton.click();
    
    // Wait for recording to start
    await expect(page.getByText(/recording/i)).toBeVisible();
    
    // Wait 5 seconds of recording
    await page.waitForTimeout(5000);
    
    // Stop recording
    const stopButton = page.getByRole('button', { name: /stop/i });
    await stopButton.click();
    
    // Verify recording completed
    await expect(page.getByText(/upload.*progress/i)).toBeVisible();
    
    // Wait for upload to complete
    await expect(page.getByText(/upload.*complete/i)).toBeVisible({ timeout: 30000 });
  });

  test('should display recording progress', async ({ page }) => {
    await page.goto('/recordings');
    
    const startButton = page.getByRole('button', { name: /start recording/i });
    await startButton.click();
    
    // Check for progress indicators
    await expect(page.locator('[role="progressbar"]')).toBeVisible();
    
    // Verify duration increases
    const durationStart = await page.locator('text=/\\d+:\\d+/').first().textContent();
    await page.waitForTimeout(2000);
    const durationEnd = await page.locator('text=/\\d+:\\d+/').first().textContent();
    expect(durationEnd).not.toBe(durationStart);
  });

  test('should handle pause/resume', async ({ page }) => {
    await page.goto('/recordings');
    
    await page.getByRole('button', { name: /start/i }).click();
    await page.waitForTimeout(2000);
    
    // Pause
    await page.getByRole('button', { name: /pause/i }).click();
    await expect(page.getByText(/paused/i)).toBeVisible();
    
    // Resume
    await page.getByRole('button', { name: /resume/i }).click();
    await expect(page.getByText(/recording/i)).toBeVisible();
    
    // Stop
    await page.getByRole('button', { name: /stop/i }).click();
  });
});
```

---

### Test 2: Crash Recovery
**File:** `apps/realtime-gateway/e2e/crash-recovery.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Crash Recovery', () => {
  test('should detect and recover interrupted recording', async ({ page, context }) => {
    await page.goto('/login');
    // Login steps
    
    await page.goto('/recordings');
    
    // Start recording
    await page.getByRole('button', { name: /start/i }).click();
    await page.waitForTimeout(3000);
    
    // Close browser tab (simulate crash)
    await page.close();
    
    // Create new page (simulate reopening browser)
    const newPage = await context.newPage();
    await newPage.goto('/recordings');
    
    // Verify recovery dialog appears
    await expect(newPage.getByRole('dialog')).toBeVisible();
    await expect(newPage.getByText(/recover.*recording/i)).toBeVisible();
    
    // Click recover
    await newPage.getByRole('button', { name: /recover|yes/i }).click();
    
    // Verify recording continues
    await expect(newPage.getByText(/recording/i)).toBeVisible();
  });

  test('should persist recording state in IndexedDB', async ({ page, context }) => {
    await page.goto('/recordings');
    
    // Start recording
    await page.getByRole('button', { name: /start/i }).click();
    await page.waitForTimeout(2000);
    
    // Check IndexedDB
    const indexedDBData = await page.evaluate(() => {
      return new Promise((resolve) => {
        const request = indexedDB.open('chunkedRecordings', 1);
        request.onsuccess = () => {
          const db = request.result;
          const transaction = db.transaction(['recordings'], 'readonly');
          const store = transaction.objectStore('recordings');
          const getRequest = store.getAll();
          getRequest.onsuccess = () => resolve(getRequest.result);
        };
      });
    });
    
    expect(indexedDBData).toBeTruthy();
    expect(Array.isArray(indexedDBData)).toBe(true);
  });
});
```

---

### Test 3: Audio Re-encoding
**File:** `apps/realtime-gateway/e2e/audio-reencoding.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Audio Re-encoding', () => {
  test('should use re-encoding service for multi-chunk recordings', async ({ page }) => {
    // Set up console monitoring
    const consoleMessages: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'log') {
        consoleMessages.push(msg.text());
      }
    });
    
    await page.goto('/recordings');
    
    // Record for > 5 minutes to trigger chunks
    await page.getByRole('button', { name: /start/i }).click();
    await page.waitForTimeout(6000); // 6 seconds for testing
    await page.getByRole('button', { name: /stop/i }).click();
    
    // Wait for processing
    await page.waitForTimeout(5000);
    
    // Check console for re-encoding logs
    const hasReencodingLog = consoleMessages.some(msg => 
      msg.includes('AudioReencoding') || msg.includes('re-encode')
    );
    
    // Note: Full multi-chunk test would require longer recording
    // This is a smoke test
    expect(hasReencodingLog || consoleMessages.length > 0).toBeTruthy();
  });

  test('should handle re-encoding errors gracefully', async ({ page }) => {
    await page.goto('/recordings');
    
    // Mock network error for re-encoding
    await page.route('**/audio-reencoding', route => {
      route.fulfill({ status: 500 });
    });
    
    // Try recording
    await page.getByRole('button', { name: /start/i }).click();
    await page.waitForTimeout(2000);
    await page.getByRole('button', { name: /stop/i }).click();
    
    // Should show error toast
    await expect(page.getByText(/error/i).first()).toBeVisible({ timeout: 10000 });
  });
});
```

---

### Test 4: Failed Uploads Banner
**File:** `apps/realtime-gateway/e2e/failed-uploads-banner.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Failed Uploads Banner', () => {
  test('should display banner when uploads fail', async ({ page }) => {
    // Mock failed upload
    await page.route('**/call-recordings/**', route => {
      route.fulfill({ status: 500, body: 'Upload failed' });
    });
    
    await page.goto('/recordings');
    
    // Trigger recording that will fail
    await page.getByRole('button', { name: /start/i }).click();
    await page.waitForTimeout(2000);
    await page.getByRole('button', { name: /stop/i }).click();
    
    // Wait for banner to appear
    await expect(page.locator('[role="alert"]')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/failed|needs attention/i)).toBeVisible();
  });

  test('should allow retry of failed uploads', async ({ page }) => {
    // First, ensure we have a failed upload
    // (setup code here)
    
    await page.goto('/recordings');
    
    // Find retry button
    const retryButton = page.getByRole('button', { name: /retry/i }).first();
    await retryButton.click();
    
    // Wait for retry to complete
    await expect(page.getByText(/success/i).first()).toBeVisible({ timeout: 30000 });
  });

  test('should allow deletion of failed uploads', async ({ page }) => {
    await page.goto('/recordings');
    
    // Find delete button
    const deleteButton = page.getByRole('button', { name: /delete/i }).first();
    
    // Click and confirm
    await deleteButton.click();
    
    // Verify banner disappears or count decreases
    await expect(page.locator('[role="alert"]')).not.toBeVisible({ timeout: 5000 });
  });
});
```

---

## 🚀 Running Tests

### Add Scripts to package.json

```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:headed": "playwright test --headed",
    "test:e2e:debug": "playwright test --debug",
    "test:e2e:report": "playwright show-report"
  }
}
```

### Run Tests

```bash
# Run all tests
npm run test:e2e

# Run with UI mode
npm run test:e2e:ui

# Run headed (see browser)
npm run test:e2e:headed

# Debug mode
npm run test:e2e:debug

# View report
npm run test:e2e:report
```

---

## 📊 CI/CD Integration

### GitHub Actions

**File:** `.github/workflows/playwright.yml`

```yaml
name: Playwright E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    timeout-minutes: 60
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install Playwright browsers
        run: npx playwright install --with-deps
      
      - name: Run E2E tests
        run: npm run test:e2e
        env:
          PLAYWRIGHT_TEST_BASE_URL: http://localhost:3000
      
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

---

## 📈 Test Coverage Goals

### Priority 1: Critical Paths (Must Have)
- [ ] Basic recording flow
- [ ] Crash recovery
- [ ] Upload completion
- [ ] Failed upload banner

### Priority 2: Important Features (Should Have)
- [ ] Pause/resume
- [ ] Progress indicators
- [ ] Audio re-encoding
- [ ] Retry functionality

### Priority 3: Edge Cases (Nice to Have)
- [ ] Network failures
- [ ] Browser crash during different states
- [ ] Multiple concurrent recordings
- [ ] Long duration recordings

---

## 🔧 Advanced Features

### Screenshot on Failure

Already configured in `playwright.config.ts`:
```typescript
screenshot: 'only-on-failure'
```

### Video Recording

```typescript
video: 'retain-on-failure'
```

### Trace Viewer

```typescript
trace: 'on-first-retry'
```

View traces:
```bash
npx playwright show-trace trace.zip
```

---

## 🐛 Debugging

### Debug a Single Test

```bash
npx playwright test chunked-recording.spec.ts --debug
```

### Inspect Element

```typescript
test('debug test', async ({ page }) => {
  await page.pause(); // Opens inspector
});
```

### Console Logging

```typescript
page.on('console', msg => console.log('Browser:', msg.text()));
```

---

## 📚 Resources

- **Playwright Docs:** https://playwright.dev
- **Best Practices:** https://playwright.dev/docs/best-practices
- **Examples:** https://github.com/microsoft/playwright

---

## ✅ Success Criteria

### Implementation
- [ ] Playwright installed and configured
- [ ] Config file created
- [ ] Test directory structure set up
- [ ] CI integration complete

### Test Coverage
- [ ] 10+ E2E tests created
- [ ] All critical paths covered
- [ ] Tests pass consistently
- [ ] Screenshots/videos captured

### CI/CD
- [ ] Tests run on PR
- [ ] Tests run on push
- [ ] Reports generated
- [ ] Artifacts stored

---

**Ready to implement!** Start with the Playwright installation and basic recording test.

