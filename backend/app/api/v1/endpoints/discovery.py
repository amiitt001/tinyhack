from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import AuthenticatedUser, get_current_user
from app.db import get_db
from app.discovery.sources import REGISTRY, source_status
from app.repositories.discovery import DiscoveryRepository
from app.schemas.discovery import (
    DiscoveryErrorResponse,
    DiscoveryRequest,
    DiscoveryResponse,
    OpportunityPage,
    OpportunityResponse,
    SaveResponse,
    SourceResponse,
)
from app.services.discovery import DiscoveryService

router = APIRouter(
    responses={
        code: {"model": DiscoveryErrorResponse} for code in (400, 401, 404, 409, 422, 429, 503)
    }
)
UserDependency = Annotated[AuthenticatedUser, Depends(get_current_user)]
SessionDependency = Annotated[Session, Depends(get_db)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.get(
    "/opportunity-sources", response_model=list[SourceResponse], tags=["opportunity-discovery"]
)
def list_sources(user: UserDependency, settings: SettingsDependency) -> list[SourceResponse]:
    return [
        SourceResponse(
            name=policy.name,
            status=source_status(policy, settings),
            supported=policy.supported,
            configured=policy.name == "official_company_careers",
            allowed_domains=policy.allowed_domains,
            behavior=policy.behavior if policy.supported else "not_implemented",
            attribution=policy.attribution,
            validation_policy="HTTPS, source-domain/path, robots, JSON-LD, no redirects",
            access_restrictions="Reviewed public company pages only; no login, CAPTCHA bypass or applications",
        )
        for policy in REGISTRY.values()
    ]


@router.post(
    "/opportunity-discoveries",
    response_model=DiscoveryResponse,
    status_code=202,
    tags=["opportunity-discovery"],
    description="Queue a persistent user-owned discovery. Reuse Idempotency-Key only for an identical request. Execution is process-local, not a durable distributed queue.",
)
def create_discovery(
    body: DiscoveryRequest,
    request: Request,
    user: UserDependency,
    session: SessionDependency,
    settings: SettingsDependency,
    idempotency_key: Annotated[
        str, Header(min_length=8, max_length=128, pattern=r"^[a-zA-Z0-9._:-]+$")
    ],
) -> DiscoveryResponse:
    run, created = DiscoveryService(settings).create(session, user, body, idempotency_key)
    response = DiscoveryResponse.model_validate(run)
    if created:
        request.app.state.discovery_executor.submit(run.id)
    return response


@router.get(
    "/opportunity-discoveries/{run_id}",
    response_model=DiscoveryResponse,
    tags=["opportunity-discovery"],
)
def get_discovery(
    run_id: UUID, user: UserDependency, session: SessionDependency, settings: SettingsDependency
) -> DiscoveryResponse:
    return DiscoveryResponse.model_validate(
        DiscoveryService(settings).owned_run(session, user.id, run_id)
    )


@router.get(
    "/opportunity-discoveries/{run_id}/results",
    response_model=OpportunityPage,
    tags=["opportunity-discovery"],
)
def discovery_results(
    run_id: UUID,
    user: UserDependency,
    session: SessionDependency,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=10000),
) -> OpportunityPage:
    return DiscoveryRepository().page(session, user.id, limit, offset, run_id)


# Declare /saved before /{opportunity_id} so it is never interpreted as a UUID.
@router.get("/opportunities/saved", response_model=OpportunityPage, tags=["opportunities"])
def saved_opportunities(
    user: UserDependency,
    session: SessionDependency,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=10000),
) -> OpportunityPage:
    return DiscoveryRepository().page(session, user.id, limit, offset)


@router.get(
    "/opportunities/{opportunity_id}", response_model=OpportunityResponse, tags=["opportunities"]
)
def opportunity_details(
    opportunity_id: UUID, user: UserDependency, session: SessionDependency
) -> OpportunityResponse:
    return DiscoveryRepository().details(session, opportunity_id)


@router.post(
    "/opportunities/{opportunity_id}/save", response_model=SaveResponse, tags=["opportunities"]
)
def save_opportunity(
    opportunity_id: UUID, user: UserDependency, session: SessionDependency
) -> SaveResponse:
    DiscoveryRepository().save(session, user, opportunity_id)
    return SaveResponse(opportunity_id=opportunity_id, saved=True)


@router.delete(
    "/opportunities/{opportunity_id}/save", response_model=SaveResponse, tags=["opportunities"]
)
def unsave_opportunity(
    opportunity_id: UUID, user: UserDependency, session: SessionDependency
) -> SaveResponse:
    DiscoveryRepository().unsave(session, user.id, opportunity_id)
    return SaveResponse(opportunity_id=opportunity_id, saved=False)
