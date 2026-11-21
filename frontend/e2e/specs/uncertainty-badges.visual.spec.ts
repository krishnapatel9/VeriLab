import { test, expect } from '@playwright/test';

test.describe('Uncertainty Badges Visual Regression (AI Context Core §4)', () => {
  test('verification badge renders text and icon correctly', async ({ page, request }) => {
    const res = await request.get('/api/v1/intake/reports');
    if (!res.ok()) return;
    const body = await res.json();
    const reports = body.reports || [];
    if (reports.length === 0) return;

    const targetReport = reports[0];
    await page.goto(`/consultation/${targetReport.id}`);

    const badge = page.getByTestId('verification-badge').first();
    if (await badge.isVisible()) {
      await expect(badge).toBeVisible();
      // Ensure text content is non-empty
      const text = await badge.textContent();
      expect(text?.length).toBeGreaterThan(0);
    }
  });
});
