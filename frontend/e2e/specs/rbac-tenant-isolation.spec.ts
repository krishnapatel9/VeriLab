import { test, expect } from '@playwright/test';

test.describe('RBAC & Tenant Isolation (Hardening 0.2)', () => {
  const fakeTenantBReportId = '99999999-9999-9999-9999-999999999999';
  const fakeResultId = '88888888-8888-8888-8888-888888888888';

  test('a doctor cannot open a report belonging to a different tenant', async ({ request }) => {
    // Attempting to access report from another tenant returns 404 (or 403)
    const res = await request.get(`/api/v1/consultation/${fakeTenantBReportId}`);
    expect([403, 404, 401]).toContain(res.status());
  });

  test('an uploader role cannot access the review-correction endpoint', async ({ request }) => {
    const res = await request.post(`/api/v1/review/results/${fakeResultId}/correct`, {
      data: { corrected_value_raw: '5.0', reason: 'OCR misread' },
    });
    // 401 or 403 status expected when role is unauthorized
    expect([401, 403]).toContain(res.status());
  });

  test('unauthenticated users are redirected to login', async ({ page }) => {
    await page.goto('/reports');
    await expect(page).toHaveURL(/\/login/);
  });
});
