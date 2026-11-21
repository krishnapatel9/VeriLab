# Requirements Traceability Matrix

This matrix maps MVP Functional Requirements (FR-1 through FR-38) to their implementation targets across the stack.

| ID | Module | Requirement Summary | DB Table | Backend Service | API Endpoint | Frontend Component | Test Target |
|----|--------|---------------------|----------|-----------------|--------------|--------------------|-------------|
| **FR-1** | Upload | Upload PDF, image, or photo files | `reports` | `IntakeService` | `POST /upload` | `UploadDropzone` | Intake E2E |
| **FR-2** | Upload | Immutable file storage & SHA-256 hash | `reports` | `IntakeService` | `POST /upload` | N/A | Intake Unit |
| **FR-3** | Upload | File-size & page-count validation | N/A | `IntakeService` | `POST /upload` | `UploadDropzone` | API Unit |
| **FR-4** | Upload | Malware & corruption detection | `reports` | `IntakeService` | `POST /upload` | `UploadStatus` | Intake Unit |
| **FR-5** | Upload | Combined-report (multi-patient) detection | `review_items` | `OCRService` | N/A | `ReviewQueue` | OCR Integration |
| **FR-6** | Upload | Capture uploader ID & timestamps | `reports` | `IntakeService` | `POST /upload` | `ReportHistory` | DB Integration |
| **FR-7** | OCR | Extract patient, lab, and dates | `reports`, `patients` | `OCRService` | Webhook | `ReportHeader` | OCR E2E |
| **FR-8** | OCR | Extract tests, values, units, ranges, flags | `results` | `OCRService` | Webhook | `ResultTable` | OCR E2E |
| **FR-9** | OCR | Retain authoritative raw printed text | `results` | `OCRService` | Webhook | `ResultTable` | OCR Unit |
| **FR-10** | OCR | Generate field-level confidence & bounding box | `results` | `OCRService` | Webhook | `SourceVerification` | OCR Unit |
| **FR-11** | Match | Identify exact Patient ID matches | `patients` | `PatientMatchService` | `POST /match` | N/A | Match Unit |
| **FR-12** | Match | Prevent auto-match on name similarity alone | `review_items` | `PatientMatchService` | N/A | `MatchReview` | Match Unit |
| **FR-13** | Match | Flag conflicting identifiers for review | `review_items` | `PatientMatchService` | N/A | `MatchReview` | Match Unit |
| **FR-14** | Match | Flag missing identifiers for review | `review_items` | `PatientMatchService` | N/A | `MatchReview` | Match Unit |
| **FR-15** | Match | Allow manual match override by reviewer | `patients`, `reports` | `ReviewService` | `POST /match/confirm`| `MatchReview` | Review E2E |
| **FR-16** | Match | Tenant-scoped matching boundaries | `patients` | `PatientMatchService` | N/A | N/A | RLS DB Test |
| **FR-17** | Review | Field-specific confidence routing | `review_items` | `RulesService` | N/A | `ReviewQueue` | Rules Unit |
| **FR-18** | Review | Route ambiguity (decimals, units) to review | `review_items` | `RulesService` | N/A | `ReviewQueue` | Rules Unit |
| **FR-19** | Review | Additive correction versioning (never overwrite) | `result_corrections` | `ReviewService` | `POST /correct` | `CorrectionForm` | DB Integration |
| **FR-20** | Review | Full state machine (needs_review -> verified) | `results` | `ReviewService` | `POST /verify` | `ReviewStatus` | Review E2E |
| **FR-21** | Rules | Config-driven consultation test lists | `consultation_types` | `RulesService` | `GET /rules` | `TestSelector` | Rules Unit |
| **FR-22** | Rules | Strict versioning of consultation rules | `consultation_type_versions` | `RulesService` | `POST /rules` | `RuleEditor` | DB Integration |
| **FR-23** | Rules | Clinical admin approval workflow for rules | `consultation_type_versions` | `RulesService` | `POST /rules/approve`| `ApprovalQueue` | RBAC Unit |
| **FR-24** | Rules | Unmatched tests must remain stored | `results` | `RulesService` | `GET /consultation`| `AdditionalResults`| API Unit |
| **FR-25** | Consult | Display patient, lab, report metadata | `reports` | `ConsultationService` | `GET /consultation`| `PatientHeader` | Consult E2E |
| **FR-26** | Consult | Display selected test results & verification status | `results` | `ConsultationService` | `GET /consultation`| `ResultTable` | Consult E2E |
| **FR-27** | Consult | Clearly separate selected vs. additional results | `results` | `ConsultationService` | `GET /consultation`| `AdditionalResults`| Consult E2E |
| **FR-28** | Consult | Uncertainty indicated by text/icons (not just color) | `results` | N/A | `GET /consultation`| `UncertaintyBadge` | UI Visual Test |
| **FR-29** | Consult | Original document always accessible | `reports` | `IntakeService` | `GET /file` | `PDFViewer` | Consult E2E |
| **FR-30** | Consult | Source verification (click to bounding box) | `results` | N/A | `GET /consultation`| `PDFHighlight` | Consult E2E |
| **FR-31** | Critical| Detect critical/abnormal flags | `results` | `OCRService` | Webhook | N/A | OCR Unit |
| **FR-32** | Critical| Surface criticals even if test is filtered out | `critical_alerts` | `ConsultationService` | `GET /consultation`| `CriticalAlerts` | Consult E2E |
| **FR-33** | Critical| Acknowledgment workflow per tenant policy | `critical_alerts` | `ReviewService` | `POST /ack` | `AlertAckButton` | API Unit |
| **FR-34** | Access | Implement 6 distinct RBAC personas | `users` | `SecurityService` | Middleware | `RoleGuard` | RBAC Unit |
| **FR-35** | Access | Verifiable Row-Level Security (Tenant Isolation) | All DB Tables | N/A | N/A | N/A | DB Integration |
| **FR-36** | Access | Enforce MFA for clinical/admin roles | `users` | `SecurityService` | Middleware | `MFAPrompt` | RBAC Unit |
| **FR-37** | Audit | Record all system actions (view, correct, approve)| `audit_events` | `AuditService` | Middleware | N/A | Audit E2E |
| **FR-38** | Audit | Append-only, tamper-evident audit logs | `audit_events` | `AuditService` | N/A | `AuditViewer` | DB Integration |
