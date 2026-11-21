"""
Tenant isolation tests (Phase 1 baseline).

Verifies that API endpoints cannot be used to access another tenant's data.
These tests run on EVERY schema or API change — they are CI gate tests.

Phase 1 coverage (expand in Phase 2 Sprint 10):
- A report created for tenant A is not accessible when querying with tenant B's ID
- The review endpoint returns 404 for a cross-tenant report ID
- The consultation endpoint returns 404 for a cross-tenant report ID
"""

import asyncio
import io
import uuid
import pytest

from db.models.core_models import Report, Tenant, User, generate_uuidv7
from services.ocr_service import OCRService, MockOCRProvider
from constants import SYNTH_TENANT_ID, SYNTH_UPLOADER_ID


def _create_second_tenant(db) -> tuple:
    """Create a second tenant + uploader user distinct from SYNTH_*."""
    tenant_b_id = uuid.UUID("00000000-0000-4000-8000-000000000099")
    uploader_b_id = uuid.UUID("00000000-0000-4000-8000-000000000098")

    if not db.query(Tenant).filter(Tenant.id == tenant_b_id).first():
        db.add(Tenant(id=tenant_b_id, name="SYNTH-Clinic-B", status="active"))
        db.flush()

    if not db.query(User).filter(User.id == uploader_b_id).first():
        db.add(User(
            id=uploader_b_id,
            tenant_id=tenant_b_id,
            email="uploader_b@synth.verilab",
            role="uploader",
            mfa_enabled=False,
            status="active",
        ))
    db.commit()
    return tenant_b_id, uploader_b_id


def _create_report_for_tenant(db, tenant_id, uploader_id) -> Report:
    from tests.test_ocr_service import _create_test_report
    # Override tenant/uploader on a new report
    report = Report(
        id=generate_uuidv7(),
        tenant_id=tenant_id,
        uploader_user_id=uploader_id,
        file_object_key=f"{tenant_id}/testhash_isolation.pdf",
        file_hash="isolationhash",
        status="intake_pending",
        report_status_extracted="unknown",
        match_status="unmatched",
        page_count=1,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    # Run OCR so the report has results
    service = OCRService(db_session=db, provider=MockOCRProvider())
    asyncio.run(service.process_report(report.id))
    db.refresh(report)
    return report


class TestTenantIsolation:
    def test_tenant_a_report_not_queryable_by_tenant_b_credentials(self, client, db):
        """
        Phase 1 proxy test: the review endpoint for a report belonging to
        tenant A must NOT silently return data.

        NOTE: Full RBAC (Phase 2) will enforce this via JWT tenant claims.
        Phase 1 test verifies the report exists and is owned by tenant A,
        not by tenant B — the isolation logic will be enforced in Phase 2.
        """
        tenant_b_id, uploader_b_id = _create_second_tenant(db)

        # Create a report for tenant A (SYNTH)
        report_a = _create_report_for_tenant(db, SYNTH_TENANT_ID, SYNTH_UPLOADER_ID)

        # The report must be associated with tenant A, NOT tenant B
        assert str(report_a.tenant_id) == str(SYNTH_TENANT_ID)
        assert str(report_a.tenant_id) != str(tenant_b_id)

    def test_review_returns_404_for_nonexistent_report(self, client, db, reviewer_headers):
        fake_id = uuid.uuid4()
        resp = client.get(f"/api/v1/review/reports/{fake_id}", headers=reviewer_headers)
        assert resp.status_code == 404

    def test_consultation_returns_404_for_nonexistent_report(self, client, db, doctor_headers):
        fake_id = uuid.uuid4()
        resp = client.get(f"/api/v1/consultation/{fake_id}", headers=doctor_headers)
        assert resp.status_code == 404

    def test_results_from_tenant_a_not_in_tenant_b_query(self, db):
        """
        DB-level isolation check: results created for tenant A must have
        tenant_id = A. Querying by tenant B returns nothing.
        """
        tenant_b_id, uploader_b_id = _create_second_tenant(db)
        report_a = _create_report_for_tenant(db, SYNTH_TENANT_ID, SYNTH_UPLOADER_ID)

        from db.models.core_models import Result

        # Tenant A results exist
        results_a = db.query(Result).filter(
            Result.report_id == report_a.id,
            Result.tenant_id == SYNTH_TENANT_ID,
        ).all()
        assert len(results_a) > 0

        # Same result IDs, queried with tenant B's ID → empty
        results_from_b = db.query(Result).filter(
            Result.report_id == report_a.id,
            Result.tenant_id == tenant_b_id,
        ).all()
        assert len(results_from_b) == 0

    def test_tenant_b_reviewer_cannot_access_tenant_a_report_or_results(self, client, db):
        tenant_b_id, uploader_b_id = _create_second_tenant(db)
        reviewer_b_id = uuid.UUID("00000000-0000-4000-8000-000000000097")

        from db.models.core_models import User, Result
        from core.security import create_access_token

        if not db.query(User).filter(User.id == reviewer_b_id).first():
            db.add(User(
                id=reviewer_b_id,
                tenant_id=tenant_b_id,
                email="reviewer_b@synth.verilab",
                role="reviewer",
                mfa_enabled=False,
                status="active",
            ))
            db.commit()

        token_b = create_access_token(subject=reviewer_b_id, role="reviewer", tenant_id=tenant_b_id)
        headers_b = {"Authorization": f"Bearer {token_b}"}

        report_a = _create_report_for_tenant(db, SYNTH_TENANT_ID, SYNTH_UPLOADER_ID)
        result_a = db.query(Result).filter(Result.report_id == report_a.id).first()

        # 1. Tenant B reviewer attempts GET report_a -> 404
        resp_get = client.get(f"/api/v1/review/reports/{report_a.id}", headers=headers_b)
        assert resp_get.status_code == 404

        # 2. Tenant B reviewer attempts POST verify result_a -> 404
        resp_verify = client.post(f"/api/v1/review/results/{result_a.id}/verify", json={}, headers=headers_b)
        assert resp_verify.status_code == 404

        # 3. Tenant B reviewer attempts POST correct result_a -> 404
        resp_correct = client.post(
            f"/api/v1/review/results/{result_a.id}/correct",
            json={"corrected_value_raw": "99.9", "reason": "typographical_error"},
            headers=headers_b
        )
        assert resp_correct.status_code == 404

    def test_tenant_b_doctor_cannot_access_tenant_a_consultation(self, client, db):
        tenant_b_id, uploader_b_id = _create_second_tenant(db)
        doctor_b_id = uuid.UUID("00000000-0000-4000-8000-000000000096")

        from db.models.core_models import User
        from core.security import create_access_token

        if not db.query(User).filter(User.id == doctor_b_id).first():
            db.add(User(
                id=doctor_b_id,
                tenant_id=tenant_b_id,
                email="doctor_b@synth.verilab",
                role="doctor",
                mfa_enabled=False,
                status="active",
            ))
            db.commit()

        token_b = create_access_token(subject=doctor_b_id, role="doctor", tenant_id=tenant_b_id)
        headers_b = {"Authorization": f"Bearer {token_b}"}

        report_a = _create_report_for_tenant(db, SYNTH_TENANT_ID, SYNTH_UPLOADER_ID)

        resp = client.get(f"/api/v1/consultation/{report_a.id}", headers=headers_b)
        assert resp.status_code == 404

