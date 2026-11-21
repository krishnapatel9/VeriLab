import os

STORAGE_DIR = os.path.join("mock_storage", "00000000-0000-4000-8000-000000000001")

VALID_PDF_BYTES = b"""%PDF-1.4
1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj
2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj
3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources <</Font <</F1 5 0 R>>>>>> endobj
4 0 obj <</Length 120>> stream
BT
/F1 22 Tf
50 720 Td
(VeriLab Clinical Report Demo) Tj
/F1 12 Tf
0 -30 Td
(Patient: Jane Doe  |  MRN-12345) Tj
0 -25 Td
(Hemoglobin: 12.5 g/dL  (Ref: 12.0 - 15.5)) Tj
0 -25 Td
(TSH: <0.01 uIU/mL  (Ref: 0.4 - 4.0) [LOW]) Tj
ET
endstream
endobj
5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj
xref
0 6
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000230 00000 n 
0000000401 00000 n 
trailer <</Size 6 /Root 1 0 R>>
startxref
472
%%EOF"""

if os.path.exists(STORAGE_DIR):
    for f in os.listdir(STORAGE_DIR):
        if f.endswith(".pdf"):
            path = os.path.join(STORAGE_DIR, f)
            with open(path, "wb") as pdf_file:
                pdf_file.write(VALID_PDF_BYTES)
            print(f"Updated {f} with valid renderable PDF content.")
