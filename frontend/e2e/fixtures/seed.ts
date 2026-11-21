import { APIRequestContext } from '@playwright/test';

export const TEST_TENANT_ID = '00000000-0000-0000-0000-000000000001';
export const TENANT_B_ID = '00000000-0000-0000-0000-000000000002';

/**
 * Seeds a test report via direct API upload instead of driving UI clicks.
 */
export async function seedReportWithCriticalFlag(api: APIRequestContext, tenantId: string = TEST_TENANT_ID) {
  const samplePdfBuffer = Buffer.from(
    '%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n' +
    '2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n' +
    '3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n' +
    'xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \n' +
    'trailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF'
  );

  const res = await api.post('/api/v1/intake/upload', {
    multipart: {
      file: {
        name: 'critical-tsh.pdf',
        mimeType: 'application/pdf',
        buffer: samplePdfBuffer,
      },
      tenant_id: tenantId,
    },
  });
  return res.json();
}
