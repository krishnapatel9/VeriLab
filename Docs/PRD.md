# Product Requirements Document (PRD)
## OCR Lab-Report Consultation System

**Version:** 0.1 (draft for review)
**Date:** 25 September 2026
**Status:** Draft — pending stakeholder sign-off

---

## 1. Product Vision

A **clinician-facing lab-report interpretation and retrieval system** that converts scanned lab reports, photos, and PDFs into a traceable, permission-controlled consultation view — showing only the tests relevant to a given appointment, alongside their exact source location in the original document.

**The system extracts and organizes reported facts. It never invents, silently modifies, discards, or clinically interprets a result.** This is the non-negotiable design principle behind every requirement below.

**Product category:** Reviewable clinical information-management tool. **Not** a diagnostic or treatment-recommendation system. This positioning is deliberate — it keeps the v1 product outside the heavier medical-device regulatory tier in most jurisdictions, India included, and it must not drift during implementation.

---

## 2. Problem Statement

Doctors currently review lab reports as flat documents (PDFs, photos, scans) with no structure, no relevance filtering for the specific consultation, and no fast way to verify an OCR-derived number against the source. This creates two risks:

1. **Clinically important results are missed or take too long to find** inside long, unstructured reports.
2. **Any automated extraction layer introduces a new risk** — a misread decimal, dropped minus sign, or swapped reference range — if it isn't paired with visible uncertainty and one-click verification against the original.

The product must solve for *speed and relevance* without weakening a doctor's ability to trust or double-check what they're seeing.

---

## 3. Target Market & Deployment Model

- **Deployment:** Multi-tenant SaaS, serving multiple independent labs, clinics, and hospital groups on shared infrastructure with strict tenant isolation.
- **Initial market:** India.
- **Regulatory posture:** Governed primarily by the **Digital Personal Data Protection Act (DPDPA), 2023**, now operational under the 2025 DPDP Rules. Key implications for design:
  - The system is a **Data Fiduciary**; each tenant (lab/clinic) is also a fiduciary for their own patients — the platform's contracts and access model must reflect this shared responsibility.
  - Digitizing a physical/scanned report brings it into DPDPA's scope as digital personal data — treat every uploaded report as regulated data from the moment of upload, not just after structuring.
  - Consent capture (for patient data processing), breach intimation procedures, data retention limits, and cross-border transfer safeguards are mandatory design inputs, not later add-ons — data residency (India-based storage/processing) should be the default assumption unless a tenant contract says otherwise.
  - A Data Protection Board now exists for enforcement — audit-readiness (Section 8 of this PRD) is a compliance requirement, not just a security nicety.
  - This PRD is not legal advice — a formal DPDPA compliance review with counsel is a Phase 0 gate before pilot (see Section 10).

---

## 4. Goals & Success Metrics (v1)

| Goal | Metric | Target for pilot exit |
|---|---|---|
| Doctors trust the view enough to use it as their primary reference | % of consultations where doctor opens original PDF anyway | Trend downward over pilot, tracked not gated |
| Uncertain data never looks confirmed | % of `needs_review` results incorrectly rendered without a badge | 0% (release gate, not a target) |
| No patient-mismatch incidents | Count of results attributed to wrong patient in production | 0 (release gate) |
| Fast enough to be adopted | Median time from upload to doctor-ready view | < 5 minutes for digital PDFs |
| Reviewers can keep up | Median review-queue time per flagged report | < 10 minutes |
| Every result is traceable | % of displayed results with a working source link | 100% (release gate) |
| No critical result hidden by filtering | % of printed critical flags surfaced regardless of consultation test list | 100% (release gate) |

---

## 5. Personas

| Persona | Role | Primary need |
|---|---|---|
| **Uploader** | Patient, front-desk staff, or lab | Upload a report and confirm basic patient info correctly |
| **Clinical Reviewer** | Trained internal staff or clinician | Resolve `needs_review` items accurately and fast |
| **Consulting Doctor** | Licensed clinician, the primary end-user | See only relevant, trustworthy results, verify instantly against source |
| **Clinical Administrator** | Clinic/lab admin | Define consultation types, test-selection rules, manage staff permissions |
| **Security/Audit Administrator** | Platform or tenant compliance staff | Review access, correction, and download logs; respond to DPDPA obligations |
| **Tenant Owner** (SaaS-specific) | Lab/clinic organization account owner | Manage their org's users, billing, data-residency settings, branding |

---

## 6. Scope: v1 (MVP) Functional Requirements

