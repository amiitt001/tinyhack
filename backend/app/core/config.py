from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "skillsphere-v3-api"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql://localhost:5432/skillsphere"
    auth_mode: str = "supabase"
    storage_backend: str = "supabase"
    local_storage_path: str = "./.local-storage"
    supabase_url: str | None = None
    supabase_jwt_secret: str | None = None
    supabase_service_key: str | None = None
    supabase_jwt_jwks_url: str | None = None
    supabase_jwt_issuer: str | None = None
    supabase_jwt_audience: str = "authenticated"
    supabase_storage_bucket: str = "resumes"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    agent_timeout_seconds: float = 30.0
    agent_max_attempts: int = 3
    agent_retry_base_seconds: float = 1.0
    tinyfish_api_key: str | None = None
    tinyfish_base_url: str | None = None
    tinyfish_timeout_seconds: float = Field(default=10, ge=1, le=30)
    tinyfish_max_attempts: int = Field(default=3, ge=1, le=4)
    tinyfish_retry_base_seconds: float = Field(default=0.5, ge=0, le=2)
    discovery_enabled: bool = False
    discovery_official_source_reviewed: bool = False
    discovery_workers: int = Field(default=2, ge=1, le=4)
    discovery_queue_size: int = Field(default=4, ge=0, le=16)
    discovery_timeout_seconds: int = Field(default=120, ge=10, le=300)
    discovery_max_results: int = Field(default=10, ge=1, le=20)
    discovery_search_pages: int = Field(default=1, ge=1, le=3)
    cors_origins: str = "http://localhost:3000"
    retention_temp_upload_hours: int = 24
    retention_deleted_document_days: int = 30
    retention_conversation_days: int = 180
    retention_agent_run_days: int = 30
    retention_audit_event_days: int = 365

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    @model_validator(mode="after")
    def validate_runtime_configuration(self) -> "Settings":
        if self.app_env == "production" and self.auth_mode != "supabase":
            raise ValueError("AUTH_MODE=development is not allowed when APP_ENV=production")
        if self.app_env == "production" and self.storage_backend != "supabase":
            raise ValueError("STORAGE_BACKEND=local is not allowed when APP_ENV=production")
        if self.auth_mode not in {"development", "supabase"}:
            raise ValueError("AUTH_MODE must be development or supabase")
        if self.storage_backend not in {"local", "supabase"}:
            raise ValueError("STORAGE_BACKEND must be local or supabase")
        if self.storage_backend == "local" and not self.local_storage_path.strip():
            raise ValueError("LOCAL_STORAGE_PATH is required for local storage")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return self.database_url

    @property
    def jwt_jwks_url(self) -> str | None:
        if self.supabase_jwt_jwks_url:
            return self.supabase_jwt_jwks_url
        if self.supabase_url:
            return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        return None

    @property
    def jwt_issuer(self) -> str | None:
        return self.supabase_jwt_issuer or (
            f"{self.supabase_url.rstrip('/')}/auth/v1" if self.supabase_url else None
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
