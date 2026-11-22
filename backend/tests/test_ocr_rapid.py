"""RapidOCR provider: line grouping, row parsing, and real OCR on the demo report."""

import asyncio
import os
import uuid

import pytest

from constants import SYNTH_TENANT_ID, SYNTH_UPLOADER_ID, settings
from db.models.core_models import Report, Result, generate_uuidv7
from services import storage
from services.ocr_service import OCRService, RapidOCRProvider, _group_lines, parse_result_lines

DEMO_REPORT = os.path.join(os.path.dirname(__file__), "..", "..", "Docs", "demo-report.png")


def _box(x1, y1, x2, y2):
    return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]


# A table row as OCR returns it: one box per cell, slightly misaligned, out of order.
ROW_BOXES = [
    (_box(714, 372, 990, 411), "12.0 - 15.5 Normal", 0.97),
    (_box(55, 379, 213, 413), "Hemoglobin", 1.0),
    (_box(551, 375, 617, 417), "g/dL", 0.88),
    (_box(393, 375, 462, 408), "12.5", 0.99),
    (_box(53, 305, 117, 337), "TEST", 1.0),
    (_box(393, 305, 485, 336), "RESULT", 1.0),
    (_box(57, 1309, 531, 1334), "End of report - Page 1 of 1", 0.97),
]


def _lines():
    boxes, txts, scores = zip(*ROW_BOXES)
    return _group_lines(boxes, txts, scores)


def test_cells_of_one_row_join_left_to_right():
    texts = [line["text"] for line in _lines()]
    assert "Hemoglobin 12.5 g/dL 12.0 - 15.5 Normal" in texts
    assert "TEST RESULT" in texts


def test_row_is_parsed_with_per_field_confidence():
    results = parse_result_lines(_lines(), page_no=1)
    assert len(results) == 1  # header and footer lines are not results
    r = results[0]
    assert (r["test_name"], r["value"], r["unit"], r["reference_range"], r["flag"]) == (
        "Hemoglobin", "12.5", "g/dL", "12.0 - 15.5", "Normal")
    # Each field carries the score of the box it was read from, not a line average.
    assert r["confidence_value"] == 0.99
    assert r["confidence_unit"] == 0.88
    assert r["confidence_test_name"] == 1.0
    assert r["confidence"] == 0.88  # overall = weakest box on the line
    assert r["bounding_box"] == {"x1": 55, "y1": 372, "x2": 990, "y2": 417}


def test_bounded_value_is_kept_verbatim():
    boxes = [_box(0, 0, 50, 20), _box(100, 0, 150, 20), _box(200, 0, 260, 20), _box(300, 0, 380, 20)]
    lines = _group_lines(boxes, ["TSH", "<0.01", "uIU/mL", "0.4 - 4.0"], [1.0, 1.0, 1.0, 1.0])
    (r,) = parse_result_lines(lines, page_no=2)
    assert r["value"] == "<0.01" and r["page"] == 2


def test_unknown_provider_is_refused(db, monkeypatch):
    monkeypatch.setattr(settings, "ocr_provider", "nonsense")
    with pytest.raises(RuntimeError):
        OCRService(db)


def test_old_tesseract_setting_maps_to_rapidocr(db, monkeypatch):
    monkeypatch.setattr(settings, "ocr_provider", "tesseract")
    assert isinstance(OCRService(db).provider, RapidOCRProvider)


@pytest.mark.slow
def test_real_ocr_reads_the_demo_report(db, monkeypatch):
    """Runs the actual OCR models on Docs/demo-report.png through the full pipeline."""
    pytest.importorskip("rapidocr")
    monkeypatch.setattr(settings, "storage_backend", "db")
    storage.get_storage.cache_clear()
    try:
        data = open(DEMO_REPORT, "rb").read()
        key = f"{SYNTH_TENANT_ID}/{uuid.uuid4().hex}.png"
        storage.get_storage().put(key, data, db)
        report = Report(
            id=generate_uuidv7(), tenant_id=SYNTH_TENANT_ID, uploader_user_id=SYNTH_UPLOADER_ID,
            file_object_key=key, file_hash=uuid.uuid4().hex * 2, status="intake_pending",
            report_status_extracted="unknown", match_status="unmatched", page_count=1,
        )
        db.add(report)
        db.commit()

        # The provider reads through its own session, which must see the test database.
        monkeypatch.setattr(storage.DatabaseStorage, "get", lambda self, k, s=None: data if k == key else None)
        service = OCRService(db, RapidOCRProvider())
        asyncio.run(service.process_report(report.id))
        db.refresh(report)

        assert report.status == "processed", service.last_error
        rows = {r.test_name_raw: r for r in db.query(Result).filter(Result.report_id == report.id)}
        assert set(rows) == {"Hemoglobin", "TSH"}
        hgb, tsh = rows["Hemoglobin"], rows["TSH"]
        assert (hgb.value_raw, hgb.unit_raw, hgb.reference_range_raw, hgb.flag_raw) == ("12.5", "g/dL", "12.0 - 15.5", "Normal")
        assert float(hgb.value_numeric) == 12.5
        assert (tsh.value_raw, tsh.reference_range_raw, tsh.flag_raw) == ("<0.01", "0.4 - 4.0", "Low")
        assert tsh.value_numeric is None  # "<0.01" is never stored as 0.01
    finally:
        storage.get_storage.cache_clear()