Organized by workflow stage. Every item here is a **must-have** — nothing in this section is deferred.

### 6.1 Upload & Intake
- FR-1: Accept scanned PDF, photo, image file, digitally-generated PDF.
- FR-2: Compute and store a file hash at intake; store the original file immutably and unmodified.
- FR-3: Capture uploader identity, timestamp, and optional metadata (patient ID, consultation ID, consultation type).
- FR-4: Validate file type, size, page count, corruption/encryption status, and emptiness before processing; reject with a clear reason if invalid.
- FR-5: Run malware scanning before the file touches any processing pipeline.
- FR-6: Detect (not silently split) the case where multiple reports appear combined in a single upload; route to manual review.

### 6.2 OCR & Structured Extraction
- FR-7: Extract patient name/ID, lab/facility name, report date, collection date, report status (final/preliminary/amended/corrected/unknown), and per-result test name, value, unit, reference range, and printed flag.
- FR-8: Store a bounding box / coordinate location for every extracted field, tied to the specific page.
- FR-9: Preserve raw printed text exactly (`<5`, `>100`, `Positive`, `Trace`, `Not detected`, negative signs) alongside any normalized version — raw is authoritative, normalized is a display convenience.
- FR-10: Record a confidence score per field (not one document-level score).

### 6.3 Patient Matching
- FR-11: Treat patient matching as a distinct safety gate, separate from extraction.
- FR-12: Exact patient-ID match may auto-pass, subject to tenant policy configuration.
- FR-13: Name-only match is never sufficient to auto-confirm.
- FR-14: Conflicting identifiers block the report and require human review.
- FR-15: Missing identifiers route to manual review.
- FR-16: Never merge results from two reports based on name similarity alone; every result retains its report ID and patient ID.

### 6.4 Confidence & Review Routing
- FR-17: Apply field-specific (not uniform) confidence thresholds — patient ID, result value, unit, and reference range carry different risk profiles and different thresholds.
- FR-18: Auto-flag for review: ambiguous decimal points, unclear `<`/`>`, uncertain minus signs, missing/inconsistent units, incomplete reference ranges, ambiguous test names, uncertain patient identity, unclear report status, any detected critical/abnormal flag, overlapping-column layouts, and values that don't fit the expected format for that test.
- FR-19: Support the review-status model: `extracted_unverified`, `needs_review`, `verified_as_reported`, `corrected_by_reviewer`, `rejected`, `superseded_by_amended_report`.
- FR-20: A reviewer correction must retain: original OCR value, corrected value, reviewer identity, timestamp, reason, evidence location, prior versions, and an optional comment. Corrections are additive versions, never overwrites.

### 6.5 Rules Engine
- FR-21: Consultation-type → test-list mapping is configuration-driven, versioned, and requires clinical-admin approval — never hard-coded or inferred by a model from free text in v1.
- FR-22: Every consultation view stores which rule version produced it.
- FR-23: Any system-suggested test addition must be visibly labeled as a suggestion, not an approved selection.
- FR-24: The engine must never silently drop an unmatched/unselected result — it is excluded from the *view*, not from the record, and its exclusion is disclosed (see FR-27).

### 6.6 Consultation View
- FR-25: Header shows patient name, patient ID, consultation type, lab name, report date, collection date (if available), report status, report ID, verification status, and a link to the original report.
- FR-26: Results table shows test, result, unit, reference range, printed flag, and verification status per row; supports "open in original" navigation to the exact source region.
- FR-27: Displays a disclosure banner when results exist outside the selected list (e.g., "12 additional results are present in the original report and are not included in this summary"), with a path to view them.
- FR-28: Uncertain values are visually unmistakable — badge plus text plus icon, never color alone; no styling may make an unverified value look final.
- FR-29: Critical flags appear in a dedicated alert section regardless of whether the test is on the consultation's selected list.
- FR-30: The doctor can always open the complete original document and the complete extracted result set, with the reason any result was excluded from the summary.

### 6.7 Critical-Result Handling
- FR-31: Preserve and prominently display the exact printed critical flag; never auto-generate a diagnostic statement from it (the copy is "Critical flag printed on report," never "Patient has condition X").
- FR-32: Create a trackable alert/work item per tenant policy when a critical flag is detected.
- FR-33: Record clinician acknowledgement of each critical alert.

