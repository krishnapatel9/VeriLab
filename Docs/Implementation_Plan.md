# Implementation Plan
## OCR Lab-Report Consultation System

**Version:** 0.1 (draft) · **Date:** 25 September 2026

This plan operationalizes the five phases from the PRD into concrete milestones, team needs, and dependencies.

---

## 1. Team Composition (minimum viable team)

| Role | Count | Phase active |
|---|---|---|
| Tech lead / architect | 1 | All phases |
| Backend engineers (FastAPI/Postgres) | 2–3 | All phases |
| Frontend engineer (React/TS) | 2 | Phase 1 onward |
| DevOps / infra engineer | 1 | Phase 0 onward (part-time until Phase 2) |
| QA / test engineer | 1 | Phase 1 onward |
| Clinical/product advisor (part-time) | 1 | All phases — validates test dictionaries, review copy, critical-flag policy |
| Legal/compliance consultant (DPDPA) | contracted | Phase 0, Phase 3 gate |
| Security reviewer (pen-test) | contracted | Phase 4 |

---

## 2. Phase 0 — Discovery & Safety Design (target: 3–4 weeks)

**Goals:** de-risk everything that would be expensive to change later.

| Milestone | Owner | Output |
|---|---|---|
| Confirm tenant onboarding model & pilot tenant candidates | Product | List of 1–3 pilot labs/clinics |
| Build sample-report corpus (skewed photos, low-res scans, multi-page, amended reports, `<`/`>` values, units-on-separate-lines cases) | Product + Clinical advisor | De-identified/synthetic corpus, versioned |
| OCR vendor evaluation against TRD §7 criteria | Tech lead | Vendor decision + signed data-processing terms |
| DPDPA legal review kickoff | Legal | Compliance checklist, retention/consent policy draft |
| Critical-result policy definition | Clinical advisor + Product | Documented policy (alert routing, acknowledgement SLA) |
| Infra baseline (Terraform, environments, CI/CD skeleton) | DevOps | `dev` and `staging` environments live |

**Gate to Phase 1:** signed-off PRD (done), sample corpus ready, OCR vendor selected, legal review in progress (not required to be complete).

---

## 3. Phase 1 — Vertical-Slice Prototype (target: 4–6 weeks)

**Goal:** one complete path through the system, thin but real, on synthetic data only.

| Sprint | Focus |
|---|---|
| Sprint 1 | Intake Service (upload, hash, basic validation) + Object Storage wiring + `reports`/`results` schema live in `dev` |
| Sprint 2 | OCR Worker integration with chosen vendor; extraction into `results` with confidence + bounding boxes |
| Sprint 3 | Review Detail screen (minimal: split-pane, verify/correct actions) wired to `review_items`/`result_corrections` |
| Sprint 4 | Consultation View (hard-coded single test list) + "open in original" source-linking; Audit events wired across all steps |

**Gate to Phase 2:** internal demo completes all 7 steps in PRD §Phase 1 definition without manual DB intervention.

---

## 4. Phase 2 — Safety-Focused MVP (target: 8–10 weeks)

Builds out the full FR-1 through FR-38 set from the PRD.

| Sprint | Focus |
|---|---|
| Sprint 5 | Patient Matching Service (full matching signal set, conflict/missing routing) |
| Sprint 6 | Confidence routing with field-specific thresholds; review-status model fully implemented |
| Sprint 7 | Rules Service: consultation-type versioning, approval workflow, admin UI |
| Sprint 8 | Consultation API with full RBAC scoping; disclosure banner; "view all results" screen |
| Sprint 9 | Critical-alert pipeline (detection → alert → notification → acknowledgement) |
| Sprint 10 | RBAC across all six personas; audit log viewer; hardening pass on tenant isolation (automated cross-tenant-access tests in CI) |

**Gate to Phase 3:** all release gates in PRD §4 pass against the synthetic + de-identified corpus:
- 100% source-link coverage
- 0% uncertain-values-shown-as-confirmed
- 0 patient-mismatch incidents in test suite
- 100% critical-flag surfacing regardless of test-list filtering

---

## 5. Phase 3 — Clinical Pilot (target: 8–12 weeks)

| Milestone | Detail |
|---|---|
| Legal review sign-off | DPDPA compliance checklist fully closed; tenant data-processing agreements signed |
| Pilot tenant onboarding | 1–3 clinics, real (de-identified or consented) data |
| Double-review sampling | A defined % of reports independently double-reviewed to measure correction/omission rates |
| Incident reporting process live | Any patient-mismatch or missed-critical-flag event triggers a defined incident review, not just a bug ticket |
| Metrics collection | Track PRD §4 metrics in production for the pilot cohort |

**Gate to Phase 4:** correction/omission rates within an agreed acceptable range (defined with clinical advisor before pilot start); zero patient-mismatch incidents; doctors report the workflow as net time-positive.

---

## 6. Phase 4 — Integration & Scale (target: ongoing, 10+ weeks for first milestone set)

| Milestone | Detail |
|---|---|
| SMART on FHIR launch | OAuth-based EHR context launch |
| FHIR export/import | `Patient`, `DiagnosticReport`, `Observation`, `DocumentReference`, `Provenance` mapping live |
| Multi-tenant hardening | Load testing at target tenant scale; per-tenant resource quotas |
| Multi-lab / multi-language | Expand OCR/test-dictionary support |
| DR testing | Formal RTO/RPO validation drill |
| Penetration testing | Third-party security assessment before general availability |
| Operational dashboards | Tenant-facing usage/quality dashboards |

---

## 7. Cross-Phase Workstreams

- **AI-assisted development governance:** the AI Context Core doc (companion document) applies from Sprint 1 onward — every AI-agent-generated PR is checked against it before human review, not after.
- **Testing discipline:** every safety-critical path (patient matching, critical-flag surfacing, correction versioning, tenant isolation) requires automated tests before merge — no exceptions, enforced in CI.
- **Documentation:** this plan, the PRD, TRD, and Backend Schema are living documents — schema or scope changes require a corresponding doc update in the same PR/change set.

---

## 8. Key Dependencies & Risks to Track

| Dependency/Risk | Mitigation |
|---|---|
| OCR vendor data-processing terms delay | Start Phase 0 vendor evaluation immediately; have a fallback vendor shortlisted |
| DPDPA legal review timeline uncertain | Run in parallel with Phase 1–2 engineering; treat as a hard gate only for Phase 3, not earlier phases |
| Sample corpus doesn't cover enough edge cases | Clinical advisor reviews corpus completeness before Phase 1 sign-off |
| Pilot tenant real-data availability | Confirm at least one pilot tenant's data-sharing agreement before Phase 3 starts, not during |
