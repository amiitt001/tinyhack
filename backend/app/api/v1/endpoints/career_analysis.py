from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConfigurationError, IntegrationError
from app.core.security import AuthenticatedUser, get_current_user
from app.db import get_db
from app.models import CareerAnalysis, Resume
from app.schemas.career import CareerAnalysisResponse
from app.services.career_analysis import CareerAnalysisService

router = APIRouter(prefix="/career-analysis")


@router.get("", response_model=list[CareerAnalysisResponse])
def list_analyses(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[CareerAnalysisResponse]:
    return list(
        session.scalars(
            select(CareerAnalysis)
            .where(CareerAnalysis.user_id == user.id)
            .order_by(CareerAnalysis.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    )


@router.post("", response_model=CareerAnalysisResponse, status_code=201)
def create_analysis(
    resume_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> CareerAnalysisResponse:
    resume = session.scalar(select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id))
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    try:
        return CareerAnalysisService(get_settings()).run(session, user, resume)
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Career analysis provider is not configured") from exc
    except IntegrationError as exc:
        raise HTTPException(status_code=502, detail="Career analysis provider request failed") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{analysis_id}", response_model=CareerAnalysisResponse)
def get_analysis(
    analysis_id: UUID,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> CareerAnalysisResponse:
    analysis = session.scalar(
        select(CareerAnalysis).where(
            CareerAnalysis.id == analysis_id, CareerAnalysis.user_id == user.id
        )
    )
    if analysis is None:
        raise HTTPException(status_code=404, detail="Career analysis not found")
    return analysis
