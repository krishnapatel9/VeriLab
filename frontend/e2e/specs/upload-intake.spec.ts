import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Upload & Intake Flow (FR-01 / FR-02)', () => {
  test('file input accepts pdf files and triggers upload state', async ({ page }) => {
    await page.goto('/');

    const fileInput = page.getByTestId('file-input');
    await expect(fileInput).toBeAttached();

    // Create a dummy PDF buffer for testing UI upload
    await fileInput.setInputFiles({
      name: 'test-lab-report.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF'),
    });

    const uploadBtn = page.getByTestId('upload-button');
    await expect(uploadBtn).toBeVisible();
  });
});
