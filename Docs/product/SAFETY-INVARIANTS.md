# Safety Invariants

These invariants are the non-negotiable engineering rules that must be enforced at the architectural and database levels. If any feature violates these invariants, development must halt.

## 1. Immutable Original Documents
*   **Rule:** The original uploaded document (PDF/Image) is immutable.
*   **Enforcement:** Stored in write-once object storage. The file hash (SHA-256) is recorded at the moment of intake and cannot be altered.

## 2. Authoritative Raw Values
*   **Rule:** The raw printed text extracted by the OCR is authoritative. Normalized values are for convenience only.
*   **Enforcement:** Exact printed strings (e.g., `<5`, `>100`, `Positive`, `-2.4`) must be preserved exactly as extracted. The system must never auto-convert ambiguous strings into numerical assumptions.

## 3. Patient Matching Boundaries
*   **Rule:** The system must **never** automatically confirm a patient match based on name similarity alone.
*   **Enforcement:** Exact, unique Patient IDs may trigger an auto-pass depending on tenant policy. Conflicting, missing, or name-only identifiers **must** be routed for human review.

## 4. Additive Correction Versioning
*   **Rule:** Human corrections must never overwrite the original OCR result in the database.
*   **Enforcement:** Corrections must be recorded as new versioned entries (e.g., in an append-only `result_corrections` table). The record must retain the original OCR value, corrected value, reviewer identity, timestamp, reason, and source evidence.

## 5. Traceable Uncertainty
*   **Rule:** The system must never display an unverified result as confirmed, nor hide uncertainty.
*   **Enforcement:** Results must carry explicit verification statuses (`needs_review`, `verified_as_reported`). The UI must use text, icons, and badges (not color alone) to clearly indicate unverified data.

## 6. Critical Flags Surface Everywhere
*   **Rule:** Critical or abnormal flags printed on the report must always be surfaced to the clinician.
*   **Enforcement:** A critical result must not be hidden just because that specific test was filtered out of the current consultation view configuration.

## 7. Verifiable Tenant Isolation
*   **Rule:** Data must be strictly isolated between tenants.
*   **Enforcement:** Row-Level Security (RLS) must be implemented and enforced on every tenant-scoped table at the PostgreSQL database layer, never solely relying on application-level filtering.

## 8. Append-Only Audit Trails
*   **Rule:** Audit events must not be deleted or altered.
*   **Enforcement:** The `audit_events` table must be insert-only, restricted by database roles, and utilize hash-chaining to ensure tamper evidence.
