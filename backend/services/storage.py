"""Where uploaded originals live.

STORAGE_BACKEND=local (default): files under STORAGE_DIR on this machine's disk.
STORAGE_BACKEND=db: files in the app's own database (stored_files table). No
    extra service needed; survives restarts on hosts without a persistent disk.
STORAGE_BACKEND=r2: files in a Cloudflare R2 bucket.

`db` is the caller's SQLAlchemy session. The db backend writes through it, so a
file is saved in the same transaction as its report; other backends ignore it.
"""

from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy.orm import Session

from constants import settings


class FileStorage:
    def put(self, key: str, data: bytes, db: Session | None = None) -> None:
        raise NotImplementedError

    def get(self, key: str, db: Session | None = None) -> bytes | None:
        """Return the file's bytes, or None if it does not exist."""
        raise NotImplementedError


class DatabaseStorage(FileStorage):
    def put(self, key: str, data: bytes, db: Session | None = None) -> None:
        from db.models.core_models import StoredFile

        if db is None:
            raise ValueError("DatabaseStorage.put needs the caller's session")
        if db.get(StoredFile, key) is None:  # same hash = same bytes; keep the original
            db.add(StoredFile(key=key, data=data, size_bytes=len(data)))
            db.flush()

    def get(self, key: str, db: Session | None = None) -> bytes | None:
        from db.models.core_models import StoredFile

        if db is not None:
            row = db.get(StoredFile, key)
            return bytes(row.data) if row else None
        from api.dependencies import SessionLocal

        with SessionLocal() as own:
            row = own.get(StoredFile, key)
            return bytes(row.data) if row else None


class LocalStorage(FileStorage):
    def __init__(self, root: str):
        self.root = root
        os.makedirs(root, exist_ok=True)

    def _path(self, key: str) -> str:
        path = os.path.abspath(os.path.join(self.root, key))
        if not path.startswith(os.path.abspath(self.root) + os.sep):
            raise ValueError("Storage key escapes the storage folder")
        return path

    def put(self, key: str, data: bytes, db: Session | None = None) -> None:
        path = self._path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    def get(self, key: str, db: Session | None = None) -> bytes | None:
        path = self._path(key)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return f.read()


class R2Storage(FileStorage):
    def __init__(self, account_id: str, access_key_id: str, secret_access_key: str, bucket: str):
        import boto3  # only needed when R2 is in use

        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )

    def put(self, key: str, data: bytes, db: Session | None = None) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data)

    def get(self, key: str, db: Session | None = None) -> bytes | None:
        try:
            return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()
        except self.client.exceptions.NoSuchKey:
            return None


@lru_cache(maxsize=1)
def get_storage() -> FileStorage:
    if settings.storage_backend == "db":
        return DatabaseStorage()
    if settings.storage_backend == "r2":
        missing = [n for n in ("r2_account_id", "r2_access_key_id", "r2_secret_access_key", "r2_bucket")
                   if not getattr(settings, n)]
        if missing:
            raise RuntimeError(f"STORAGE_BACKEND=r2 but these are not set: {', '.join(m.upper() for m in missing)}")
        return R2Storage(settings.r2_account_id, settings.r2_access_key_id,
                         settings.r2_secret_access_key, settings.r2_bucket)
    return LocalStorage(settings.storage_dir)
