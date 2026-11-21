import { test as base, request, APIRequestContext } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const ROLES = ['uploader', 'reviewer', 'doctor', 'admin'] as const;
export type RoleName = typeof ROLES[number];

export const EMAIL_MAP: Record<RoleName, string> = {
  uploader: 'uploader@synth.verilab',
  reviewer: 'reviewer@synth.verilab',
  doctor: 'doctor@synth.verilab',
  admin: 'admin@synth.verilab',
};

export async function globalLoginSetup(baseURL: string) {
  const api: APIRequestContext = await request.newContext({ baseURL });
  const authDir = path.join(process.cwd(), 'e2e', '.auth');
  fs.mkdirSync(authDir, { recursive: true });

  for (const role of ROLES) {
    const email = EMAIL_MAP[role];
    const password = process.env.E2E_TEST_PASSWORD ?? 'dev123';

    try {
      const res = await api.post('/api/v1/auth/login', {
        form: { username: email, password },
      });
      if (res.ok()) {
        const body = await res.json();
        const access_token = body.access_token;
        fs.writeFileSync(
          path.join(authDir, `${role}.json`),
          JSON.stringify({
            cookies: [],
            origins: [{ origin: baseURL, localStorage: [{ name: 'auth_token', value: access_token }] }],
          })
        );
      }
    } catch {
      // Setup helper continues gracefully if role is unseeded
    }
  }
}

export const uploaderTest = base.extend({
  storageState: 'e2e/.auth/uploader.json',
});

export const reviewerTest = base.extend({
  storageState: 'e2e/.auth/reviewer.json',
});

export const doctorTest = base.extend({
  storageState: 'e2e/.auth/doctor.json',
});
