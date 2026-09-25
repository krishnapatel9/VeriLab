# UI/UX Design Document
## OCR Lab-Report Consultation System

**Version:** 0.1 (draft) · **Date:** 25 September 2026

This document defines the key screens, the uncertainty design system (the single most important UX system in this product), and interaction patterns. It assumes a React/TypeScript + Tailwind implementation.

---

## 1. Design Principles

1. **Uncertainty must be impossible to miss, and impossible to mistake for confirmed data.** No exceptions.
2. **Every clinical value is one click from its source.** The original document is never more than one action away.
3. **The doctor's screen is deliberately narrow.** Show only what the consultation needs; disclose, don't hide, the rest.
4. **No diagnostic language anywhere in copy.** UI text is reviewed against Section 9 of the PRD (non-goals) as a checklist.
5. **Color is never the only signal.** Every status uses icon + text + color together, for accessibility and for print/grayscale contexts.

---

## 2. The Uncertainty Design System

This is a shared component set used across Review and Consultation screens.

| Status | Badge | Icon | Color (supplementary only) | Copy |
|---|---|---|---|---|
| `extracted_unverified` | "Unverified" | ⏳ | Gray | "Not yet reviewed" |
| `needs_review` | "Needs review" | ⚠ | Amber | "OCR confidence below threshold — not verified against original report" |
| `verified_as_reported` | "Verified" | ✓ | Green | "Confirmed against original report" |
| `corrected_by_reviewer` | "Corrected" | ✎ | Blue | "Value corrected by reviewer — see history" |
| `rejected` | "Illegible" | ✕ | Red | "Could not be reliably extracted — see original" |
| `superseded_by_amended_report` | "Superseded" | ↻ | Slate | "Replaced by an amended report" |

**Hard rule:** the `needs_review` and `extracted_unverified` styles must never share a visual treatment with `verified_as_reported` beyond typography — no shared "clean confirmed-looking" default that a badge merely sits on top of. Badges are inline in the row, not a hover-only tooltip.

---

## 3. Key Screens

### 3.1 Upload Screen (Uploader)
- Large drop zone / camera-capture button.
- Patient lookup: search-as-you-type by patient ID first (primary), name second (secondary, with a persistent inline note: "Name match alone will not auto-confirm identity").
- Optional fields: consultation type, consultation ID.
- Post-submit state: report ID + processing status, no clinical content shown.

### 3.2 Review Queue (Clinical Reviewer)
- Table: Patient (partial mask per role), Flag reasons (chips), Confidence, Age in queue, Priority (critical-flag items pinned top, visually distinct row background).
- Sort/filter by flag type, tenant, priority.

### 3.3 Review Detail (Clinical Reviewer) — core screen
- **Split-pane layout:** left = original document viewer (PDF/image) with the flagged bounding box highlighted and zoomable; right = extracted field detail.
- Right pane per field: raw OCR value (large, monospace to make ambiguity visible — e.g., `1.2` vs `12`), confidence score, flag reason, three actions: **Verify as reported / Correct / Reject**.
- Correct action opens an inline form: new value, required reason (short text or reason-code dropdown), submit — no correction submits without a reason (enforces FR-20).
- Patient-mismatch variant: candidate patient cards side-by-side with matching/conflicting identifiers highlighted; explicit "Select this patient" or "Escalate — cannot determine" actions; no default selection.

### 3.4 Consultation View (Consulting Doctor) — primary screen
- **Header band:** patient name + ID, consultation type, lab, report date, collection date, status badge (Final/Preliminary/Amended), report ID, link to original ("View original report").
- **Critical Alerts banner** (only if present): red/high-contrast band above the results table, cannot be dismissed without the "Acknowledge" action; expands to full detail on click.
- **Results table:** Test | Result | Unit | Reference range | Flag | Verification (uses the badge system above) | "Open in original" icon-button per row.
- **Disclosure footer:** "N additional results are present in the original report and are not included in this summary. [View all results]"
- Doctor cannot edit; no edit affordances rendered for this role at all (not just disabled — absent).

### 3.5 "View All Results" Screen (Consulting Doctor)
- Same table pattern as Consultation View but unfiltered, with an added "Included in summary?" column and, where excluded, the exclusion reason (not on list / below confidence pending review / rejected).

### 3.6 Critical Alert Detail (Consulting Doctor)
- Exact printed flag text (verbatim, quoted styling to signal "this is what the report says," not a system judgment).
- Source location thumbnail + "Open in original" jump.
- Verification status.
- Prominent copy: "Critical flag printed on report." Never a diagnostic sentence.
- "Acknowledge" button — confirmation modal shows what will be logged (identity + timestamp) before submission.

### 3.7 Consultation-Type Rules Editor (Clinical Administrator)
- Left: list of existing consultation types + version history.
- Right: test-list builder — searchable checklist from the org's test dictionary; system-suggested tests appear in a visually separate "Suggested (not yet approved)" section with an explicit "Add to list" action per suggestion.
- "Approve & Publish" primary action — requires typed confirmation for safety (e.g., type the consultation type name) given downstream clinical impact.

### 3.8 Audit Log Viewer (Security/Audit Admin)
- Filter bar: event type, user, patient, date range.
- Table: Timestamp, Actor, Event, Patient/Report reference, Result (success/denied).
- Export action, itself logged.

---

## 4. Responsive & Accessibility Notes

- Doctor-facing screens must work well on tablet (common in-consultation device) — split-pane Review Detail is desktop/reviewer-focused and can collapse to tabs on narrower viewports.
- WCAG AA minimum contrast for all status badges; icon+text redundancy already covers colorblind accessibility.
- Original-document viewer must support pinch-zoom and keyboard navigation between flagged regions.

---

## 5. Content/Copy Guardrails (enforced in UI review, not just engineering)

Banned patterns in any UI string, tooltip, or system-generated notification:
- "This indicates [condition]"
- "Patient has [diagnosis]"
- "This result is safe / normal" as a system judgment (only the report's own printed reference range / flag may be shown, verbatim)
- Any imperative treatment language ("start," "stop," "adjust dosage")

Permitted pattern: "[Value] is outside the reference range printed on the report ([range])." — describes the report, not the patient's condition.
