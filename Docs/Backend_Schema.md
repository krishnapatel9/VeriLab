# Backend Schema Document
## OCR Lab-Report Consultation System

**Version:** 0.1 (draft) · **Date:** 25 September 2026
**Database:** PostgreSQL 16, Row-Level Security enforced on every tenant-scoped table.

---

## 1. Schema Conventions

- Every tenant-scoped table has a `tenant_id` column and an RLS policy restricting rows to the requesting session's tenant.
- Every table has `created_at`, `updated_at` (UTC timestamptz).
- Soft state transitions (status columns) are never deleted-and-reinserted; history tables capture prior states where traceability is required (results, corrections, rule versions).
- Primary keys are UUIDv7 (time-ordered, index-friendly) except where noted.
- No table representing an original document or an audit event supports `UPDATE` or `DELETE` at the application layer — enforced via restricted DB roles, not just app logic.

---

## 2. Core Tables

### `tenants`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| name | text | |
| data_residency_region | text | default `in-mumbai` (example) |
| status | text | active / suspended |
| created_at / updated_at | timestamptz | |

### `users`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| tenant_id | uuid FK → tenants | nullable for platform-level (cross-tenant) auditors |
| email | text unique | |
| role | text | uploader / reviewer / doctor / clinical_admin / audit_admin / tenant_owner |
| mfa_enabled | boolean | |
| status | text | active / disabled |
| created_at / updated_at | timestamptz | |

### `patients`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| tenant_id | uuid FK | |
| external_patient_id | text | the lab/clinic's own patient ID — primary matching signal |
| full_name | text | |
| date_of_birth | date | nullable |
| sex | text | nullable |
| created_at / updated_at | timestamptz | |

*Unique constraint:* `(tenant_id, external_patient_id)`.

### `reports`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | "Report ID" throughout the product |
| tenant_id | uuid FK | |
| patient_id | uuid FK → patients | nullable until match confirmed |
| uploader_user_id | uuid FK → users | |
| file_object_key | text | pointer into immutable object storage |
| file_hash | text | SHA-256 at intake |
| status | text | `intake_pending`, `intake_rejected`, `ocr_processing`, `ocr_complete`, `needs_review`, `ready`, `superseded` |
| report_status_extracted | text | `final` / `preliminary` / `amended` / `corrected` / `unknown` — as printed on the report, distinct from workflow `status` above |
| lab_name | text | |
| report_date | date | nullable |
| collection_date | date | nullable |
| match_status | text | `unmatched`, `needs_review`, `confirmed`, `conflict` |
| superseded_by_report_id | uuid FK → reports | nullable, self-referencing, for amendment chains |
| page_count | int | |
| created_at / updated_at | timestamptz | |

*Immutability:* `file_object_key` and `file_hash` are write-once.

### `results`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| tenant_id | uuid FK | |
| report_id | uuid FK → reports | |
| test_name_raw | text | |
| test_name_normalized | text | nullable, from terminology service (Phase 4) |
| value_raw | text | preserves `<5`, `Positive`, negative signs, exactly as printed |
| value_numeric | numeric | nullable — null when non-numeric (e.g., "Positive") |
| unit_raw | text | nullable |
| reference_range_raw | text | nullable |
| flag_raw | text | nullable — printed H/L/Critical/Abnormal as-is |
| is_critical | boolean | derived flag for fast alert-section queries |
| confidence_test_name | numeric(3,2) | |
| confidence_value | numeric(3,2) | |
| confidence_unit | numeric(3,2) | |
| confidence_reference_range | numeric(3,2) | |
| source_page | int | |
| source_x / source_y / source_width / source_height | numeric | bounding box |
| verification_status | text | `extracted_unverified`, `needs_review`, `verified_as_reported`, `corrected_by_reviewer`, `rejected`, `superseded_by_amended_report` |
| created_at / updated_at | timestamptz | |