### 6.8 Access, Roles & Audit
- FR-34: Enforce access at tenant, patient, encounter/consultation, and role level — application access does not imply access to every patient's data.
- FR-35: Role-based access for the six personas in Section 5, configurable per tenant.
- FR-36: Multifactor authentication required for all clinical and administrative roles.
- FR-37: Append-only audit log for: upload, OCR processing, patient-match decision, report opened, result viewed, original viewed, correction made, correction approved, download, share, access denied, critical-result acknowledgement, configuration change, permission change.
- FR-38: Audit records are tamper-evident and accessible to authorized tenant and platform auditors.

---

## 7. Explicit Non-Goals for v1

Deferred deliberately — pulling these forward would slow the safety-critical core:

- No diagnostic suggestions, treatment recommendations, or free-text clinical interpretation.
- No autonomous test-relevance model — test lists are explicit, admin-approved dictionaries only.
- No FHIR/SMART-on-FHIR EHR integration (target: Phase 4).
- No LOINC/SNOMED/UCUM terminology mapping beyond a simple internal test-name dictionary (target: post-pilot).
- No patient-facing portal.
- No multi-language OCR beyond the pilot tenant's primary language(s).
- No handwriting-heavy report support beyond what the chosen OCR vendor handles out of the box.

---

## 8. Regulatory, Privacy & Security Requirements

- All data at rest and in transit encrypted; key management and rotation in place.
- Data residency: default to India-based storage and processing per tenant, configurable only with explicit contractual basis.
- Consent capture from patients (via uploader flow) before processing, per DPDPA.
- Defined data retention and deletion policy per tenant, enforced technically (not just documented).
- Breach-intimation procedure that meets DPDPA timelines.
- Tenant data isolation must be verifiable (row-level security or equivalent), not just application-layer convention.
- A formal legal/compliance review (Phase 0 gate) before any pilot with real patient data.
- The product must never be marketed or documented as "DPDPA compliant" on the strength of encryption alone — compliance requires organizational process, contracts (fiduciary/processor terms with each tenant), risk assessment, and operational controls beyond this PRD's scope.

---

## 9. Release Phases

| Phase | Focus | Exit criteria |
|---|---|---|
| **Phase 0 — Discovery & safety design** | Confirm tenant onboarding model, sample report set (skewed photos, low-res scans, multi-page, amended reports, edge-case values), critical-result policy, retention policy, legal review kickoff | Signed-off PRD + sample corpus + legal engagement started |
| **Phase 1 — Vertical-slice prototype** | One full path: upload → OCR → small field set → review screen → correction → consultation view → source-linked verification → audit events, using synthetic/de-identified data | Internal demo passes all 7 workflow steps |
| **Phase 2 — Safety-focused MVP** | Full feature set in Section 6 | All release gates in Section 4 met on synthetic + de-identified data |
| **Phase 3 — Clinical pilot** | Small clinician group, predefined consultation types, de-identified/approved real data, double-review sampling, incident reporting | Correction/omission rates measured and acceptable; zero patient-mismatch incidents |
| **Phase 4 — Integration & scale** | Multi-tenant hardening, FHIR/SMART launch, multi-lab onboarding, DR testing, pen testing | Passes security review; ready for general availability |

---

## 10. Risks & Assumptions

**Key risks carried from the source research (still open in v1 design):**
- Decimal points, minus signs, or reference-range/result confusion silently corrupting a value.
- A preliminary report shown as final, or an amended report ignored.
- A similar-name patient incorrectly matched.
- A critical flag excluded because its test isn't on the consultation list (mitigated by FR-29, must be verified in testing).
- A correction overwriting rather than versioning the original extraction (mitigated by FR-20, must be enforced at the data layer).
- A third-party OCR vendor retaining patient data beyond agreed terms — vendor contract review required before selection.
- A system "suggestion" being read by a doctor as a diagnosis — copy and UI review required.

**Assumptions to validate in Phase 0:**
- A managed OCR vendor with bounding-box and confidence output is acceptable from a data-residency/DPDPA standpoint for at least one Phase 0 pilot tenant.
- Initial pilot tenants can supply or approve de-identified sample reports covering the edge cases above.

---

## 11. Open Questions (to resolve before Phase 1 build starts)

1. Which OCR vendor(s) are acceptable given India data-residency requirements — managed cloud (with India region) vs. self-hosted?
2. What is the tenant onboarding and billing model (per-report, per-seat, flat SaaS fee)?
3. Who owns the initial test-list dictionaries per consultation type — the platform, or each tenant's clinical admin?
4. What is the target number of pilot tenants and clinicians for Phase 3?
5. Is a DPO (Data Protection Officer) required per tenant, or centrally by the platform, under the applicable DPDPA rules for this data volume?
