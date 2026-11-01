from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.exceptions import ConfigurationError, TinyFishError, TinyFishInvalidResponseError
from app.core.security import AuthenticatedUser, get_current_user
from app.integrations.source_registry import source_registry
from app.integrations.tinyfish import TinyFishAdapter
from app.integrations.tinyfish_fetch import TinyFishFetchAdapter

router = APIRouter(prefix="/opportunity-tools")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=512)
    location: str | None = Field(default=None, max_length=255)
    page: int = Field(default=0, ge=0, le=10)


class SearchResult(BaseModel):
    position: int
    title: str
    url: str
    site_name: str
    snippet: str
    date: str | None
    publisher: str | None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total_results: int
    page: int


class FetchRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)


class FetchResponse(BaseModel):
    url: str
    final_url: str | None
    title: str | None
    text: str
    latency_ms: float | None


def _provider_error(exc: TinyFishError) -> HTTPException:
    if isinstance(exc, TinyFishInvalidResponseError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=502, detail=str(exc))


@router.post("/search", response_model=SearchResponse)
def search(
    body: SearchRequest,
    _user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> SearchResponse:
    try:
        response = TinyFishAdapter(get_settings()).search(
            body.query.strip(),
            location=body.location.strip() if body.location else None,
            page=body.page,
        )
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Opportunity search is not configured") from exc
    except TinyFishError as exc:
        raise _provider_error(exc) from exc
    return SearchResponse(
        query=response.query,
        results=[
            SearchResult(
                position=item.position,
                title=item.title,
                url=item.url,
                site_name=item.site_name,
                snippet=item.snippet,
                date=item.date,
                publisher=item.publisher,
            )
            for item in response.results
        ],
        total_results=response.total_results,
        page=response.page,
    )


@router.post("/fetch", response_model=FetchResponse)
def fetch(
    body: FetchRequest,
    _user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> FetchResponse:
    source = source_registry.get("official_company_careers")
    if source is None:
        raise HTTPException(status_code=503, detail="Opportunity source policy is unavailable")
    try:
        page = TinyFishFetchAdapter(get_settings()).fetch(
            body.url.strip(), allowed_domains=source.allowed_domains
        )
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Opportunity fetch is not configured") from exc
    except TinyFishError as exc:
        raise _provider_error(exc) from exc
    return FetchResponse(
        url=page.url,
        final_url=page.final_url,
        title=page.title,
        text=page.text or "",
        latency_ms=page.latency_ms,
    )
