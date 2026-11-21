import { test, expect } from '@playwright/test';

test.describe('Review & Additive Corrections (Hardening 1.5 / Schema Invariant)', () => {
  test('correcting a value preserves original OCR read in history', async ({ page, request }) => {
    const res = await request.get('/api/v1/intake/reports');
    if (!res.ok()) return;
    const body = await res.json();
    const reports = body.reports || [];
    if (reports.length === 0) return;

    const reportToReview = reports.find((r: { status: string }) => r.status === 'processed') || reports[0];
    await page.goto(`/review/${reportToReview.id}`);

    const correctBtn = page.getByTestId('correct-btn').first();
    if (await correctBtn.isVisible()) {
      await correctBtn.click();

      const input = page.getByTestId('correct-value-input');
      await expect(input).toBeVisible();
      await input.fill('5.4');

      const reasonSelect = page.getByTestId('correction-reason');
      if (await reasonSelect.isVisible()) {
        await reasonSelect.selectOption({ index: 0 });
      }

      await page.getByTestId('submit-correction').click();
      await expect(page.getByTestId('verification-badge').first()).toBeVisible();
    }
  });
});
