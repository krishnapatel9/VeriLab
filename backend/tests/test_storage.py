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
