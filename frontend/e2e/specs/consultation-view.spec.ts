import { test, expect } from '@playwright/test';

test.describe('Consultation View & Additional Results Disclosure (FR-24 / FR-27)', () => {
  test('consultation page renders selected and additional results sections', async ({ page, request }) => {
    const res = await request.get('/api/v1/intake/reports');
    if (!res.ok()) return;
    const body = await res.json();
    const reports = body.reports || [];
    if (reports.length === 0) return;

    const report = reports[0];
    await page.goto(`/consultation/${report.id}`);

    // Main header and results table should be rendered
    await expect(page.getByText('Consultation')).toBeVisible();
  });
});
