"""Authenticated opportunity discovery and saved-opportunity endpoints."""

from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConfigurationError
from app.core.security import AuthenticatedUser, get_current_user
from app.db import SessionLocal, get_db
from app.models.opportunity import DiscoveryRun, TinyFishExecution
from app.repositories.opportunity import (
    DiscoveryRunRepository,
    OpportunityDetailRepository,
    SavedOpportunityRepository,
)
from app.repositories.profile import ProfileRepository
from app.schemas.opportunity import (
    CreateDiscoveryRequest,
    DiscoveryRunResponse,
    OpportunityResponse,
    PaginatedOpportunityResponse,
    PaginatedSavedOpportunityResponse,
    SavedOpportunityResponse,
    SaveRequest,
    TinyFishExecutionResponse,
)
from app.services.discovery import DiscoveryService

logger = logging.getLogger(__name__)
router = APIRouter()

_run_repo = DiscoveryRunRepository()
_opportunity_repo = OpportunityDetailRepository()
_saved_repo = SavedOpportunityRepository()
_profile_repo = ProfileRepository()


def _execute_discovery(run_id: uuid.UUID) -> None:
    """Run a queued discovery with a task-owned session.

    FastAPI BackgroundTasks are in-process and are not durable across process
    termination. A future worker queue is required for reliable recovery.
    """
    with SessionLocal() as session:
        try:
            DiscoveryService(get_settings()).execute_run(run_id, session)
        except Exception as exc:
            session.rollback()
            run = session.get(DiscoveryRun, run_id)
            if run is not None and run.status in {"pending", "running"}:
                _run_repo.mark_failed(
                    session,
                    run,
                    error_code="discovery_execution_error",
                    safe_error_message="Discovery could not be completed. Please try again.",
                )
                session.commit()
            logger.error(
                "Discovery execution failed run_id=%s error_type=%s",
                run_id,
                type(exc).__name__,
            )


@router.post(
    "/opportunity-discoveries",
    response_model=DiscoveryRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_discovery(
    body: CreateDiscoveryRequest,
    background_tasks: BackgroundTasks,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> DiscoveryRunResponse:
    try:
        _profile_repo.get_or_create_user(session, user.id, user.email)
        session.commit()
        service = DiscoveryService(get_settings())
    except ConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Discovery provider is not configured") from exc

    if body.sources:
        from app.integrations.source_registry import source_registry

        _, rejected = source_registry.resolve_requested(body.sources)
        if rejected:
            raise HTTPException(
                status_code=422,
                detail={"code": "unsupported_sources", "sources": rejected},
            )

    try:
        run, created = service.create_run(
            session,
            user,
            query=body.query,
            location=body.location,
            employment_type=body.employment_type,
            experience_level=body.experience_level,
            skills=body.skills,
            requested_sources=body.sources,
            idempotency_key=body.idempotency_key,
            refresh=body.refresh,
        )
    except IntegrityError as exc:
        session.rollback()
        if body.idempotency_key:
            existing = _run_repo.find_by_idempotency_key(
                session, user_id=user.id, idempotency_key=body.idempotency_key
            )
            if existing is not None:
                return existing
        raise HTTPException(
            status_code=409, detail="Discovery request conflicts with an existing run"
        ) from exc
    if created:
        background_tasks.add_task(_execute_discovery, run.id)
    return run


@router.get("/opportunity-discoveries/{run_id}", response_model=DiscoveryRunResponse)
def get_discovery(
    run_id: uuid.UUID,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> DiscoveryRunResponse:
    run = _run_repo.get_for_user(session, run_id=run_id, user_id=user.id)
    if run is None:
        raise HTTPException(status_code=404, detail="Discovery run not found")
    return run


@router.get(
    "/opportunity-discoveries/{run_id}/executions",
    response_model=list[TinyFishExecutionResponse],
)
def get_discovery_executions(
    run_id: uuid.UUID,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[TinyFishExecutionResponse]:
    if _run_repo.get_for_user(session, run_id=run_id, user_id=user.id) is None:
        raise HTTPException(status_code=404, detail="Discovery run not found")
    return list(
        session.scalars(
            select(TinyFishExecution)
            .where(TinyFishExecution.discovery_run_id == run_id)
            .order_by(TinyFishExecution.started_at)
        )
    )


@router.get(
    "/opportunity-discoveries/{run_id}/results",
    response_model=PaginatedOpportunityResponse,
)
def get_discovery_results(
    run_id: uuid.UUID,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PaginatedOpportunityResponse:
    if _run_repo.get_for_user(session, run_id=run_id, user_id=user.id) is None:
        raise HTTPException(status_code=404, detail="Discovery run not found")
    return PaginatedOpportunityResponse(
        items=_opportunity_repo.list_for_run_page(
            session, run_id=run_id, limit=limit, offset=offset
        ),
        total=_opportunity_repo.count_for_run(session, run_id=run_id),
        limit=limit,
        offset=offset,
    )


@router.get("/opportunities/saved", response_model=PaginatedSavedOpportunityResponse)
def list_saved_opportunities(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PaginatedSavedOpportunityResponse:
    return PaginatedSavedOpportunityResponse(
        items=_saved_repo.list_saved(session, user_id=user.id, limit=limit, offset=offset),
        total=_saved_repo.count_saved(session, user_id=user.id),
        limit=limit,
        offset=offset,
    )


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
def get_opportunity(
    opportunity_id: uuid.UUID,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> OpportunityResponse:
    del user  # Authentication is required; discovery records are shared catalog entries.
    opportunity = _opportunity_repo.get_by_id(session, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunity


@router.post(
    "/opportunities/{opportunity_id}/save",
    response_model=SavedOpportunityResponse,
    status_code=status.HTTP_201_CREATED,
)
def save_opportunity(
    opportunity_id: uuid.UUID,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
    body: SaveRequest | None = None,
) -> SavedOpportunityResponse:
    if _opportunity_repo.get_by_id(session, opportunity_id) is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    _profile_repo.get_or_create_user(session, user.id, user.email)
    saved = _saved_repo.save(
        session,
        user_id=user.id,
        opportunity_detail_id=opportunity_id,
        notes=body.notes if body else None,
    )
    session.commit()
    return saved


@router.delete("/opportunities/{opportunity_id}/save", status_code=status.HTTP_204_NO_CONTENT)
def unsave_opportunity(
    opportunity_id: uuid.UUID,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> Response:
    if not _saved_repo.unsave(session, user_id=user.id, opportunity_detail_id=opportunity_id):
        raise HTTPException(status_code=404, detail="Saved opportunity not found")
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
