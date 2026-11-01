from sqlalchemy.orm import Session

from app.core.security import AuthenticatedUser
from app.repositories.profile import ProfileRepository
from app.schemas.profile import ProfileUpdate


class ProfileService:
    def __init__(self, repository: ProfileRepository | None = None) -> None:
        self.repository = repository or ProfileRepository()

    def get_profile(self, session: Session, user: AuthenticatedUser):
        profile = self.repository.get(session, user.id)
        if profile is None:
            profile = self.repository.upsert(
                session,
                user.id,
                user.email,
                ProfileUpdate(),
            )
        return profile

    def update_profile(self, session: Session, user: AuthenticatedUser, update: ProfileUpdate):
        return self.repository.upsert(session, user.id, user.email, update)
