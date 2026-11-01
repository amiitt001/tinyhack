import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, IntegrationError


@dataclass(frozen=True)
class StoredObject:
    key: str


class StorageAdapter(Protocol):
    def upload(self, key: str, content: bytes, content_type: str) -> StoredObject: ...
    def download(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...


class LocalStorageAdapter:
    def __init__(self, settings: Settings, max_size: int = 10 * 1024 * 1024) -> None:
        self.root = Path(settings.local_storage_path).expanduser().resolve()
        self.max_size = max_size
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.root.chmod(0o700)

    @staticmethod
    def make_key(user_id: str, extension: str) -> str:
        return f"{user_id}/{uuid4()}{extension}"

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if path == self.root or self.root not in path.parents:
            raise ValueError("Invalid storage object key")
        return path

    def upload(self, key: str, content: bytes, content_type: str) -> StoredObject:
        if not content or len(content) > self.max_size:
            raise ValueError("Stored object must be between 1 byte and 10 MB")
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.parent.chmod(0o700)
        descriptor = None
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = None
                handle.write(content)
        except FileExistsError as exc:
            raise IntegrationError("Storage object already exists") from exc
        except Exception:
            if descriptor is not None:
                os.close(descriptor)
            path.unlink(missing_ok=True)
            raise
        return StoredObject(key=key)

    def download(self, key: str) -> bytes:
        try:
            return self._path(key).read_bytes()
        except FileNotFoundError as exc:
            raise IntegrationError("Storage object not found") from exc

    def delete(self, key: str) -> None:
        try:
            self._path(key).unlink()
        except FileNotFoundError:
            return


class SupabaseStorageAdapter:
    def __init__(self, settings: Settings) -> None:
        if not settings.supabase_url or not settings.supabase_storage_bucket:
            raise ConfigurationError("Supabase Storage is not configured")
        self.settings = settings

    def _bucket(self):
        from supabase import create_client

        service_key = self.settings.supabase_service_key
        if not service_key:
            raise ConfigurationError("Supabase server credential is not configured")
        return create_client(self.settings.supabase_url, service_key).storage.from_(
            self.settings.supabase_storage_bucket
        )

    def upload(self, key: str, content: bytes, content_type: str) -> StoredObject:
        try:
            self._bucket().upload(key, content, {"content-type": content_type, "upsert": "false"})
            return StoredObject(key=key)
        except Exception as exc:
            raise IntegrationError("Resume storage upload failed") from exc

    def delete(self, key: str) -> None:
        try:
            self._bucket().remove([key])
        except Exception as exc:
            raise IntegrationError("Resume storage deletion failed") from exc

    def download(self, key: str) -> bytes:
        try:
            return self._bucket().download(key)
        except Exception as exc:
            raise IntegrationError("Resume storage download failed") from exc


SupabaseStorage = SupabaseStorageAdapter


def create_storage_adapter(settings: Settings) -> StorageAdapter:
    if settings.storage_backend == "local":
        return LocalStorageAdapter(settings)
    return SupabaseStorageAdapter(settings)
