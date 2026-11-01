from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CareerProfile, User
from app.schemas.profile import ProfileUpdate


class ProfileRepository:
    def get_or_create_user(self, session: Session, user_id: str, email: str | None) -> User:
        user = session.get(User, user_id)
        if user is None:
            user = User(id=user_id, email=email)
            session.add(user)
            session.flush()
        elif email and user.email != email:
            user.email = email
        return user

    def get(self, session: Session, user_id: str) -> CareerProfile | None:
        return session.scalar(select(CareerProfile).where(CareerProfile.user_id == user_id))

    def upsert(
        self, session: Session, user_id: str, email: str | None, update: ProfileUpdate
    ) -> CareerProfile:
        self.get_or_create_user(session, user_id, email)
        profile = self.get(session, user_id)
        if profile is None:
            profile = CareerProfile(user_id=user_id)
            session.add(profile)
        for field, value in update.model_dump().items():
            setattr(profile, field, value)
        session.commit()
        session.refresh(profile)
        return profile
