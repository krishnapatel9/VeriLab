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
from tests.sample_files import make_pdf, make_png


UPLOAD_URL = "/api/v1/intake/upload"


def _make_pdf_file(content: bytes | None = None) -> dict:
    return {"file": ("test_report.pdf", io.BytesIO(content or make_pdf()), "application/pdf")}


class TestUploadHappyPath:
    def test_upload_returns_200_with_report_id(self, client, uploader_headers):
        resp = client.post(UPLOAD_URL, files=_make_pdf_file(), headers=uploader_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "report_id" in data
        assert "file_hash" in data
        assert data["status"] == "intake_pending"

    def test_file_hash_is_sha256_of_content(self, client, db, uploader_headers):
        content = make_pdf("unique-content-abc")
        expected_hash = hashlib.sha256(content).hexdigest()

        resp = client.post(UPLOAD_URL, files=_make_pdf_file(content), headers=uploader_headers)
        assert resp.status_code == 200
        assert resp.json()["file_hash"] == expected_hash

    def test_report_row_created_in_db(self, client, db, uploader_headers):
        resp = client.post(UPLOAD_URL, files=_make_pdf_file(), headers=uploader_headers)
        assert resp.status_code == 200
        report_id_str = resp.json()["report_id"]

        import uuid as _uuid
        report = db.query(Report).filter(
            Report.id == _uuid.UUID(report_id_str)
        ).first()
        assert report is not None
        assert str(report.tenant_id) == str(SYNTH_TENANT_ID)
        assert str(report.uploader_user_id) == str(SYNTH_UPLOADER_ID)

    def test_upload_emits_audit_event(self, client, db, uploader_headers):
        resp = client.post(UPLOAD_URL, files=_make_pdf_file(), headers=uploader_headers)
        assert resp.status_code == 200

        events = db.query(AuditEvent).filter(
            AuditEvent.event_type == "report.uploaded"
        ).all()
        assert len(events) >= 1
        assert events[0].metadata_json["file_hash"] is not None


class TestUploadValidation:
    def test_txt_file_rejected(self, client, uploader_headers):
        resp = client.post(
            UPLOAD_URL,
            files={"file": ("report.txt", io.BytesIO(b"not a pdf"), "text/plain")},
            headers=uploader_headers,
        )
        assert resp.status_code == 400
        assert "Invalid file type" in resp.json()["detail"]

    def test_exe_file_rejected(self, client, uploader_headers):
        resp = client.post(
            UPLOAD_URL,
            files={"file": ("malware.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
            headers=uploader_headers,
        )
        assert resp.status_code == 400

    def test_png_file_accepted(self, client, uploader_headers):
        resp = client.post(
            UPLOAD_URL,
            files={"file": ("scan.png", io.BytesIO(make_png()), "image/png")},
            headers=uploader_headers,
        )
        assert resp.status_code == 200

    def test_extension_spoofing_rejected(self, client, uploader_headers):
        resp = client.post(
            UPLOAD_URL,
            files={"file": ("report.pdf", io.BytesIO(b"MZ not a pdf"), "application/pdf")},
            headers=uploader_headers,
        )
        assert resp.status_code == 400

    def test_zero_byte_file_rejected(self, client, uploader_headers):
        resp = client.post(
            UPLOAD_URL,
            files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
            headers=uploader_headers,
        )
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    def test_encrypted_pdf_rejected(self, client, uploader_headers):
        resp = client.post(
            UPLOAD_URL,
            files={"file": ("encrypted.pdf", io.BytesIO(b"%PDF-1.4 /Encrypt 12 0 R ..."), "application/pdf")},
            headers=uploader_headers,
        )
        assert resp.status_code == 400
        assert "encrypted" in resp.json()["detail"].lower()



class TestUnreadableFilesRefused:
    """A file that can never be read is refused at upload, with a reason,
    instead of being accepted and failing during OCR."""

    def test_placeholder_pdf_rejected(self, client, uploader_headers):
        fake = b"%PDF-1.4\n%Dummy PDF content for testing upload endpoint\n%%EOF"
        resp = client.post(UPLOAD_URL, files=_make_pdf_file(fake), headers=uploader_headers)
        assert resp.status_code == 400
        assert "can't be opened" in resp.json()["detail"]

    def test_header_only_png_rejected(self, client, uploader_headers):
        resp = client.post(
            UPLOAD_URL,
            files={"file": ("scan.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
            headers=uploader_headers,
        )
        assert resp.status_code == 400

    def test_tiny_image_rejected(self, client, uploader_headers):
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (20, 20), "white").save(buf, format="PNG")
        resp = client.post(UPLOAD_URL, files={"file": ("tiny.png", io.BytesIO(buf.getvalue()), "image/png")},
                           headers=uploader_headers)
        assert resp.status_code == 400
        assert "too small" in resp.json()["detail"]

    def test_too_many_pages_rejected(self, client, uploader_headers, monkeypatch):
        from constants import settings
        monkeypatch.setattr(settings, "max_pdf_pages", 0)
        resp = client.post(UPLOAD_URL, files=_make_pdf_file(), headers=uploader_headers)
        assert resp.status_code == 400
        assert "limit" in resp.json()["detail"]

    def test_real_page_count_is_stored(self, client, db, uploader_headers):
        resp = client.post(UPLOAD_URL, files=_make_pdf_file(), headers=uploader_headers)
        assert resp.status_code == 200
        import uuid
        report = db.get(Report, uuid.UUID(resp.json()["report_id"]))
        assert report.page_count == 1

    def test_sample_report_in_repo_is_a_real_pdf(self):
        import os
        from services.documents import inspect_document
        here = os.path.dirname(__file__)
        for path in ("../test_report.pdf", "../../Docs/demo-report.pdf"):
            with open(os.path.join(here, path), "rb") as f:
                assert inspect_document(f.read(), ".pdf") == 1


def test_failed_ocr_records_a_reason(db):
    """A report that fails OCR carries a plain-language reason for the list view."""
    import asyncio, uuid
    from db.models.core_models import generate_uuidv7
    from services.ocr_service import OCRService, OCRProvider

    class Broken(OCRProvider):
        async def extract_data(self, file_path):
            raise FileNotFoundError(file_path)

    report = Report(id=generate_uuidv7(), tenant_id=SYNTH_TENANT_ID, uploader_user_id=SYNTH_UPLOADER_ID,
                    file_object_key=f"{SYNTH_TENANT_ID}/{uuid.uuid4().hex}.pdf", file_hash=uuid.uuid4().hex * 2,
                    status="intake_pending", report_status_extracted="unknown", match_status="unmatched", page_count=1)
    db.add(report)
    db.commit()
    service = OCRService(db, Broken())
    asyncio.run(service.process_report(report.id))
    db.refresh(report)
    assert report.status == "error"
    assert "missing" in report.processing_error
    assert service.last_error.startswith("FileNotFoundError")


def test_report_list_includes_reason_and_pages(client, uploader_headers):
    resp = client.get("/api/v1/intake/reports", headers=uploader_headers)
    assert resp.status_code == 200
    for r in resp.json()["reports"]:
        assert "processing_error" in r and "page_count" in r
