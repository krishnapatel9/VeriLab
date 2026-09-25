# VeriLab

VeriLab is a safety-critical laboratory report intake and review system. It automates the extraction of patient data from uploaded lab reports (PDFs/Images) using OCR, maps the extracted data to patient records, and safely surfaces critical anomalies (like a dangerously low TSH or high Glucose) to the reviewing doctors.

The platform is designed with strict Role-Based Access Control (RBAC) to ensure that only authorized personnel can upload, verify, or clinically consult on sensitive medical data.

## 🚀 Features

*   **Automated OCR Extraction:** Uses Tesseract OCR to automatically read and parse lab reports into structured data.
*   **Critical Result Detection:** Automatically flags abnormal results (e.g., High/Low) and routes them for immediate attention.
*   **Role-Based Access Control (RBAC):** 
    *   **Uploaders:** Can upload new lab reports.
    *   **Reviewers:** Can verify OCR accuracy and correct misread values before a doctor sees them.
    *   **Doctors:** Can view verified reports and conduct clinical consultations based on the extracted data.
*   **Full Audit Trail:** (In Progress) Every action is logged in an append-only, tamper-evident audit log.

## 🛠 Tech Stack

*   **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, React Router, Axios.
*   **Backend:** Python, FastAPI, SQLAlchemy, Pydantic, PyTesseract.
*   **Database:** SQLite (Development) / PostgreSQL (Staging/Production).

## 💻 Getting Started (Local Development)

### 1. Backend Setup

Open a terminal in the `backend` folder:

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Start the server (FastAPI will run on http://127.0.0.1:8000)
uvicorn main:app --reload
```
*Note: The backend seed script automatically creates a development database (`verilab_dev.db`) on the first run.*

### 2. Frontend Setup

Open a new terminal in the `frontend` folder:

```bash
cd frontend

# Install dependencies
npm install

# Start the development server (Vite will run on http://localhost:5173)
npm run dev
```

### 3. Usage & Test Credentials

Navigate to `http://localhost:5173` in your browser. The database is pre-seeded with synthetic test users. You can log in with any of the following accounts (Password for all: `dev123`):

*   **Uploader:** `uploader@synth.verilab` (Uploads new PDFs)
*   **Reviewer:** `reviewer@synth.verilab` (Verifies OCR results)
*   **Doctor:** `doctor@synth.verilab` (Views the final consultation)

## ⚠️ Important Note Regarding Git
If you clone this repository, you may notice `node_modules/` and `venv/` are checked into source control. It is highly recommended to add a `.gitignore` file to ignore these massive dependency directories in the future.
