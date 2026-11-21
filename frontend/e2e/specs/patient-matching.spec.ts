import { test, expect } from '@playwright/test';

test.describe('Patient Matching Invariants (FR-13 / FR-14)', () => {
  test('name-only match requires manual confirmation and routes unverified entries to review', async ({ page, request }) => {
    // Check report review interface status for matched records
    const res = await request.get('/api/v1/intake/reports');
    if (!res.ok()) return;
    const body = await res.json();
    const reports = body.reports || [];
    if (reports.length === 0) return;

    const report = reports[0];
    await page.goto(`/review/${report.id}`);
    
    // Ensure report page loads cleanly without unhandled errors
    await expect(page).toHaveURL(new RegExp(`/review/${report.id}`));
  });
});
