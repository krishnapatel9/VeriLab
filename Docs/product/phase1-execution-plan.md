# Phase 1: Vertical Slice Execution Plan

With Phase 0 product constraints and safety invariants locked, this plan details how we will execute the **Phase 1 Vertical Slice**.

**The Goal:** Build ONE complete, end-to-end working path using synthetic data—from file upload to the final consultation view and audit log—without requiring manual database changes.

## Sprint 1: Intake Pipeline (Weeks 1-2)
*   **Focus:** File ingestion, integrity, and storage.
*   **Tasks:**
    *   Initialize the React Frontend (`npx create-react-app` or Vite).
    *   Build the `UploadDropzone` component.
    *   Connect Frontend to the `/api/v1/intake/upload` endpoint (already stubbed).
    *   Implement actual local object storage logic (or MinIO for dev).
    *   Write E2E tests for the Intake flow ensuring immutable hashes are recorded.

## Sprint 2: OCR Integration & Extraction (Weeks 2-3)
*   **Focus:** Wiring up the managed OCR provider and saving structured data.
*   **Tasks:**
    *   Create the `OCRProvider` interface.
    *   Implement the integration with the chosen managed OCR vendor.
    *   Map the raw OCR JSON response to the `results` table schema (ensuring bounding boxes and confidence scores are preserved).
    *   Implement webhook handlers to receive asynchronous OCR completions.

## Sprint 3: Review & Correction Interface (Weeks 3-4)
*   **Focus:** The human-in-the-loop safety net.
*   **Tasks:**
    *   Build the side-by-side Review UI (PDF viewer on left, extracted data on right).
    *   Implement the API for submitting corrections (`/api/v1/review/correct`).
    *   **Crucial:** Enforce the additive correction invariant (write new rows to `result_corrections`, never update `results` directly).
    *   Implement the state machine transition from `needs_review` to `verified_as_reported`.

## Sprint 4: Consultation View & Audit (Weeks 4-5)
*   **Focus:** The clinician's final dashboard.
*   **Tasks:**
    *   Build the `ConsultationDashboard` component.
    *   Implement the `/api/v1/consultation` endpoint utilizing a mock/hard-coded rule set (since the dynamic rules engine is Phase 2).
    *   Build the "Source Verification" feature allowing clinicians to click a test value and highlight the bounding box in the original PDF.
    *   Ensure all actions across Sprints 1-4 are actively logging to the `audit_events` table.

## Phase 1 Exit Gate
We will not proceed to Phase 2 (Safety MVP) until we can successfully demonstrate an uploaded synthetic report flowing cleanly through all these steps via the UI.
