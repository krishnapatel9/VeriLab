"""
Tests for OCRService — the extraction and ReviewItem creation logic.

Covers:
- MockOCRProvider produces the expected two results (Hemoglobin, TSH)
- High-confidence results → verification_status = 'unverified'
- Low-confidence results → verification_status = 'needs_review'
- A ReviewItem row is created for every needs_review result
- No ReviewItem is created for high-confidence results
- Report status transitions: intake_pending → processing → processed
"""

import asyncio
import uuid
import pytest

from db.models.core_models import Report, Result, ReviewItem, generate_uuidv7
from services.ocr_service import OCRService, MockOCRProvider
from constants import SYNTH_TENANT_ID, SYNTH_UPLOADER_ID, PHASE1_VALUE_CONFIDENCE_REVIEW_BELOW


def _create_test_report(db) -> Report:
    """Helper: insert a minimal Report row for OCR testing."""
    report = Report(
        id=generate_uuidv7(),
        tenant_id=SYNTH_TENANT_ID,
        uploader_user_id=SYNTH_UPLOADER_ID,
        file_object_key=f"{SYNTH_TENANT_ID}/testhash_test.pdf",
        file_hash="testhash",
        status="intake_pending",
        report_status_extracted="unknown",
        match_status="unmatched",
        page_count=1,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


class TestOCRService:
    def test_process_report_creates_two_results(self, db):
        report = _create_test_report(db)
        service = OCRService(db_session=db, provider=MockOCRProvider())
        asyncio.run(service.process_report(report.id))

        results = db.query(Result).filter(Result.report_id == report.id).all()
        assert len(results) == 2

    def test_hemoglobin_is_high_confidence_unverified(self, db):
        report = _create_test_report(db)
        service = OCRService(db_session=db, provider=MockOCRProvider())
        asyncio.run(service.process_report(report.id))

        hgb = (
            db.query(Result)
            .filter(Result.report_id == report.id, Result.test_name_raw == "Hemoglobin")
            .first()
        )
        assert hgb is not None
        assert float(hgb.confidence_value) >= PHASE1_VALUE_CONFIDENCE_REVIEW_BELOW
        assert hgb.verification_status == "unverified"

    def test_tsh_is_low_confidence_needs_review(self, db):
        report = _create_test_report(db)
        service = OCRService(db_session=db, provider=MockOCRProvider())
        asyncio.run(service.process_report(report.id))

        tsh = (
            db.query(Result)
            .filter(Result.report_id == report.id, Result.test_name_raw == "TSH")
            .first()
        )
        assert tsh is not None
        assert float(tsh.confidence_value) < PHASE1_VALUE_CONFIDENCE_REVIEW_BELOW
        assert tsh.verification_status == "needs_review"

    def test_review_item_created_only_for_low_confidence(self, db):
        report = _create_test_report(db)
        service = OCRService(db_session=db, provider=MockOCRProvider())
        asyncio.run(service.process_report(report.id))

        review_items = (
            db.query(ReviewItem)
            .filter(ReviewItem.report_id == report.id)
            .all()
        )
        # Only TSH (confidence 0.85) should produce a ReviewItem
        assert len(review_items) == 1
        assert review_items[0].item_type == "field_confidence"
        assert review_items[0].status == "open"

    def test_report_status_becomes_processed(self, db):
        report = _create_test_report(db)
        service = OCRService(db_session=db, provider=MockOCRProvider())
        asyncio.run(service.process_report(report.id))

        db.refresh(report)
        assert report.status == "processed"

    def test_bounding_boxes_stored_on_result(self, db):
        report = _create_test_report(db)
        service = OCRService(db_session=db, provider=MockOCRProvider())
        asyncio.run(service.process_report(report.id))

        hgb = (
            db.query(Result)
            .filter(Result.report_id == report.id, Result.test_name_raw == "Hemoglobin")
            .first()
        )
        assert hgb.source_page == 1
        assert float(hgb.source_x) == 100
        assert float(hgb.source_y) == 200
        assert float(hgb.source_width) == 300   # x2 - x1 = 400 - 100
        assert float(hgb.source_height) == 20   # y2 - y1 = 220 - 200

    def test_mock_ocr_prohibited_in_production(self, db):
        from constants import settings
        orig_env = settings.environment
        try:
            settings.environment = "production"
            with pytest.raises(RuntimeError, match="prohibited"):
                OCRService(db_session=db, provider=MockOCRProvider())
        finally:
            settings.environment = orig_env

    def test_ocr_failure_sets_report_error_status(self, db):
        class FailingOCRProvider(MockOCRProvider):
            async def extract_data(self, file_path: str):
                raise RuntimeError("OCR processing binary crashed")

        report = _create_test_report(db)
        service = OCRService(db_session=db, provider=FailingOCRProvider())
        asyncio.run(service.process_report(report.id))

        db.refresh(report)
        assert report.status == "error"

    def test_bounded_inequality_numeric_parsing(self):
        from services.ocr_service import parse_numeric_value
        assert parse_numeric_value("<0.01") is None
        assert parse_numeric_value(">100") is None
        assert parse_numeric_value("12.5") == 12.5
        assert parse_numeric_value("0.4") == 0.4

    def test_per_field_confidence_threshold_routing(self, db):
        class FieldConfidenceProvider(MockOCRProvider):
            async def extract_data(self, file_path: str):
                return {
                    "results": [
                        {
                            "test_name": "Glucose",
                            "value": "95",
                            "unit": "mg/dL",
                            "reference_range": "70 - 99",
                            "confidence": 0.96,  # Overall high, but value confidence is 0.92 (< 0.95 threshold)
                            "confidence_value": 0.92,
                            "confidence_test_name": 0.98,
                            "confidence_unit": 0.95,
                            "confidence_reference_range": 0.90,
                            "bounding_box": {"x1": 10, "y1": 10, "x2": 50, "y2": 30},
                        }
                    ]
                }

        report = _create_test_report(db)
        service = OCRService(db_session=db, provider=FieldConfidenceProvider())
        asyncio.run(service.process_report(report.id))

        res = db.query(Result).filter(Result.report_id == report.id).first()
        assert res is not None
        assert res.verification_status == "needs_review"
        assert res.value_numeric == 95.0

        rev_item = db.query(ReviewItem).filter(ReviewItem.result_id == res.id).first()
        assert rev_item is not None
        assert "Value confidence 92% is below threshold 95%" in rev_item.flag_reason


