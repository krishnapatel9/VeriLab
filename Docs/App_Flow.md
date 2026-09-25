# App Flow Document
## OCR Lab-Report Consultation System

**Version:** 0.1 (draft) · **Date:** 25 September 2026

This document maps every screen-to-screen journey per persona, matched to the functional requirements (FR-#) in the PRD. It is the bridge between the PRD and the UI/UX Design doc.

---

## 1. Global Flow Overview

```
Tenant Owner sets up org
        │
        ▼
Clinical Admin configures consultation types + test lists (FR-21..24)
        │
        ▼
Uploader submits a report ──► Intake validation (FR-1..6)
        │
        ▼
OCR + structured extraction (FR-7..10)
        │
        ▼
Patient matching gate (FR-11..16) ──► if uncertain ──► Review Queue
        │ if confident match
        ▼
Confidence routing (FR-17..18) ──► if any field flagged ──► Review Queue
        │ if fully confident
        ▼
Rules engine applies consultation-type test list (FR-21..24)
        │
        ▼
Consultation View generated, linked to Report ID + Rule version
        │
        ▼
Consulting Doctor opens view (FR-25..30), acknowledges any critical alert (FR-31..33)
        │
        ▼
Every step logged to Audit (FR-37..38)
```

---

## 2. Persona: Uploader

**Entry point:** "Upload Report" action (web or mobile).

1. **Upload screen** — drag/drop or camera capture; select or confirm patient (search by patient ID/name — name-only never auto-confirms per FR-13); optionally tag consultation ID/type.
2. **Intake validation feedback** — inline: "File received," or a rejection reason (corrupt, empty, wrong type, too large, encrypted, multiple reports detected).
3. **Confirmation screen** — report ID assigned, status "Processing." Uploader's role ends here; they are not shown extracted clinical data.
4. **(Optional) Status check** — uploader can check report status (processing / needs review / ready), not the content.

*Exit:* Report enters the OCR pipeline. No further uploader action unless intake flags "multiple reports in one upload," in which case the uploader is prompted to re-split and re-upload.

---

## 3. Persona: Clinical Reviewer

**Entry point:** Review Queue (dashboard, sorted by report age / urgency — critical-flagged items prioritized).

1. **Queue list view** — each row: patient (masked/partial if reviewer's role doesn't require full identity), flagged field types, confidence level, age in queue.
2. **Review detail screen** (the core reviewer screen) — split view: original document (with the flagged region highlighted) alongside the extracted field, its confidence score, and why it was flagged (FR-18's flag reasons rendered as plain text, e.g., "Decimal point uncertain").
3. **Correction action** — reviewer either:
   - **Verifies as reported** (confirms OCR was correct) → status `verified_as_reported`
   - **Corrects** the value → must enter corrected value + reason → status `corrected_by_reviewer`, original retained (FR-20)
   - **Rejects** the field (illegible/unusable) → status `rejected`, doctor sees explicit "illegible in source" marker instead of a blank
4. **Patient-mismatch resolution** (if flagged at matching stage) — reviewer sees candidate patient matches side by side with source identifiers; must explicitly select the correct patient or escalate — the system never auto-selects (FR-13..16).
5. **Batch completion** — once all flagged fields on a report are resolved, report status flips from `needs_review` to ready-to-view; still individually tagged per field (`verified_as_reported` / `corrected_by_reviewer` don't collapse into one document-level flag).

*Exit:* Report becomes available to the rules engine / consultation view generation.

---

## 4. Persona: Consulting Doctor

**Entry point:** Consultation list (their patients, filtered by upcoming/active consultations) or a direct EHR-context deep link (Phase 4).

1. **Consultation View (primary screen)** — as specified in PRD FR-25..30:
   - Header block
   - Critical-alerts banner (if any) — must be acknowledged before it collapses (FR-33)
   - Results table scoped to the consultation-type test list
   - "N additional results not shown" disclosure banner
2. **"Open in original" action** — from any table row, opens the source PDF/image at the exact page and highlights the bounding box (FR-26).
3. **"View all results" screen** — the complete extracted result set for the report, with each excluded-from-summary result showing its exclusion reason (not on approved list vs. below confidence vs. rejected).
4. **Critical Alerts detail screen** — full context on any critical flag: exact printed text, source location, verification status; doctor action = "Acknowledge" (logged with identity + timestamp, FR-33).
5. **Review-history view** (optional drill-in per result) — shows original OCR value → correction chain, reviewer identity, timestamps, reasons (transparency, not editability — doctors don't correct OCR themselves in v1).

*Exit:* No write actions besides critical-alert acknowledgement; all views logged to audit (FR-37).

---

## 5. Persona: Clinical Administrator

**Entry point:** Admin console → "Consultation Types."

1. **Consultation type list** — existing types (e.g., "Diabetes follow-up"), each showing current version, approver, last-updated date.
2. **Test-list editor** — select tests from the org's approved test dictionary; system may suggest additions (visibly labeled "Suggested," FR-23) but admin must explicitly add them.
3. **Approval step** — every change requires an explicit "Approve & publish" action, creating a new version (FR-21..22); prior versions remain queryable (which consultation views used which version).
4. **User & role management** — invite/manage Uploaders, Reviewers, Doctors, Auditors within their tenant; assign patient/encounter-scoped permissions where applicable (FR-34..35).

*Exit:* Published rule versions immediately available to the rules engine for new consultation views (existing views remain pinned to their original version).

---

## 6. Persona: Security/Audit Administrator

**Entry point:** Admin console → "Audit Log."

1. **Audit log viewer** — filterable by event type, user, patient, date range, tenant (platform-level auditors only) (FR-37).
2. **Access-denied report** — dedicated filtered view for failed-access attempts, useful for incident review.
3. **Export** — download filtered audit records (this action is itself logged, per "Report downloaded" event type).
4. **Correction-history report** — all corrections across the tenant in a period, for periodic clinical-quality review (supports Phase 3 pilot metrics).

---

## 7. Persona: Tenant Owner (SaaS-specific)

**Entry point:** Org settings.

1. **Org setup wizard** (first login) — org name, data-residency confirmation, billing details, initial admin invite.
2. **Org settings screen** — branding, default consultation-type templates, integration keys (Phase 4: FHIR/SMART endpoints).
3. **Billing & usage screen** — reports processed, seats active, plan tier.

---

## 8. Cross-Cutting Flow: Amended Report Handling

```
New report uploaded with same patient + accession/order number as an existing FINAL report
        │
        ▼
System detects potential amendment (not auto-merged)
        │
        ▼
Routed to review: reviewer confirms it is an amendment
        │
        ▼
Prior report marked "superseded_by_amended_report" (FR-19) — original NOT deleted or overwritten
        │
        ▼
Doctor's consultation view shows the amended report as current, with a visible link to the superseded version
```