### `result_corrections`
Append-only — one row per correction event, never updated.

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| result_id | uuid FK → results | |
| original_value_raw | text | value at time of correction |
| corrected_value_raw | text | |
| reviewer_user_id | uuid FK → users | |
| reason | text | required |
| evidence_source_page / x / y / width / height | — | may differ from original if reviewer re-locates the correct region |
| comment | text | nullable |
| created_at | timestamptz | |

### `review_items`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| tenant_id | uuid FK | |
| report_id | uuid FK → reports | |
| result_id | uuid FK → results | nullable (patient-match items reference the report, not a result) |
| item_type | text | `field_confidence`, `patient_match`, `multi_report_detected` |
| flag_reason | text | e.g., `decimal_uncertain`, `unit_missing`, `name_conflict` |
| status | text | `open`, `resolved` |
| assigned_user_id | uuid FK → users | nullable |
| resolved_at | timestamptz | nullable |
| created_at / updated_at | timestamptz | |

### `test_dictionary`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| tenant_id | uuid FK | nullable if platform-shared |
| canonical_name | text | |
| loinc_code | text | nullable, Phase 4 |
| synonyms | text[] | |

### `consultation_types`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| tenant_id | uuid FK | |
| name | text | e.g., "Diabetes follow-up" |
| current_version_id | uuid FK → consultation_type_versions | |
| created_at / updated_at | timestamptz | |

### `consultation_type_versions`
Append-only — new row per approved change, never updated.

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| consultation_type_id | uuid FK | |
| version_number | int | |
| selected_test_ids | uuid[] | FK-like array → test_dictionary |
| always_show | text[] | e.g., `critical_flags`, `amended_reports`, `unverified_results` |
| approved_by_user_id | uuid FK → users | |
| approved_at | timestamptz | |

### `consultation_views`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| tenant_id | uuid FK | |
| report_id | uuid FK → reports | |
| consultation_type_version_id | uuid FK → consultation_type_versions | pinned at generation time |
| generated_at | timestamptz | |

### `critical_alerts`
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| tenant_id | uuid FK | |
| result_id | uuid FK → results | |
| status | text | `open`, `acknowledged` |
| acknowledged_by_user_id | uuid FK → users | nullable |
| acknowledged_at | timestamptz | nullable |
| created_at | timestamptz | |

### `audit_events`
Append-only, restricted-role insert-only table; hash-chained (`prev_event_hash`) for tamper evidence.

| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| tenant_id | uuid FK | nullable for platform-level events |
| actor_user_id | uuid FK → users | nullable (system-initiated events) |
| event_type | text | upload / ocr_processed / patient_match_decision / report_opened / result_viewed / original_viewed / result_corrected / correction_approved / report_downloaded / report_shared / access_denied / critical_result_acknowledged / configuration_changed / permission_changed |
| resource_type | text | report / result / user / consultation_type / ... |
| resource_id | uuid | |
| metadata | jsonb | event-specific detail |
| prev_event_hash | text | for the hash chain |
| event_hash | text | |
| created_at | timestamptz | |

---

## 3. Key Relationships (summary)

```
tenants 1──* users
tenants 1──* patients
patients 1──* reports
reports 1──* results
results 1──* result_corrections
reports 1──* review_items
consultation_types 1──* consultation_type_versions
reports 1──* consultation_views (one active per rule application)
results 1──0/1 critical_alerts
all tenant tables ──* audit_events (via resource_id)
```

---

## 4. Row-Level Security Pattern (example)

```sql
ALTER TABLE results ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_results ON results
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

Every tenant-scoped table gets an equivalent policy. The application sets `app.current_tenant_id` from the authenticated session at the start of every request — never accepted as client input.

---

## 5. Indexing Notes

- `results(report_id)`, `results(verification_status)`, `results(is_critical) WHERE is_critical = true` (partial index for fast alert queries).
- `review_items(status, tenant_id)` for queue listing performance.
- `audit_events(tenant_id, created_at)` and `audit_events(resource_id)` for auditor queries.
- `patients(tenant_id, external_patient_id)` unique index (also the primary matching lookup path).
