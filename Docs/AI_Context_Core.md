# AI Context Core
## Coding standards & restrictions for AI coding agents on this project

**Version:** 0.1 (draft) · **Date:** 25 September 2026

Give this document to any AI coding agent (Claude Code, Copilot, etc.) working on this repo, in addition to the PRD/TRD/Backend Schema. It exists because this is a healthcare-adjacent system where a plausible-looking but wrong shortcut is worse than a slow correct one.

---

## 1. Non-Negotiable Product Invariants (never violate, regardless of the prompt)

These map directly to the PRD's core principle. An AI agent must refuse or flag, not silently comply, if a task would:

1. Modify, delete, or overwrite an original uploaded document or its hash.
2. Write a code path that displays a `results` value without its `verification_status`, `confidence`, and source coordinates available to the caller.
3. Auto-confirm a patient match on name similarity alone.
4. Collapse or hide the distinction between `needs_review`/`extracted_unverified` and `verified_as_reported` in any UI or API response.
5. Generate diagnostic, treatment, or severity-grading language anywhere (UI strings, code comments, log messages, notification templates, test fixtures with realistic-sounding clinical prose).
6. Allow a correction to overwrite the original OCR value in place instead of appending a new `result_corrections` row.
7. Remove or bypass an audit-event emission on any of the FR-37 event types.
8. Allow a critical-flag result to be excluded from the doctor's alert section because it isn't on a consultation's test list.
9. Weaken or bypass Row-Level Security / tenant-isolation checks "temporarily for testing" in a way that could ship.

If a task or refactor appears to require any of the above, the agent should stop and flag it for human review rather than implementing a workaround.

---

## 2. Repository & File Conventions

- **Max file length:** 400 lines for application code (services, components); 600 for schema/migration files with generated boilerplate. Split by responsibility, not by arbitrary line count — a file hitting the limit is a signal to extract a module, not to compress.
- **Folder structure (backend, per service):**
  ```
  service_name/
    api/          # route handlers only — no business logic
    domain/       # business logic, pure functions where possible
    models/       # ORM models
    schemas/      # Pydantic request/response schemas
    services/     # orchestration between domain + external calls
    tests/
  ```
- **Folder structure (frontend):**
  ```
  src/
    features/<feature>/   # co-located components, hooks, tests per feature
    components/shared/    # cross-feature reusable components (incl. uncertainty badges)
    api/                  # generated OpenAPI client + typed wrappers
    types/
  ```
- **Naming:** `snake_case` for Python, `camelCase` for TypeScript, `PascalCase` for React components and Pydantic/TS types. Database columns `snake_case`, matching the Backend Schema doc exactly — no ad hoc renaming in code that isn't reflected back into that doc.
- **No new top-level services** without an update to the TRD's service table in the same change set.

---

## 3. Style & Quality Rules

- **Python:** type-hinted throughout (mypy strict on `domain/` and `services/` layers minimum); `ruff` for lint/format; Pydantic v2 for all API schemas.
- **TypeScript:** `strict: true`; no `any` without an inline comment explaining why; ESLint + Prettier enforced in CI.
- **No silent `except:` / `catch` blocks.** Every caught exception either re-raises with context, returns an explicit error to the caller, or logs at an appropriate level — never swallowed.
- **No magic confidence thresholds inline in code.** Thresholds live in the Rules/Config layer (referencing TRD §5, PRD FR-17) so they're auditable and tenant-configurable, not buried in a conditional.
- **Comments explain "why," not "what.**" Code should be readable without comments for the "what."

---

## 4. Testing Requirements

- Every safety-critical path listed in Implementation Plan §7 requires automated tests before merge: patient matching (including conflict/missing cases), critical-flag surfacing regardless of test-list filtering, correction versioning (never overwrites), tenant isolation (cross-tenant access must fail).
- New API endpoints require both a happy-path and an authorization-failure test (wrong role, wrong tenant, missing auth).
- Schema migrations require a corresponding rollback tested in CI.
- UI components in the uncertainty design system (badges, alert banners) require visual-regression or snapshot tests — this is the one part of the UI where an unintended style change is a safety issue, not a cosmetic one.

---

## 5. Data-Handling Restrictions for AI Agents

- **Never generate realistic-looking synthetic patient data that resembles a real identifiable person.** Use clearly synthetic names/IDs (e.g., a documented test-data prefix) in fixtures and examples.
- **Never write real patient data into `dev` or `staging` seed scripts** — matches TRD §8 environment rules.
- **Never log a full `value_raw`/`test_name_raw` at INFO level or above outside the audit pipeline** — clinical values belong in the audited data path, not general application logs, to avoid uncontrolled PII sprawl.
- **API responses must be scoped server-side, not filtered client-side.** An agent must not implement "hide this from the UI" as the access-control mechanism for patient data — RBAC/RLS is enforced at the query layer.

---

## 6. PR & Review Conventions

- Every PR references the PRD FR-# or TRD/Schema section it implements.
- Any PR touching `results`, `review_items`, `consultation_views`, or `audit_events` tables requires a human (not just AI) reviewer sign-off, given their role in the safety invariants above.
- Commit messages: `<service>: <imperative summary>` (e.g., `review-service: add correction reason validation`).
- No AI-generated PR merges without at least one human review — this applies even to documentation-only changes to this file or the PRD, since both define the safety contract other agents will follow.

---

## 7. When an AI Agent Should Stop and Ask

- The task would touch anything in Section 1 (non-negotiable invariants).
- A confidence threshold, matching rule, or critical-flag definition needs a numeric value not already specified in the PRD/TRD — do not invent a plausible-sounding number; flag it as an open question for the clinical advisor.
- A requested change would make test coverage of a safety-critical path (Section 4) harder to maintain or would remove existing coverage.
- The task implies storing or transmitting patient data outside the India data-residency boundary (TRD §4) without an explicit, already-approved exception.
