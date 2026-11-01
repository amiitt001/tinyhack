from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.security import AuthenticatedUser, get_current_user
from app.integrations.storage import LocalStorageAdapter


def test_local_storage_is_private_user_scoped_and_round_trips(tmp_path: Path):
    adapter = LocalStorageAdapter(
        Settings(storage_backend="local", local_storage_path=str(tmp_path))
    )
    key = adapter.make_key("user-a", ".pdf")
    stored = adapter.upload(key, b"%PDF synthetic", "application/pdf")

    assert stored.key == key
    assert key.startswith("user-a/")
    assert adapter.download(key) == b"%PDF synthetic"
    assert not (tmp_path.parent / "user-a").exists()
    adapter.delete(key)
    with pytest.raises(Exception, match="not found"):
        adapter.download(key)


def test_local_storage_rejects_path_traversal(tmp_path: Path):
    adapter = LocalStorageAdapter(
        Settings(storage_backend="local", local_storage_path=str(tmp_path))
    )
    with pytest.raises(ValueError, match="Invalid storage object key"):
        adapter.upload("../outside.txt", b"data", "text/plain")


def test_production_rejects_development_auth_and_local_storage():
    with pytest.raises(ValueError, match="AUTH_MODE"):
        Settings(app_env="production", auth_mode="development")
    with pytest.raises(ValueError, match="STORAGE_BACKEND"):
        Settings(app_env="production", storage_backend="local")


@pytest.mark.asyncio
async def test_development_authentication_is_user_scoped():
    settings = Settings(auth_mode="development", app_env="development")

    class Request:
        headers = {"Authorization": "Bearer dev:user-a"}

    user = await get_current_user(Request(), settings)
    assert isinstance(user, AuthenticatedUser)
    assert user.id == "user-a"
    assert user.claims["auth_mode"] == "development"
