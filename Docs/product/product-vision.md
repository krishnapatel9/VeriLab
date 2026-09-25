# Product Vision: OCR Lab-Report Consultation System

## The Core Promise
The OCR Lab-Report Consultation System is an **information-management and retrieval system**, not a diagnostic or clinical recommendation engine.

Its fundamental purpose is to accelerate and organize a clinician's workflow by extracting reported facts from uploaded laboratory reports (PDFs, scans, photos) and presenting them alongside a traceable consultation view.

## The Guiding Principle
**"Organize reported facts; never invent, silently modify, discard, or clinically interpret them."**

## Core Objectives
1. **Accelerate Data Entry:** Reduce the manual burden of transcribing lab values into structured formats.
2. **Preserve Truth:** The original uploaded document always remains the undisputed source of truth.
3. **Traceability:** Every structured data point presented to a clinician must be traceable back to exact coordinates (bounding boxes) on the original document.
4. **Safety over Speed:** The system must proactively route ambiguous or low-confidence extractions (e.g., uncertain decimals, overlapping columns, conflicting patient IDs) to human reviewers rather than guessing.
