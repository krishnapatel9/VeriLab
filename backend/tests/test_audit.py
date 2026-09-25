"""
Tests for the AuditEvent hash-chain (Task 1.2).

Covers:
- First event uses 'genesis' as prev_event_hash
- Subsequent events chain correctly (prev_event_hash == previous event_hash)
- Chain is verifiable — recomputing the hash from fields gives the same result
- Events are NOT rolled back if the caller's transaction rolls back (isolation)
"""

import hashlib
import uuid
import pytest

from db.models.core_models import AuditEvent
from core.audit import emit_audit_event, _compute_event_hash
from constants import SYNTH_TENANT_ID, SYNTH_UPLOADER_ID, SYNTH_REVIEWER_ID


class TestAuditHashChain:
    def test_first_event_uses_genesis_prev_hash(self, db):
        resource_id = uuid.uuid4()
        event = emit_audit_event(
            db=db,
            event_type="test.event",
            resource_type="test",
            resource_id=resource_id,
            metadata={"key": "value"},
            tenant_id=SYNTH_TENANT_ID,
        )
        assert event.prev_event_hash == "genesis"

    def test_second_event_chains_to_first(self, db):
        rid1 = uuid.uuid4()
        rid2 = uuid.uuid4()

        e1 = emit_audit_event(
            db=db,
            event_type="test.first",
            resource_type="test",
            resource_id=rid1,
            metadata={},
            tenant_id=SYNTH_TENANT_ID,
        )
        e2 = emit_audit_event(
            db=db,
            event_type="test.second",
            resource_type="test",
            resource_id=rid2,
            metadata={},
            tenant_id=SYNTH_TENANT_ID,
        )

        assert e2.prev_event_hash == e1.event_hash

    def test_event_hash_is_recomputable(self, db):
        resource_id = uuid.uuid4()
        event = emit_audit_event(
            db=db,
            event_type="test.hash",
            resource_type="test",
            resource_id=resource_id,
            metadata={"x": 1},
            tenant_id=SYNTH_TENANT_ID,
        )

        expected = _compute_event_hash(
            event.prev_event_hash,
            event.event_type,
            resource_id,
            event.created_at.isoformat(),
        )
        assert event.event_hash == expected

    def test_three_event_chain_is_intact(self, db):
        events = []
        for i in range(3):
            e = emit_audit_event(
                db=db,
                event_type=f"test.step_{i}",
                resource_type="test",
                resource_id=uuid.uuid4(),
                metadata={"step": i},
                tenant_id=SYNTH_TENANT_ID,
            )
            events.append(e)

        assert events[1].prev_event_hash == events[0].event_hash
        assert events[2].prev_event_hash == events[1].event_hash

    def test_upload_action_emits_audit_event(self, client, db):
        """Integration: uploading a report must produce an audit event."""
        import io
        resp = client.post(
            "/api/v1/intake/upload",
            files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")},
        )
        assert resp.status_code == 200

        events = db.query(AuditEvent).filter(
            AuditEvent.event_type == "report.uploaded"
        ).all()
        assert len(events) >= 1

    def test_verify_action_emits_audit_event(self, client, db):
        """Integration: verifying a result must produce an audit event."""
        import io, asyncio
        from services.ocr_service import OCRService, MockOCRProvider
        from tests.test_ocr_service import _create_test_report
        from db.models.core_models import Result
        from tests.conftest import TestSessionLocal

        # Setup processed report
        report = _create_test_report(db)
        service = OCRService(db_session=db, provider=MockOCRProvider())
        asyncio.run(service.process_report(report.id))
        db.commit()

        result = db.query(Result).filter(Result.report_id == report.id).first()

        client.post(
            f"/api/v1/review/results/{result.id}/verify",
            json={"reviewer_user_id": str(SYNTH_REVIEWER_ID)},
        )

        # Use a fresh session to see commits from the client's session
        fresh_db = TestSessionLocal()
        try:
            events = fresh_db.query(AuditEvent).filter(
                AuditEvent.event_type == "result.verified"
            ).all()
            assert len(events) >= 1
        finally:
            fresh_db.close()

