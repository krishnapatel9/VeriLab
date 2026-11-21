# Development Status

**Last updated:** 25 September 2026  
**Current phase:** Phase 1 — Vertical-Slice Prototype (Sprint 4 in progress)  
**Do not start Phase 2 until the Phase 1 gate passes.**

## Where the project sits

```text
PHASE 0     Discovery + Safety Foundation     DONE (docs + product decisions)
PHASE 0.5   Architecture / repo / local env  PARTIAL (code exists; no Terraform/CI/Postgres yet)
PHASE 1     Vertical-slice prototype         IN PROGRESS  ← YOU ARE HERE
PHASE 2     Safety-focused MVP               NOT STARTED
PHASE 3     Clinical pilot                   NOT STARTED
PHASE 4     Integration + scale              NOT STARTED
```

Phase 0 product contracts are treated as frozen:

- PRD functional requirements FR-1 → FR-38
- Safety invariants
- Requirements traceability matrix
- Open questions documented as Phase 0 decisions (OCR abstraction, per-report billing for pilot, platform dictionary + tenant overrides, small pilot, split DPO duties pending legal review)

Engineering work remaining in Phase 0.5 (can proceed in parallel, must not block the vertical slice): PostgreSQL 16 + RLS, Terraform, CI/CD, sample-report corpus, signed OCR DPA. Those are **not** Phase 1 feature work.

## Phase 1 objective

One complete synthetic-data path, with **no manual database intervention**:

```text
Upload → OCR → Extract → Review → Correct → Consultation → Source verification → Audit
```

## Sprint status

| Sprint | Focus | Status |
|--------|--------|--------|
| 1 | Intake: upload, hash, immutable store, `reports` row | Partial — upload/hash/store exist; tenant/user were previously fabricated per request |
| 2 | OCR provider abstraction + structured `results` | Partial — `MockOCRProvider` only; not India-region vendor |
| 3 | Review verify/correct without mutating OCR rows | Partial — APIs exist; UI actions were not wired |
| 4 | Hard-coded consultation view, source coords, audit | Missing at last inventory; this is the current build target |

## Phase 1 gate (must all be true)

- [ ] Upload a synthetic file in the UI
- [ ] Hash and original object stored
- [ ] OCR produces results with raw value, confidence, page, bbox
- [ ] Reviewer can verify or correct without overwriting `results.value_raw`
- [ ] Consultation view uses a hard-coded test list and does not drop unmatched results
- [ ] Clicking a result shows source coordinates against the original
- [ ] Audit events exist for the steps above
- [ ] No SQL/admin console required to make the demo work

## Explicitly out of scope until later

Diagnostic/treatment language, FHIR/SMART, LOINC/SNOMED, patient portal, full RBAC/MFA, tenant billing engine, field-specific production thresholds, real OCR vendor cutover.
