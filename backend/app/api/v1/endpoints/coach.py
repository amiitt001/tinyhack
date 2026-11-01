from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.exceptions import ConfigurationError, IntegrationError
from app.core.security import AuthenticatedUser, get_current_user
from app.integrations.gemini import GeminiCareerAnalyzer

router = APIRouter(prefix="/coach")


class CoachRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    profile_summary: str = Field(default="", max_length=12000)


class CoachResponse(BaseModel):
    response: str
    model: str


@router.post("", response_model=CoachResponse)
def coach(
    body: CoachRequest,
    _user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> CoachResponse:
    try:
        analyzer = GeminiCareerAnalyzer(get_settings())
        response = analyzer.coach(body.message.strip(), body.profile_summary)
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Career coach provider is not configured") from exc
    except IntegrationError as exc:
        raise HTTPException(status_code=502, detail="Career coach provider request failed") from exc
    return CoachResponse(response=response, model=get_settings().gemini_model)
