import uuid

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import IntegrationError
from app.core.security import AuthenticatedUser
from app.integrations.storage import StorageAdapter, create_storage_adapter
from app.models import Resume, User
from app.repositories.resume import ResumeRepository
from app.services.resume_parser import ResumeParser


class ResumeService:
    def __init__(
        self,
        settings: Settings,
        repository: ResumeRepository | None = None,
        storage: StorageAdapter | None = None,
        parser: ResumeParser | None = None,
    ) -> None:
        self.repository = repository or ResumeRepository()
        self.storage = storage or create_storage_adapter(settings)
        self.parser = parser or ResumeParser()
        self.max_size = 10 * 1024 * 1024

    def upload(
        self,
        session: Session,
        user: AuthenticatedUser,
        filename: str,
        mime_type: str,
        content: bytes,
    ) -> Resume:
        if mime_type not in ResumeParser.SUPPORTED:
            raise ValueError("Only PDF, DOCX, and plain text resumes are supported")
        if not content or len(content) > self.max_size:
            raise ValueError("Resume must be between 1 byte and 10 MB")
        if session.get(User, user.id) is None:
            session.add(User(id=user.id, email=user.email))
            session.flush()
        resume_id = uuid.uuid4()
        extension = ResumeParser.SUPPORTED[mime_type]
        key = (
            self.storage.make_key(user.id, extension)
            if hasattr(self.storage, "make_key")
            else f"{user.id}/{resume_id}{extension}"
        )
        uploaded = False
        try:
            self.storage.upload(key, content, mime_type)
            uploaded = True
            resume = Resume(
                id=resume_id,
                user_id=user.id,
                storage_key=key,
                filename=filename,
                mime_type=mime_type,
                size_bytes=len(content),
            )
            parsed = self.parser.parse(content, mime_type)
            resume.parsed_data = parsed.model_dump()
            resume.status = "parsed"
        except (ValueError, IntegrationError) as exc:
            if not uploaded:
                raise
            if "resume" not in locals():
                self.storage.delete(key)
                raise
            resume.status = "parse_failed"
            resume.parse_error = str(exc)
        except Exception:
            if uploaded:
                self.storage.delete(key)
            raise
        try:
            return self.repository.create(session, resume)
        except Exception:
            self.storage.delete(key)
            raise

    def list(self, session: Session, user: AuthenticatedUser) -> list[Resume]:
        return self.repository.list_for_user(session, user.id)

    def get(self, session: Session, user: AuthenticatedUser, resume_id):
        return self.repository.get_for_user(session, user.id, resume_id)

    def delete(self, session: Session, user: AuthenticatedUser, resume_id) -> bool:
        resume = self.get(session, user, resume_id)
        if resume is None:
            return False
        self.storage.delete(resume.storage_key)
        self.repository.delete(session, resume)
        return True
