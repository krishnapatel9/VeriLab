# Technical Requirements Document (TRD)
## OCR Lab-Report Consultation System

**Version:** 0.1 (draft) · **Date:** 25 September 2026

---

## 1. Architecture Overview

```
                         ┌─────────────────────────┐
                         │   Web app (React/TS)    │
                         └────────────┬─────────────┘
                                      │ HTTPS/REST (OpenAPI)
                         ┌────────────▼─────────────┐
                         │  API Gateway + Identity   │  (OIDC, MFA, rate limiting)
                         └────────────┬─────────────┘
                                      │
        ┌─────────────┬──────────────┼──────────────┬─────────────┐
        ▼             ▼              ▼              ▼             ▼
   Intake Svc   Patient-Match   Rules Engine   Consultation   Audit Svc
   (FastAPI)      Svc            Svc           API Svc       (FastAPI)
        │             ▲              ▲              ▲
        ▼             │              │              │
  Object Storage  Extraction DB  Config DB      Read replica
  (S3, immutable) (Postgres,     (Postgres)     (Postgres)
                   RLS per tenant)
        │
        ▼
  OCR Worker Pool (async, queue-driven)
        │
        ▼
  Managed OCR Provider (India region)
```

**Processing is asynchronous from upload onward.** The API layer never blocks on OCR; clients poll or subscribe (WebSocket/SSE) for status.

---

## 2. Services & Responsibilities

| Service | Responsibility | Tech |
|---|---|---|
| **API Gateway / Identity** | AuthN (OIDC + MFA), authorization enforcement, rate limiting, routing | Kong/Traefik or managed API Gateway + Keycloak |
| **Intake Service** | Upload handling, hashing, validation, malware scan trigger, dedup detection | FastAPI |
| **OCR Worker Pool** | Calls managed OCR provider, normalizes raw output into the structured result schema (Section 5 / Backend Schema doc) | Python workers, queue-consumer |
| **Extraction/Validation Service** | Applies field-level confidence rules, normalization (raw vs. normalized), format checks | FastAPI |
| **Patient Matching Service** | Deterministic matching logic + escalation to review queue | FastAPI |
| **Review Service** | Review queue, correction workflow, versioning of corrections | FastAPI |
| **Rules Service** | Consultation-type configs, versioning, approval workflow | FastAPI |
| **Consultation API** | Assembles the doctor-facing view: applies rules + RBAC scoping; never a raw DB passthrough | FastAPI |
| **Audit Service** | Append-only event ingestion, tamper-evidence (hash-chained records), query API for auditors | FastAPI + dedicated append-only table/partition |
| **Notification Service** | Review-queue assignment alerts, critical-result alerts | FastAPI + email/SMS/push provider |
| **Monitoring/Observability** | OCR quality metrics, latency, failure rates, security events | OpenTelemetry → Prometheus/Grafana + centralized logs |

All services are independently deployable but share the Postgres cluster (logically separated schemas per the Backend Schema doc) for v1 — full service-owned databases are a Phase 4 consideration once tenant volume justifies the operational cost.

---

## 3. Tech Stack (confirmed)

| Layer | Choice | Notes |
|---|---|---|
| Backend framework | Python 3.12 + FastAPI | Async-native, OpenAPI-first, strong OCR/data-science ecosystem |
| Frontend | React 18 + TypeScript + Tailwind CSS | react-pdf or pdf.js for original-document viewer + canvas overlay for bounding boxes |
| Database | PostgreSQL 16 | Row-Level Security for tenant/patient isolation; JSONB for flexible OCR-confidence payloads |
| Object storage | S3-compatible, India region, versioning + Object Lock (immutability) enabled | Original documents never overwritten |
| Queue | Amazon SQS or RabbitMQ | Async OCR pipeline, retry with dead-letter queue |
| OCR provider | Managed OCR vendor with India-region processing and bounding-box + confidence output (vendor selection is an open PRD question — evaluate against Section 10 criteria below) | Must support BAA-equivalent / DPDPA-compatible data-processing terms |
| Identity | Keycloak (self-hosted, for full tenant/data control) or Auth0 (if managed preferred) | OIDC, MFA mandatory |
| API contract | OpenAPI 3.1, generated from FastAPI | Also the basis for a future FHIR-adjacent API |
| Observability | OpenTelemetry, Prometheus, Grafana, centralized log store (e.g., Loki or managed SIEM) | |
| CI/CD | GitHub Actions (or GitLab CI) → containerized deploy | |
| Container/orchestration | Docker + Kubernetes (or managed equivalent, e.g., AWS ECS if team is smaller) | K8s recommended given multi-tenant scaling needs |
| Infra-as-code | Terraform | |

