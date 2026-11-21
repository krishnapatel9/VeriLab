```mermaid
flowchart TD
    subgraph Frontend [React / TypeScript SPA]
        UploadUI[Upload & Intake UI]
        ReviewUI[Clinical Review UI]
        ConsultUI[Consultation Dashboard]
    end

    subgraph API [FastAPI Gateway]
        AuthMid[Auth & RBAC Middleware]
        IntakeRouter[Intake Router]
        OCRRouter[OCR Webhook Router]
        ReviewRouter[Review & Rules Router]
        ConsultRouter[Consultation Router]
    end

    subgraph Services [Domain Logic]
        IntakeSvc[Intake Service]
        OCRSvc[OCR Abstraction Layer]
        PatientSvc[Patient Match Engine]
        RulesSvc[Rules & Config Engine]
    end

    subgraph Infrastructure [Data & Storage]
        DB[(PostgreSQL 16\nRow-Level Security)]
        Storage[(Immutable Object\nStorage)]
    end

    subgraph External [External Integrations]
        OCRVendor[Managed OCR Provider\n(India Region)]
    end

    %% Flow Definitions
    UploadUI -->|Upload Report| IntakeRouter
    IntakeRouter --> AuthMid
    AuthMid --> IntakeSvc
    IntakeSvc -->|Save File| Storage
    IntakeSvc -->|Create Record| DB

    IntakeSvc -->|Trigger processing| OCRSvc
    OCRSvc -->|Send file| OCRVendor
    OCRVendor -->|Webhook/Response| OCRRouter
    OCRRouter --> OCRSvc
    OCRSvc -->|Extract & Map| DB

    OCRSvc -->|Trigger| PatientSvc
    PatientSvc -->|Match| DB
    PatientSvc -->|Flag Anomaly| DB

    ReviewUI --> ReviewRouter
    ReviewRouter --> AuthMid
    AuthMid --> RulesSvc
    RulesSvc -->|Update state / Add correction| DB

    ConsultUI --> ConsultRouter
    ConsultRouter --> AuthMid
    AuthMid --> RulesSvc
    RulesSvc -->|Fetch approved tests| DB
    ConsultUI -->|Verify source| Storage
```
