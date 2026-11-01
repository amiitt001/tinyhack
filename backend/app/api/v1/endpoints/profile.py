from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import AuthenticatedUser, get_current_user
from app.db import get_db
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services.profile import ProfileService

router = APIRouter()


@router.get("/career-profile", response_model=ProfileResponse)
def get_profile(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> ProfileResponse:
    profile = ProfileService().get_profile(session, user)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Career profile not found"
        )
    return profile


@router.put("/career-profile", response_model=ProfileResponse)
def put_profile(
    update: ProfileUpdate,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> ProfileResponse:
    return ProfileService().update_profile(session, user, update)