---

## 4. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | Median upload-to-doctor-ready < 5 min for digital PDFs (per PRD goal); Consultation View API p95 < 500ms |
| **Scalability** | Support N tenants with per-tenant data isolation; horizontal scaling of OCR workers independent of API tier |
| **Availability** | 99.5% for v1 (clinical-adjacent but not life-critical real-time system); scheduled maintenance windows communicated per tenant |
| **Durability** | Original documents: 11 nines (S3 standard durability) with versioning; no hard-delete path for originals within retention period |
| **Security** | TLS 1.2+ everywhere; encryption at rest (AES-256); secrets in a dedicated secrets manager (never in code/config repos); dependency and container scanning in CI |
| **Data residency** | All patient data storage and processing within India region by default per tenant |
| **Auditability** | Every FR-37 event captured within 1 second of occurrence; audit store append-only, hash-chained per record for tamper evidence |
| **Tenant isolation** | Verified via automated tests that one tenant's API credentials cannot retrieve another tenant's data, run in CI on every schema/API change |
| **Backup/DR** | Daily automated Postgres backups, point-in-time recovery; documented RTO/RPO (targets: RTO 4h, RPO 1h for pilot; tightened post-pilot) |

---

## 5. Data Flow Detail (Upload → Consultation View)

1. Client uploads file → Intake Service computes hash, stores original in Object Storage (immutable), writes a `reports` row (`status = intake_pending`), enqueues an OCR job.
2. OCR Worker picks up job → calls OCR provider → receives raw text + layout + confidence → Extraction Service normalizes into `results` rows (raw + normalized + confidence + source coordinates), sets `reports.status = ocr_complete`.
3. Patient Matching Service runs against `results` patient-identifying fields + any provided metadata → either confirms match (`reports.patient_id` set, `match_status = confirmed`) or creates a `review_items` entry (`match_status = needs_review`).
4. Confidence rules evaluate every `results` row → any field below its type-specific threshold creates a `review_items` entry (`verification_status = needs_review`); others default to `extracted_unverified` pending optional spot-review policy, or `verified_as_reported` if tenant policy allows confidence-based auto-verification for high-confidence fields.
5. Once all blocking `review_items` for a report are resolved (or none existed), Rules Service is invoked with the report's consultation type → filters `results` into the summary set, stamps the active `rules_config` version onto a new `consultation_views` row.
6. Consultation API serves the `consultation_views` row + linked `results` + header data to the authorized doctor, applying RBAC scoping at query time (never returning unauthorized patient data even if requested).
7. Every read/write in steps 1–6 emits an event to the Audit Service.

---

## 6. Integration Points (Phase 4, designed for but not built in v1)

- **HL7 FHIR:** `Patient`, `DiagnosticReport`, `Observation`, `DocumentReference`, `Provenance`, `Practitioner`/`PractitionerRole`, `Encounter` — the internal schema (see Backend Schema doc) is already shaped to map cleanly onto these resources.
- **SMART App Launch:** OAuth-based launch from an EHR, passing the active patient context — API design keeps patient-context resolution as a discrete step for this reason.
- **Terminology services:** LOINC (tests), UCUM (units), SNOMED CT (where clinically appropriate) — normalization layer (`test_name_normalized`, `unit_raw` → `unit_ucum`) is structured to slot these in without a schema change.

---

## 7. OCR Vendor Evaluation Criteria (for the open PRD question)

Do not select solely on recognition accuracy. Score candidates against:
- India data residency and whether patient data is used for vendor model training (must be contractually excluded).
- Retention period and deletion guarantees.
- Availability of a data-processing agreement compatible with DPDPA fiduciary/processor obligations.
- Native bounding-box and per-field confidence output (required — avoids building this ourselves).
- Table and handwriting performance on the Phase 0 sample corpus.
- Versioning/reproducibility of OCR model updates (a silent vendor model update must not silently change extraction behavior in production without a way to detect it).
- Outage/fallback behavior.

---

## 8. Environments

| Environment | Purpose | Data |
|---|---|---|
| `dev` | Active development | Synthetic data only |
| `staging` | Pre-release validation, pilot-tenant UAT | De-identified data only |
| `production` | Live tenants | Real patient data, full compliance controls active |

No real patient data enters `dev` or `staging` under any circumstance — enforced by environment-level access controls, not just policy.
