# Product Scope: Non-Goals

To maintain clinical safety and adhere to the strict scope of Phase 0/1 development, the following features and behaviors are **explicitly excluded** from the MVP (Version 1).

## ❌ Diagnostic AI
The system will not attempt to interpret lab results to suggest potential diseases or diagnoses.

## ❌ Treatment Recommendations
The system will not suggest medications, follow-up tests, or treatment plans based on extracted values.

## ❌ Autonomous Test-Selection Modeling
The list of tests displayed for a given consultation type must be driven by strict, clinically approved, versioned configurations. The system will not use AI to "guess" which tests are relevant.

## ❌ Free-Text Clinical Interpretation
The system will not attempt to summarize or rephrase clinical notes or interpretations printed on the report.

## ❌ FHIR / SMART Integration
Integration with external Electronic Health Record (EHR) systems via FHIR/SMART is deferred to Phase 4 (Integration & Scale).

## ❌ Broad Multilingual OCR
The MVP will focus on the default language capabilities provided by the chosen OCR vendor without building custom translation pipelines.

## ❌ Patient Portal
The system is exclusively clinician-facing. Patients will not have login access in this version.
