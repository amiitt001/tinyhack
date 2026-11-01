from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import AuthenticatedUser, get_current_user
from app.db import get_db
from app.repositories.profile import ProfileRepository
from app.schemas.profile import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_me(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    persisted = ProfileRepository().get_or_create_user(session, user.id, user.email)
    session.commit()
    return UserResponse(id=persisted.id, email=persisted.email, status=persisted.status)
