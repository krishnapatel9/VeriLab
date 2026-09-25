"""
Tests for the Intake API (upload endpoint).

Covers:
- Happy path: valid PDF → Report row created with correct hash and status
- File type validation: non-allowed extensions rejected with 400
- OCR background task is queued (we verify the initial status, not OCR output)
"""

import io
import hashlib
import pytest

from db.models.core_models import Report, AuditEvent
from constants import SYNTH_TENANT_ID, SYNTH_UPLOADER_ID


UPLOAD_URL = "/api/v1/intake/upload"


def _make_pdf_file(content: bytes = b"%PDF-1.4 fake-pdf-content") -> dict:
    return {"file": ("test_report.pdf", io.BytesIO(content), "application/pdf")}


class TestUploadHappyPath:
    def test_upload_returns_200_with_report_id(self, client):
        resp = client.post(UPLOAD_URL, files=_make_pdf_file())
        assert resp.status_code == 200
        data = resp.json()
        assert "report_id" in data
        assert "file_hash" in data
        assert data["status"] == "intake_pending"

    def test_file_hash_is_sha256_of_content(self, client, db):
        content = b"%PDF-1.4 unique-content-abc"
        expected_hash = hashlib.sha256(content).hexdigest()

        resp = client.post(UPLOAD_URL, files=_make_pdf_file(content))
        assert resp.status_code == 200
        assert resp.json()["file_hash"] == expected_hash

    def test_report_row_created_in_db(self, client, db):
        resp = client.post(UPLOAD_URL, files=_make_pdf_file())
        assert resp.status_code == 200
        report_id_str = resp.json()["report_id"]

        import uuid as _uuid
        report = db.query(Report).filter(
            Report.id == _uuid.UUID(report_id_str)
        ).first()
        assert report is not None
        assert str(report.tenant_id) == str(SYNTH_TENANT_ID)
        assert str(report.uploader_user_id) == str(SYNTH_UPLOADER_ID)

    def test_upload_emits_audit_event(self, client, db):
        resp = client.post(UPLOAD_URL, files=_make_pdf_file())
        assert resp.status_code == 200

        events = db.query(AuditEvent).filter(
            AuditEvent.event_type == "report.uploaded"
        ).all()
        assert len(events) >= 1
        assert events[0].metadata_json["file_hash"] is not None


class TestUploadValidation:
    def test_txt_file_rejected(self, client):
        resp = client.post(
            UPLOAD_URL,
            files={"file": ("report.txt", io.BytesIO(b"not a pdf"), "text/plain")},
        )
        assert resp.status_code == 400
        assert "Invalid file type" in resp.json()["detail"]

    def test_exe_file_rejected(self, client):
        resp = client.post(
            UPLOAD_URL,
            files={"file": ("malware.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
        )
        assert resp.status_code == 400

    def test_png_file_accepted(self, client):
        resp = client.post(
            UPLOAD_URL,
            files={"file": ("scan.png", io.BytesIO(b"\x89PNG\r\n"), "image/png")},
        )
        assert resp.status_code == 200
