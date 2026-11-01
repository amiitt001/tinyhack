from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Resume


class ResumeRepository:
    def create(self, session: Session, resume: Resume) -> Resume:
        session.add(resume)
        session.commit()
        session.refresh(resume)
        return resume

    def list_for_user(self, session: Session, user_id: str) -> list[Resume]:
        return list(
            session.scalars(
                select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())
            )
        )

    def get_for_user(self, session: Session, user_id: str, resume_id: UUID) -> Resume | None:
        return session.scalar(
            select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
        )

    def delete(self, session: Session, resume: Resume) -> None:
        session.delete(resume)
        session.commit()
