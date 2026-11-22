import pytest

from constants import settings
from services import storage
from services.storage import LocalStorage, get_storage


def test_local_storage_round_trip(tmp_path):
    s = LocalStorage(str(tmp_path))
    s.put("tenant-1/abc.pdf", b"%PDF-1.4 data")
    assert s.get("tenant-1/abc.pdf") == b"%PDF-1.4 data"
    assert s.get("tenant-1/missing.pdf") is None


def test_local_storage_rejects_keys_outside_root(tmp_path):
    s = LocalStorage(str(tmp_path / "root"))
    with pytest.raises(ValueError):
        s.put("../escape.pdf", b"x")


def test_r2_backend_requires_credentials(monkeypatch):
    monkeypatch.setattr(settings, "storage_backend", "r2")
    monkeypatch.setattr(settings, "r2_bucket", "")
    storage.get_storage.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="R2_BUCKET"):
            get_storage()
    finally:
        storage.get_storage.cache_clear()


def test_database_storage_round_trip(db):
    import uuid
    from services.storage import DatabaseStorage

    key = f"tenant-x/{uuid.uuid4()}.pdf"
    s = DatabaseStorage()
    s.put(key, b"%PDF-1.4 in the db", db)
    db.commit()
    assert s.get(key, db) == b"%PDF-1.4 in the db"
    assert s.get("tenant-x/missing.pdf", db) is None
    s.put(key, b"%PDF-1.4 in the db", db)  # re-upload of the same file is a no-op
    db.commit()


def test_upload_and_view_with_database_storage(client, monkeypatch, uploader_headers, reviewer_headers):
    import io
    import uuid

    monkeypatch.setattr(settings, "storage_backend", "db")
    storage.get_storage.cache_clear()
    try:
        body = b"%PDF-1.4 db-backed " + uuid.uuid4().bytes.hex().encode()
        files = {"file": ("r.pdf", io.BytesIO(body), "application/pdf")}
        rid = client.post("/api/v1/intake/upload", files=files, headers=uploader_headers).json()["report_id"]
        resp = client.get(f"/api/v1/intake/reports/{rid}/file", headers=reviewer_headers)
        assert resp.status_code == 200 and resp.content == body
    finally:
        storage.get_storage.cache_clear()
