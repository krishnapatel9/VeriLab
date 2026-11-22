# Deploying VeriLab for free

Synthetic demo data only. Not for real patient data (see `AUDIT.md`).

| Part | Where | Cost |
|---|---|---|
| Website (React) | Cloudflare Worker (static files) | Free |
| Backend (FastAPI + Tesseract OCR) | Render, free plan | Free |
| Keeps the backend awake | Cloudflare Worker, every 10 min | Free |
| Database (Postgres) and uploaded reports | Neon | Free, 0.5 GB |

No card is needed anywhere.

Do the steps in this order. Keep a notepad open: you'll copy values from one
step into a later one. The values to copy are marked 📋.

---

## 1. Database: Neon

1. Sign up at https://neon.tech.
2. Create a project. Name it `verilab` and pick the region closest to you.
3. On the project dashboard, click **Connect**. Turn **Connection pooling off**,
   then copy the connection string. It looks like
   `postgresql://user:password@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require`.
   Any format Neon offers works (`postgresql://` or `postgresql+psycopg://`).
   📋 **DATABASE_URL**

## 2. Backend: Render

1. Sign up at https://dashboard.render.com, using your GitHub account.
2. Click **New** → **Blueprint**, then connect the **VeriLabb** repo.
3. Render reads `render.yaml` and asks for these values:

   | Key | Value |
   |---|---|
   | `DATABASE_URL` | from step 1 |
   | `ALLOWED_ORIGINS` | `https://example.com` for now. You'll set the real website address in step 5. |
   | `DEMO_USER_PASSWORD` | a strong password you choose |

4. Click **Apply**. The first build takes about 5–10 minutes.
5. Copy the service URL shown at the top of the page, e.g.
   `https://verilab-api.onrender.com`. 📋 **BACKEND_URL**
6. Open `BACKEND_URL/health` in your browser. You should see `"status":"ok"`.

## 3. Website: Cloudflare Worker

1. Sign up at https://dash.cloudflare.com (no card needed for Workers).
2. Open **Workers & Pages** → **Create** → **Import a repository**, connect
   GitHub and pick this repo.
3. Use these settings:

   | Setting | Value |
   |---|---|
   | Project name | `verilab` (must match `name` in `frontend/wrangler.jsonc`) |
   | Build command | `npm run build` |
   | Deploy command | `npx wrangler deploy` |
   | Root directory | `frontend` |

4. Under **Settings → Build → Variables and secrets** (build variables, not the
   runtime ones), add `VITE_API_BASE_URL` = **BACKEND_URL** from step 2, with
   no trailing slash.
5. Deploy (or **Retry build**). When it finishes, copy the site URL, e.g.
   `https://verilab.<your-subdomain>.workers.dev`. 📋 **SITE_URL**

## 4. Keep-awake Worker: Cloudflare

1. In `infrastructure/cloudflare/keepalive/wrangler.toml`, set `BACKEND_URL` to
   your **BACKEND_URL** and push the change.
2. In Cloudflare, **Workers & Pages** → **Create** → **Import a repository**,
   pick this repo again, and use:

   | Setting | Value |
   |---|---|
   | Project name | `verilab-keepalive` (must match `name` in its `wrangler.toml`) |
   | Build command | leave empty |
   | Deploy command | `npx wrangler deploy` |
   | Root directory | `infrastructure/cloudflare/keepalive` |

   Or from a terminal: `cd infrastructure/cloudflare/keepalive`, then
   `npx wrangler login` and `npx wrangler deploy`.
3. Open the Worker's `*.workers.dev` URL. You should see `{"ok":true,...}`.
   From now on, it pings the backend every 10 minutes by itself
   (check **Settings → Trigger events** shows the cron `*/10 * * * *`).

## 5. Connect the pieces

In Render, open **verilab-api** → **Environment**, set `ALLOWED_ORIGINS` to
your exact **SITE_URL** (no trailing slash), and save. Render redeploys by itself.

## 6. Test it

1. Open **SITE_URL**.
2. Log in as `uploader@synth.verilab` with your `DEMO_USER_PASSWORD`, then upload
   `Docs/demo-report.png`.
   Type the password by hand; it must match `DEMO_USER_PASSWORD` exactly, and
   the demo accounts are reset to it every time the backend starts.
3. Log in as `reviewer@synth.verilab` and open the report. Its original image
   should display, which shows file storage is working.

Other demo logins: `doctor@synth.verilab` and `admin@synth.verilab`.

---

## Updating the app later

Run `git push`. Render (backend) and the Cloudflare website Worker both redeploy
automatically. The keep-awake Worker redeploys too if it was set up from the repo.

## If something goes wrong

| Symptom | Fix |
|---|---|
| Website shows "Starting the server…" for a long time | The backend was asleep or is redeploying. Wait about a minute. If it keeps happening, check the Worker URL (step 4.3). |
| Login says "That password isn't right" | Retype `DEMO_USER_PASSWORD` by hand (browser autofill may use an old one), or set a new value in Render and wait for the redeploy. |
| Login fails with a network or CORS error | `ALLOWED_ORIGINS` in Render must exactly match **SITE_URL**, with no trailing slash. |
| Render deploy fails | Open the Render **Logs** tab. A crash on startup usually means a typo in `DATABASE_URL`. |
| Uploaded report shows "missing from storage" | Check that `STORAGE_BACKEND` is `db` in Render's **Environment** tab. |

## Free-plan limits to know

- **Render:** 750 free hours a month, which covers one service running nonstop.
  Keeping a free service awake on purpose is a grey area with Render, so this
  setup suits demos, not anything important.
- **Neon:** the database sleeps when unused and wakes in under a second on the
  next request. The free plan includes 0.5 GB, shared by the data and the
  uploaded reports (enough for hundreds of typical uploads; each is capped at 10 MB).
  If you ever need more file space, switch to Cloudflare R2: set
  `STORAGE_BACKEND=r2` plus the `R2_*` values in Render (R2 needs a card on file).
