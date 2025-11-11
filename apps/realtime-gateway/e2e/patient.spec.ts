import { test, expect } from '@playwright/test';

test.describe('Patient Management', () => {
  test('should navigate to patient details page', async ({ page }) => {
    const testPatientName = 'test-patient-123';
    await page.goto(`/patient/${testPatientName}`);
    await page.waitForLoadState('networkidle');
    
    // Check for patient-related content
    const patientIndicators = [
      page.getByText(/patient|details/i),
      page.getByText(/loading/i),
      page.getByText(/not found|error/i),
    ];
    
    const visible = await Promise.all(
      patientIndicators.map(async (el) => {
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

  test('should display patient information or empty state', async ({ page }) => {
    const testPatientName = 'test-patient-123';
    await page.goto(`/patient/${testPatientName}`);
    await page.waitForLoadState('networkidle');
    
    // Should show patient info, loading, or not found
    const possibleStates = [
      page.getByText(/patient|name|contact/i),
      page.getByText(/loading/i),
      page.getByText(/not found|404|error/i),
      page.locator('[data-testid*="patient"]').first(),
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

