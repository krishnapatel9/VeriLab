# Deploying VeriLab for free

Synthetic demo data only. Not for real patient data (see `AUDIT.md`).

| Part | Where | Cost |
|---|---|---|
| Website (React) | Cloudflare Pages | Free |
| Backend (FastAPI + Tesseract OCR) | Render, free plan | Free |
| Keeps the backend awake | Cloudflare Worker, every 10 min | Free |
| Database (Postgres) | Neon | Free |
| Uploaded reports | Cloudflare R2 | Free up to 10 GB |

Do the steps in this order. Keep a notepad open: you'll copy values from one
step into a later one. The values to copy are marked 📋.

---

## 1. Database: Neon

1. Sign up at https://neon.tech.
2. Create a project. Name it `verilab` and pick the region closest to you.
3. On the project dashboard, click **Connect**. Turn **Connection pooling off**,
   then copy the connection string. It looks like
   `postgresql://user:password@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require`.
   📋 **DATABASE_URL**

## 2. File storage: Cloudflare R2

1. Sign up at https://dash.cloudflare.com.
2. In the left menu, open **R2 Object Storage**. Cloudflare asks you to add a
   card. You need it to turn on R2, but nothing is charged within the free limits.
3. Click **Create bucket**, name it `verilab-uploads`, and keep the default settings.
   📋 **R2_BUCKET** = `verilab-uploads`
4. Back on the R2 overview page, copy your **Account ID**. 📋 **R2_ACCOUNT_ID**
5. Click **Manage API tokens** → **Create API token**:
   - Permissions: **Object Read & Write**
   - Specify bucket: `verilab-uploads`
   - Click **Create**.
6. Copy the **Access Key ID** and the **Secret Access Key**. The secret is shown only once.
   📋 **R2_ACCESS_KEY_ID**, 📋 **R2_SECRET_ACCESS_KEY**

## 3. Backend: Render

1. Sign up at https://dashboard.render.com, using your GitHub account.
2. Click **New** → **Blueprint**, then connect the **VeriLabb** repo.
3. Render reads `render.yaml` and asks for these values:

   | Key | Value |
   |---|---|
   | `DATABASE_URL` | from step 1 |
   | `ALLOWED_ORIGINS` | `https://verilab.pages.dev` for now. You'll fix it in step 6 if it's different. |
   | `DEMO_USER_PASSWORD` | a strong password you choose |
   | `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET` | from step 2 |

4. Click **Apply**. The first build takes about 5–10 minutes.
5. Copy the service URL shown at the top of the page, e.g.
   `https://verilab-api.onrender.com`. 📋 **BACKEND_URL**
6. Open `BACKEND_URL/health` in your browser. You should see `"status":"ok"`.

## 4. Website: Cloudflare Pages

1. In Cloudflare, open **Workers & Pages** → **Create** → the **Pages** tab →
   **Connect to Git**, then pick the **VeriLabb** repo.
   (If you only see Workers options, look for a "Get started" link for Pages.)
2. Use these build settings:

   | Setting | Value |
   |---|---|
   | Project name | `verilab` |
   | Framework preset | `Vite` (or None) |
   | Root directory | `frontend` |
   | Build command | `npm run build` |
   | Build output directory | `dist` |
   | Environment variable | `VITE_API_BASE_URL` = **BACKEND_URL** from step 3 |

3. Click **Save and Deploy**. When it finishes, copy the site URL, e.g.
   `https://verilab.pages.dev`. 📋 **SITE_URL**

## 5. Keep-awake Worker: Cloudflare

1. Open `infrastructure/cloudflare/keepalive/wrangler.toml` and set
   `BACKEND_URL` to your **BACKEND_URL**.
2. Run these commands from the project folder. The first one opens a browser
   window so you can sign in to Cloudflare:

   ```powershell
   cd infrastructure/cloudflare/keepalive
   npx wrangler login
   npx wrangler deploy
   ```

3. Open the `*.workers.dev` URL it prints. You should see `{"ok":true,...}`.
   From now on, it pings the backend every 10 minutes by itself.

## 6. Connect the pieces

If **SITE_URL** isn't exactly `https://verilab.pages.dev`: in Render, open
**verilab-api** → **Environment**, set `ALLOWED_ORIGINS` to your **SITE_URL**,
and save. Render redeploys by itself.

## 7. Test it

1. Open **SITE_URL**.
2. Log in as `uploader@synth.verilab` with your `DEMO_USER_PASSWORD`, then upload
   `Docs/demo-report.png`.
3. Log in as `reviewer@synth.verilab` and open the report. Its original image
   should display, which shows R2 is working.

Other demo logins: `doctor@synth.verilab` and `admin@synth.verilab`.

---

## Updating the app later

Run `git push`. Render (backend) and Cloudflare Pages (website) both redeploy
automatically. The Worker only needs `npx wrangler deploy` again if you change it.

## If something goes wrong

| Symptom | Fix |
|---|---|
| Website shows "Starting the server…" for a long time | The backend was asleep or is redeploying. Wait about a minute. If it keeps happening, check the Worker URL (step 5.3). |
| Login fails with a network or CORS error | `ALLOWED_ORIGINS` in Render must exactly match **SITE_URL**, with no trailing slash. |
| Render deploy fails | Open the Render **Logs** tab. A crash on startup usually means a typo in `DATABASE_URL` or an R2 value. |
| Uploaded report shows "missing from storage" | Check the four `R2_*` values in Render. |

## Free-plan limits to know

- **Render:** 750 free hours a month, which covers one service running nonstop.
  Keeping a free service awake on purpose is a grey area with Render, so this
  setup suits demos, not anything important.
- **Neon:** the database sleeps when unused and wakes in under a second on the
  next request. The free plan includes 0.5 GB of storage.
- **R2:** 10 GB of storage free.
