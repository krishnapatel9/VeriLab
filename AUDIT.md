# VeriLab — Brutal Audit

Date: 2026-09-30 · Scope: Docs/, backend/ (all Python), frontend/ (structure + grep), infrastructure/ · Tests run: `pytest tests` → 30 passed.

## Verdict

**Not OK for anything except a synthetic-data demo.** The documentation is excellent and the skeleton is tidy. But the code breaks several of the project's own "non-negotiable" safety invariants. Some of the README's claims are false. The Phase 1 gate is **not met**. Do not show this to a clinician, and do not load real patient data.

| Area | Grade |
|---|---|
| Docs / safety thinking | A− |
| Backend structure, tenant scoping, tests | B |
| Safety invariants actually enforced | **D** |
| OCR / extraction | **F** (fake) |
| Security / production readiness | **D−** |
| Repo hygiene | **D** |
| Frontend | C (works, unverified against invariants, no tests) |

---

## CRITICAL — violates stated safety invariants

**C1. Doctor never sees corrected values.** `consultation.py:_to_schema` returns `r.value_raw`, which is the original OCR value. Corrections live only in `result_corrections`, and nothing joins them into the view. A result corrected from `12.5` to `2.5` shows the doctor `12.5` labelled `verified_with_correction`. This is the worst bug in the repo, because it shows a wrong value with a "verified" badge.

**C2. Unverified critical results are hidden from the doctor.** The consultation query filters to verified statuses *before* the critical bypass. A critical result in `needs_review` or `unverified` is silently dropped. This breaks Invariant 6 and FR-32, and it also breaks Invariant 5 ("never hide uncertainty"). The doctor also gets no "N results pending review" indicator. An empty page looks the same as "nothing abnormal".

**C3. OCR is fake.** `MockOCRProvider` returns the same Jane Doe / Hemoglobin / TSH data for every upload. `TesseractOCRProvider` runs real OCR, **throws the text away**, and returns hard-coded "WBC (Real OCR)" and "Glucose (Real OCR)" rows. On any error it silently falls back to the mock. The README advertises "automated OCR extraction using Tesseract", which is false. In a medical system, fabricated results that look extracted are the most dangerous failure mode.

**C4. `is_critical` is computed wrongly.** Any flag of high, low, h, l, abnormal, `*` is treated as critical. "Abnormal" is not "critical". It also treats a slightly-high value the same as a panic value. The docs say critical detection (FR-31) needs clinician-approved definitions. `AI_Context_Core` explicitly says not to invent these.

**C5. No patient matching exists (FR-11 to FR-16).** `patient_info` from OCR is discarded. `patient_id` is never set, `match_status` stays `unmatched`, and there is no `PatientMatchService`. Invariant 3 is "satisfied" only because the feature is missing. The consultation view doesn't show which patient the report belongs to, so a doctor can't tell.

**C6. Audit log is not reliable.**
- The OCR-completed audit event is written with `flush()` and the session is then closed without `commit()`, so **it is never persisted**. Also `ocr_provider: "MockOCRProvider"` is hard-coded in the metadata.
- `audit.py`'s docstring promises "committed in its own transaction, survives rollback". The code does the opposite: it flushes and leaves the commit to the caller. In `verify` and `correct`, the state change is committed **before** the audit event is written. A crash in between gives you a change with no audit record.
- The hash covers only `prev|type|resource_id|timestamp`. Actor, tenant and metadata (including the corrected values) can be edited without breaking the chain.
- The "previous event" lookup is `ORDER BY created_at DESC LIMIT 1` with no lock or sequence. Concurrent writers fork the chain, and timestamp ties are non-deterministic. Tenant-less events form a separate chain.
- No DB-level insert-only restriction, and no chain-verification code or endpoint. A "tamper-evident" log that nothing ever verifies is decoration.
- Missing events: login, failed login, file view, OCR failure, and critical acknowledgement (FR-37).

**C7. No source verification (FR-29/30, Phase 1 gate item).** There is no `GET /file` endpoint and no viewer or bbox overlay in the frontend. The bounding boxes are stored and returned but can never be shown against the original document. The bbox values are also fake (`x1:100, y1:200`).

**C8. Row-Level Security does not exist (Invariant 7, FR-35).** Isolation is `WHERE tenant_id = …` in application code. The docs call this out as explicitly insufficient. The tests are valid for that app-level check, but the dev DB is SQLite, so the RLS requirement can't even be tested. Phase 0.5 admits Postgres and RLS are not done.

## HIGH — security

- **Default JWT secret** `dev_only_insecure_secret_key…` with no startup guard. If the env var is forgotten in staging or prod, anyone can forge an admin token. Fail hard when `environment != development` and the secret is the default.
- Tokens last **7 days**, have no revocation, and are stored in `localStorage` (XSS-exfiltratable). This is a healthcare app.
- No login rate-limiting or lockout. No MFA, although FR-36 makes it mandatory for clinical roles. `mfa_enabled` is a column nobody reads.
- `require_role` has a silent `admin` bypass. No admin exists in the seed, but nothing in the docs defines admin semantics. The documented roles (`clinical_admin`, `audit_admin`, `tenant_owner`) don't match.
- Upload validation trusts the filename extension only. No magic-byte check, no page-count check (`page_count=1` is hard-coded), and no malware or corruption check (FR-3/4). The 500 handler returns `str(e)` to the client.
- "Immutable, write-once" storage is a local folder written with `open(path, "wb")`. Nothing prevents overwrite or delete. Invariant 1 is not enforced. It's content-addressed by hash, which helps, but that's all.
- `staging.env` is committed and references **Google Document AI in `us`** with a real-looking project ID. That contradicts the India-residency decision and the TRD. `docker-compose.yml` has a hard-coded DB password (fine for dev, but flag it).
- The verify/correct endpoints have no state-machine guard. Anything can be re-verified, and verified-with-correction can be flipped to verified-as-reported without a new correction. There's no "reviewer cannot verify their own upload" rule.

