import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConfigurationError, IntegrationError
from app.core.security import AuthenticatedUser, get_current_user
from app.db import get_db
from app.schemas.profile import ProfileUpdate
from app.schemas.resume import ResumeResponse
from app.services.profile import ProfileService
from app.services.resume import ResumeService

router = APIRouter(prefix="/resumes")


def service() -> ResumeService:
    return ResumeService(get_settings())


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: Annotated[UploadFile, File()],
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> ResumeResponse:
    content = await file.read()
    try:
        resume = service().upload(
            session, user, file.filename or "resume", file.content_type or "", content
        )
        if resume.parsed_data:
            profile = ProfileService().get_profile(session, user)
            if not profile.summary:
                parsed = resume.parsed_data
                fields = {
                    "name": parsed.get("name", ""),
                    "location": parsed.get("location", ""),
                    "skills": ", ".join(parsed.get("technical_skills", [])),
                    "experience": "\n".join(
                        item.get("role") or item.get("description") or ""
                        for item in parsed.get("experience", [])
                    ),
                    "projects": "\n".join(parsed.get("projects", [])),
                    "education": "\n".join(
                        item.get("institution") or "" for item in parsed.get("education", [])
                    ),
                }
                fields = {key: value for key, value in fields.items() if value}
                ProfileService().update_profile(
                    session,
                    user,
                    ProfileUpdate(
                        summary=json.dumps(fields),
                        completion_percent=min(100, round(len(fields) / 6 * 100)),
                        career_stage="development",
                    ),
                )
        return resume
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Resume storage is not configured") from exc
    except IntegrationError as exc:
        raise HTTPException(status_code=502, detail="Resume storage request failed") from exc


@router.get("", response_model=list[ResumeResponse])
def list_resumes(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[ResumeResponse]:
    try:
        return service().list(session, user)
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Resume storage is not configured") from exc
    except IntegrationError as exc:
        raise HTTPException(status_code=502, detail="Resume storage request failed") from exc


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> ResumeResponse:
    try:
        resume = service().get(session, user, resume_id)
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Resume storage is not configured") from exc
    except IntegrationError as exc:
        raise HTTPException(status_code=502, detail="Resume storage request failed") from exc
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> None:
    try:
        deleted = service().delete(session, user, resume_id)
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Resume storage is not configured") from exc
    except IntegrationError as exc:
        raise HTTPException(status_code=502, detail="Resume storage request failed") from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Resume not found")
