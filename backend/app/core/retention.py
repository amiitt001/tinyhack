from dataclasses import dataclass

from app.core.config import Settings


@dataclass(frozen=True)
class RetentionPolicy:
    temp_upload_hours: int
    deleted_document_days: int
    conversation_days: int
    agent_run_days: int
    audit_event_days: int

    @classmethod
    def from_settings(cls, settings: Settings) -> "RetentionPolicy":
        return cls(
            temp_upload_hours=settings.retention_temp_upload_hours,
            deleted_document_days=settings.retention_deleted_document_days,
            conversation_days=settings.retention_conversation_days,
            agent_run_days=settings.retention_agent_run_days,
            audit_event_days=settings.retention_audit_event_days,
        )