## MEDIUM — correctness and design

- Confidence: one score is copied into all four confidence fields, so field-level confidence (FR-10) is meaningless. The `0.90` threshold lives in `constants.py`. AI_Context says thresholds belong in the Rules layer, but this is acknowledged as Phase 1.
- Status vocabulary drifts from the docs: code uses `unverified`, docs use `extracted_unverified`.
- Consultation test list is `("Hemoglobin",)`, exact string match on raw name. Real reports use "Hb", "HGB", "Haemoglobin", and so on. Without normalization, the selected list will rarely match.
- No async or queue. OCR runs in a FastAPI `BackgroundTask` using `asyncio.run` inside a sync thread, with no retry and no dead-letter. Failures are `print`ed and swallowed (contrary to AI_Context's "no silent catch"). The report status can get stuck at `processing`.
- No pagination on `/reports`. `datetime.utcnow()` is deprecated. `uuid7` is in requirements, but the code uses `uuid4` as a placeholder.
- Dead or duplicate code: `core/config.py` (deprecated, empty), duplicate `emit_audit_event` import and duplicated docstring in `intake.py`, duplicate `import uuid`, and a late import in `dependencies.py`.
- No Alembic migrations exist despite the dependency. `create_all` on startup means any schema change breaks existing DBs. I hit this on day one: the committed dev DB had a stale schema and the app crashed at startup.

## Repo hygiene

- **7,456 tracked `node_modules` files** plus `.pyc` files. `.gitignore` exists but the files were committed first. Both `verilab_dev.db` and `verilab_test.db` are committed, along with uploaded PDFs and PNGs in `mock_storage/`. Run `git rm -r --cached` on all of it.
- `requirements.txt` is all `>=` with no lock file. It is missing `pytesseract`, `pillow`, `pdf2image` and `requests`, and the newest `bcrypt` breaks passlib (`bcrypt<4.1` needed). A fresh install does not work out of the box.
- `backend/test_upload.py` needs `requests` and a live server, so plain `pytest` fails at collection. Move it or delete it.
- No CI, even though the docs require CI for tenant isolation, migrations and security scanning. No frontend tests, no lint config (`npm run lint` references eslint, which isn't installed). AI_Context demands visual-regression tests for uncertainty badges.
- The Consultation view `any` types and `catch (err: any)` blocks violate the repo's own TS rules. No Dockerfile audit was done.

## Docs vs reality

- `development-status.md` says Sprint 4 is "Missing". The code shows it is partially built, so the doc is stale.
- README claims "Automated OCR Extraction using Tesseract" and "Critical Result Detection". Neither is true (C3, C4).
- Traceability matrix: of FR-1 to FR-38, roughly 8 are real (upload, hash, raw values, correction versioning, basic state, basic consultation, basic tenant scoping, partial audit). Roughly 20 are absent (matching, rules service, critical ack, MFA, RLS, source viewer, malware scan, multi-report detection, and so on).
- Missing from docs: Backend_Schema.md defines tables (`consultation_views`, `critical_alerts`, `test_dictionary`, `rules_config`) that don't exist in `core_models.py`.

## What's good (credit where due)

- Safety thinking in the docs is unusually strong. The invariants, non-goals and AI-agent rules are the best part of the repo.
- Correction versioning really is additive (`ResultCorrection` row, `value_raw` never mutated).
- Consistent tenant filter on every query, backed by a real cross-tenant test file.
- Clean layering (routers, services, models, schemas), sensible seed script, and a green test suite with isolation and audit tests.
- The `OCRProvider` abstraction is the right shape.

## Phase 1 gate (docs' own checklist)

| Gate item | Status |
|---|---|
| Upload a synthetic file in the UI | ✅ |
| Hash and original object stored | ⚠️ stored, not immutable |
| OCR results with raw value, confidence, page, bbox | ❌ fabricated data |
| Verify/correct without overwriting `value_raw` | ⚠️ DB yes, doctor view shows the wrong value (C1) |
| Consultation uses hard-coded list, doesn't drop unmatched results | ❌ drops unverified, including critical (C2) |
| Clicking a result shows source coordinates on the original | ❌ |
| Audit events exist for the steps | ⚠️ OCR event lost, chain weak (C6) |
| No SQL/admin console required | ✅ |

**Result: 2 pass, 3 partial, 3 fail.** The gate is not met.

## Fix order

1. C1: join the latest `ResultCorrection` into the consultation response. Show both the original and the corrected value, with a badge.
2. C2: return all results to the doctor. Show unverified ones in a clearly marked "Pending review" section, with criticals pinned at the top regardless of status.
3. C6: commit the audit event in the same transaction as the state change, or in a separate session. Fix the OCR audit commit, add a sequence number or row lock to the chain, hash the full payload, and add a `verify_chain()` function with a test.
4. C3: make the Tesseract provider parse its actual text, or remove it. Never return invented values. Fail loudly, and set the report to `error`.
5. C4: replace the flag heuristics with a config-driven, clinician-approved critical definition. Until then, label flags as "printed flag" and don't call them "critical".
6. Security quick wins: a startup guard on the secret key, a shorter token lifetime, login rate limit, magic-byte upload checks, and no `str(e)` in responses.
7. Hygiene: untrack `node_modules`, `.pyc`, DBs and uploads. Pin dependencies, add a lock file, fix `test_upload.py`, add CI with pytest, plus `npm run build` and lint.
8. Build C7 (file endpoint and bbox viewer), then C5 (matching), then Postgres plus RLS (C8).
