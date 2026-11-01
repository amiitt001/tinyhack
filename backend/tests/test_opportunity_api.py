from __future__ import annotations

import uuid

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.api.v1.endpoints import opportunities
from app.core.config import Settings
from app.core.security import AuthenticatedUser
from app.models import DiscoveryRun, OpportunityDetail, User
from app.schemas.opportunity import CreateDiscoveryRequest, OpportunityResponse, SaveRequest


def new_user(session, prefix: str) -> AuthenticatedUser:
    user_id = f"{prefix}-{uuid.uuid4()}"
    session.add(User(id=user_id, email=None))
    session.commit()
    return AuthenticatedUser(id=user_id, email=None, claims={})


def test_openapi_registers_all_authenticated_discovery_paths():
    from app.main import app

    paths = app.openapi()["paths"]
    assert "/api/v1/opportunity-discoveries" in paths
    assert "/api/v1/opportunity-discoveries/{run_id}" in paths
    assert "/api/v1/opportunity-discoveries/{run_id}/results" in paths
    assert "/api/v1/opportunities/{opportunity_id}" in paths
    assert "/api/v1/opportunities/{opportunity_id}/save" in paths
    assert "/api/v1/opportunities/saved" in paths
    assert paths["/api/v1/opportunity-discoveries"]["post"]["security"] == [{"HTTPBearer": []}]
    for route in opportunities.router.routes:
        assert any(dep.call.__name__ == "get_current_user" for dep in route.dependant.dependencies)


def test_discovery_creation_schedules_once_and_honors_idempotency(db_session, monkeypatch):
    user = new_user(db_session, "api-user")
    monkeypatch.setattr(
        opportunities, "get_settings", lambda: Settings(tinyfish_api_key="mock-key")
    )
    body = CreateDiscoveryRequest(
        query="Python Developer Intern",
        location="Delhi NCR",
        employment_type="internship",
        skills=["Python", "SQL", "FastAPI"],
        idempotency_key="same-request",
    )
    tasks = BackgroundTasks()
    first = opportunities.create_discovery(body, tasks, user, db_session)
    assert first.status == "pending"
    assert first.user_id == user.id
    assert len(tasks.tasks) == 1
    duplicate_tasks = BackgroundTasks()
    second = opportunities.create_discovery(body, duplicate_tasks, user, db_session)
    assert second.id == first.id
    assert duplicate_tasks.tasks == []


def test_discovery_run_and_results_are_owner_scoped(db_session):
    owner = new_user(db_session, "owner")
    other = new_user(db_session, "other")
    run = DiscoveryRun(
        id=uuid.uuid4(),
        user_id=owner.id,
        query="Python intern",
        requested_sources=[],
        requested_skills=[],
        status="completed",
    )
    db_session.add(run)
    db_session.commit()
    assert opportunities.get_discovery(run.id, owner, db_session).id == run.id
    with pytest.raises(HTTPException) as denied:
        opportunities.get_discovery(run.id, other, db_session)
    assert denied.value.status_code == 404
    page = opportunities.get_discovery_results(run.id, owner, db_session, limit=1, offset=0)
    assert (page.total, page.limit, page.offset, page.items) == (0, 1, 0, [])
    with pytest.raises(HTTPException):
        opportunities.get_discovery_results(run.id, other, db_session, limit=1, offset=0)


def test_saved_opportunities_are_scoped_and_paged(db_session):
    owner = new_user(db_session, "saved-owner")
    other = new_user(db_session, "saved-other")
    opportunity = OpportunityDetail(
        id=uuid.uuid4(),
        title="Python Developer Intern",
        source_url="https://jobs.lever.co/acme/python-intern",
        canonical_url=f"https://jobs.lever.co/acme/{uuid.uuid4()}",
        status="unknown",
        extraction_status="unextracted",
        required_skills=[],
        preferred_skills=[],
    )
    db_session.add(opportunity)
    db_session.commit()
    saved = opportunities.save_opportunity(
        opportunity.id, owner, db_session, SaveRequest(notes="Review this role")
    )
    assert saved.user_id == owner.id
    owner_page = opportunities.list_saved_opportunities(owner, db_session, limit=1, offset=0)
    other_page = opportunities.list_saved_opportunities(other, db_session, limit=1, offset=0)
    assert owner_page.total == 1
    assert len(owner_page.items) == 1
    assert owner_page.items[0].opportunity.extraction_status == "unextracted"
    assert other_page.items == []
    with pytest.raises(HTTPException) as denied:
        opportunities.unsave_opportunity(opportunity.id, other, db_session)
    assert denied.value.status_code == 404
    assert opportunities.unsave_opportunity(opportunity.id, owner, db_session).status_code == 204
    detail = opportunities.get_opportunity(opportunity.id, owner, db_session)
    assert OpportunityResponse.model_validate(detail).is_verified is False
