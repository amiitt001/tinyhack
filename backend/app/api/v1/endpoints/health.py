from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_db

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready(session: Session = Depends(get_db)) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    return {"status": "ready"}


@router.get("/integrations")
def integrations() -> dict[str, object]:
    """Expose safe provider configuration status without credentials."""
    settings = get_settings()
    return {
        "status": "ready",
        "gemini": {
            "configured": bool(settings.gemini_api_key),
            "model": settings.gemini_model,
        },
        "tinyfish": {
            "configured": bool(settings.tinyfish_api_key),
            "agent_enabled": settings.tinyfish_agent_enabled,
        },
        "supabase": {
            "configured": bool(settings.supabase_url and settings.supabase_service_key),
            "storage_backend": settings.storage_backend,
        },
    }
