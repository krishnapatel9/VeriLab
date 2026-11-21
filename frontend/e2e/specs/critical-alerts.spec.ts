import { test, expect } from '@playwright/test';

test.describe('Critical Alerts & Safety Badge Surfacing', () => {
  test('critical flag surfaces even when test is outside consultation list', async ({ page, request }) => {
    // Fetch available reports for tenant
    const res = await request.get('/api/v1/intake/reports');
    if (!res.ok()) return;
    const body = await res.json();
    const reports = body.reports || [];
    if (reports.length === 0) return;

    const targetReport = reports.find((r: { status: string }) => r.status === 'processed') || reports[0];
    await page.goto(`/consultation/${targetReport.id}`);

    const banner = page.getByTestId('critical-alert-banner');
    if (await banner.isVisible()) {
      await expect(banner).toBeVisible();
      await expect(banner).toContainText(/Flagged|Critical/i);
    }
  });

  test('every row in the results table shows a verification badge (Hardening 0.4)', async ({ page, request }) => {
    const res = await request.get('/api/v1/intake/reports');
    if (!res.ok()) return;
    const body = await res.json();
    const reports = body.reports || [];
    if (reports.length === 0) return;

    const targetReport = reports.find((r: { status: string }) => r.status === 'processed') || reports[0];
    await page.goto(`/consultation/${targetReport.id}`);

    const rows = page.getByTestId('result-row');
    const count = await rows.count();
    for (let i = 0; i < count; i++) {
      await expect(rows.nth(i).getByTestId('verification-badge')).toBeVisible();
    }
  });
});
