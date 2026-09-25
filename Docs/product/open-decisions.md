# Resolved Open Questions (Phase 0 Decisions)

The following core questions have been resolved and will serve as the foundation for the Phase 1 MVP architecture.

## 1. OCR Vendor Strategy
*   **Decision:** **Managed OCR initially**, utilizing a provider that supports **India data residency**. 
*   **Engineering Impact:** We will implement an `OCRProvider` abstraction layer (e.g., in `backend/services/ocr_service.py`) so the application is not tightly coupled to the vendor API, allowing a seamless switch to self-hosted models later if required.

## 2. Tenant / Business Model
*   **Decision:** **Per-report pricing** for the pilot and MVP phases.
*   **Engineering Impact:** The system is optimized to track reports as the primary unit of work. Billing metrics can be derived directly by querying the number of reports processed per `tenant_id` within a given billing cycle.

## 3. Test-List Ownership
*   **Decision:** **Global platform dictionary with tenant-level configuration/overrides.**
*   **Engineering Impact:** The `test_dictionary` table will support a global namespace (e.g., where `tenant_id` is null) that tenants can inherit from. Tenant Clinical Admins will manage their specific consultation rule versions mapping to these tests. All mappings will remain strictly versioned and require clinical approval.

## 4. Pilot Size Target
*   **Decision:** **Start small: 2–3 clinics, around 5–10 clinicians.**
*   **Engineering Impact:** Infrastructure scaling limits for the pilot phase can remain conservative. We can prioritize rock-solid stability and deep auditing over massive concurrent throughput. Expansion will be data-driven based on pilot results.

## 5. DPO Responsibility
*   **Decision:** **Central platform handles platform-level privacy/security governance**, while each tenant remains responsible for its own organizational/legal obligations.
*   **Engineering Impact:** We will support distinct roles for `audit_admin` and `tenant_owner` to empower tenants to perform their own compliance duties. The final legal framework around DPO responsibilities remains subject to formal legal/compliance review.
