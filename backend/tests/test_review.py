"""
Tests for the Review API (verify and correct endpoints).

Covers:
- Verify happy path: status transitions to 'verified_as_reported'
- Verify closes linked ReviewItem
- Correct happy path: ResultCorrection appended, original value NOT mutated
- Correct status transitions to 'verified_with_correction'
- Correct closes linked ReviewItem
- 404 on unknown result_id
"""

import asyncio
import pytest

from db.models.core_models import Report, Result, ResultCorrection, ReviewItem, generate_uuidv7
from services.ocr_service import OCRService, MockOCRProvider
from constants import SYNTH_TENANT_ID, SYNTH_UPLOADER_ID, SYNTH_REVIEWER_ID


REVIEWER_UUID = str(SYNTH_REVIEWER_ID)


def _setup_processed_report(db):
    """Upload → OCR → return (report, results, review_items)."""
    from tests.test_ocr_service import _create_test_report
    report = _create_test_report(db)
    service = OCRService(db_session=db, provider=MockOCRProvider())
    asyncio.run(service.process_report(report.id))
    db.refresh(report)

    results = db.query(Result).filter(Result.report_id == report.id).all()
    review_items = db.query(ReviewItem).filter(ReviewItem.report_id == report.id).all()
    return report, results, review_items


class TestVerifyResult:
    def test_verify_sets_status_verified_as_reported(self, client, db, reviewer_headers):
        report, results, _ = _setup_processed_report(db)
        # Pick any result
        result = results[0]

        resp = client.post(
            f"/api/v1/review/results/{result.id}/verify",
            json={"reviewer_user_id": REVIEWER_UUID},
            headers=reviewer_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["verification_status"] == "verified_as_reported"

    def test_verify_closes_linked_review_item(self, client, db, reviewer_headers):
        report, results, review_items = _setup_processed_report(db)

        # Find the result with a linked open ReviewItem (TSH)
        tsh_result = next(r for r in results if r.test_name_raw == "TSH")

        client.post(
            f"/api/v1/review/results/{tsh_result.id}/verify",
            json={"reviewer_user_id": REVIEWER_UUID},
            headers=reviewer_headers,
        )

        # The ReviewItem must now be resolved
        db.expire_all()
        linked_item = db.query(ReviewItem).filter(
            ReviewItem.result_id == tsh_result.id
        ).first()
        assert linked_item is not None
        assert linked_item.status == "resolved"
        assert linked_item.resolved_at is not None

    def test_verify_unknown_result_returns_404(self, client, db, reviewer_headers):
        import uuid
        fake_id = uuid.uuid4()
        resp = client.post(
            f"/api/v1/review/results/{fake_id}/verify",
            json={"reviewer_user_id": REVIEWER_UUID},
            headers=reviewer_headers,
        )
        assert resp.status_code == 404


class TestCorrectResult:
    def test_correct_creates_result_correction_row(self, client, db, reviewer_headers):
        report, results, _ = _setup_processed_report(db)
        tsh = next(r for r in results if r.test_name_raw == "TSH")

        client.post(
            f"/api/v1/review/results/{tsh.id}/correct",
            json={
                "reviewer_user_id": REVIEWER_UUID,
                "corrected_value_raw": "0.01",
                "reason": "OCR misread",
                "comment": "The < sign was missed",
            },
            headers=reviewer_headers,
        )

        corrections = db.query(ResultCorrection).filter(
            ResultCorrection.result_id == tsh.id
        ).all()
        assert len(corrections) == 1
        assert corrections[0].corrected_value_raw == "0.01"

    def test_correct_does_not_mutate_original_value(self, client, db, reviewer_headers):
        """Safety invariant: original value_raw must never change."""
        report, results, _ = _setup_processed_report(db)
        tsh = next(r for r in results if r.test_name_raw == "TSH")
        original_value = tsh.value_raw  # "<0.01"

        client.post(
            f"/api/v1/review/results/{tsh.id}/correct",
            json={
                "reviewer_user_id": REVIEWER_UUID,
                "corrected_value_raw": "0.01",
                "reason": "OCR misread",
            },
            headers=reviewer_headers,
        )

        db.expire_all()
        updated_result = db.query(Result).filter(Result.id == tsh.id).first()
        # Original value_raw MUST be unchanged
        assert updated_result.value_raw == original_value

    def test_correct_sets_status_verified_with_correction(self, client, db, reviewer_headers):
        report, results, _ = _setup_processed_report(db)
        tsh = next(r for r in results if r.test_name_raw == "TSH")

        resp = client.post(
            f"/api/v1/review/results/{tsh.id}/correct",
            json={
                "reviewer_user_id": REVIEWER_UUID,
                "corrected_value_raw": "0.01",
                "reason": "OCR misread",
            },
            headers=reviewer_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["verification_status"] == "verified_with_correction"

    def test_correct_closes_linked_review_item(self, client, db, reviewer_headers):
        report, results, _ = _setup_processed_report(db)
        tsh = next(r for r in results if r.test_name_raw == "TSH")

        client.post(
            f"/api/v1/review/results/{tsh.id}/correct",
            json={
                "reviewer_user_id": REVIEWER_UUID,
                "corrected_value_raw": "0.01",
                "reason": "OCR misread",
            },
            headers=reviewer_headers,
        )

        db.expire_all()
        linked_item = db.query(ReviewItem).filter(
            ReviewItem.result_id == tsh.id
        ).first()
        assert linked_item.status == "resolved"
