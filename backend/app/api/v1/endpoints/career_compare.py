from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.exceptions import ConfigurationError, IntegrationError
from app.core.security import AuthenticatedUser, get_current_user
from app.integrations.gemini import GeminiCareerAnalyzer

router = APIRouter(prefix="/career-comparisons")


class CareerCompareRequest(BaseModel):
    first_career: str = Field(..., min_length=1, max_length=200)
    second_career: str = Field(..., min_length=1, max_length=200)
    profile_summary: str = Field(default="", max_length=12000)


class CareerCompareResponse(BaseModel):
    first_career: str
    second_career: str
    summary: str
    career_a_fit: str
    career_b_fit: str
    shared_skills: list[str]
    tradeoffs: list[str]
    recommended_next_step: str
    limitations: list[str]
    model: str


@router.post("", response_model=CareerCompareResponse)
def compare_careers(
    body: CareerCompareRequest,
    _user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> CareerCompareResponse:
    if body.first_career == body.second_career:
        raise HTTPException(status_code=422, detail="Choose two different career paths")
    settings = get_settings()
    try:
        result = GeminiCareerAnalyzer(settings).compare_careers(
            body.first_career, body.second_career, body.profile_summary
        )
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Career comparison provider is not configured") from exc
    except IntegrationError as exc:
        raise HTTPException(status_code=502, detail="Career comparison provider request failed") from exc
    return CareerCompareResponse(
        first_career=body.first_career,
        second_career=body.second_career,
        model=settings.gemini_model,
        **result,
    )
