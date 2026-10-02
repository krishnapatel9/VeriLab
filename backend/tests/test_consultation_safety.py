"""Consultation view must show corrected values and never hide unverified/flagged results."""

from db.models.core_models import Result
from tests.test_review import _setup_processed_report


def _consultation(client, headers, report_id):
    resp = client.get(f"/api/v1/consultation/{report_id}", headers=headers)
    assert resp.status_code == 200
    return resp.json()


def test_unverified_and_flagged_results_are_returned(client, db, doctor_headers):
    report, results, _ = _setup_processed_report(db)
    data = _consultation(client, doctor_headers, report.id)
    shown = data["selected_results"] + data["additional_results"]
    assert len(shown) == len(results)
    assert data["pending_count"] == len(results)
    assert all(r["verification_status"] in ("unverified", "needs_review") for r in shown)
    # TSH carries a printed "Low" flag and is not on the test list: it must still be in selected.
    assert any(r["test_name_raw"] == "TSH" for r in data["selected_results"])


def test_corrected_value_is_what_the_doctor_sees(client, db, reviewer_headers, doctor_headers):
    report, results, _ = _setup_processed_report(db)
    hgb = next(r for r in results if r.test_name_raw == "Hemoglobin")
    resp = client.post(
        f"/api/v1/review/results/{hgb.id}/correct",
        json={"corrected_value_raw": "2.5", "reason": "OCR misread"},
        headers=reviewer_headers,
    )
    assert resp.status_code == 200
    data = _consultation(client, doctor_headers, report.id)
    row = next(r for r in data["selected_results"] if r["test_name_raw"] == "Hemoglobin")
    assert row["value_raw"] == "2.5" and row["is_corrected"]
    assert row["original_value_raw"] == "12.5"
    db.expire_all()
    assert db.get(Result, hgb.id).value_raw == "12.5"  # OCR original untouched


def test_double_verify_conflicts(client, db, reviewer_headers):
    _, results, _ = _setup_processed_report(db)
    url = f"/api/v1/review/results/{results[0].id}/verify"
    assert client.post(url, json={}, headers=reviewer_headers).status_code == 200
    assert client.post(url, json={}, headers=reviewer_headers).status_code == 409


def test_original_file_is_served_and_tenant_scoped(client, db, uploader_headers, reviewer_headers):
    import io
    files = {"file": ("r.pdf", io.BytesIO(b"%PDF-1.4 synthetic"), "application/pdf")}
    rid = client.post("/api/v1/intake/upload", files=files, headers=uploader_headers).json()["report_id"]
    ok = client.get(f"/api/v1/intake/reports/{rid}/file", headers=reviewer_headers)
    assert ok.status_code == 200 and ok.content.startswith(b"%PDF-")
    assert client.get(f"/api/v1/intake/reports/{rid}/file", headers=uploader_headers).status_code == 403
