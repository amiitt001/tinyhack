import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.security import AuthenticatedUser
from app.db import get_db
from app.discovery.extraction import extract_opportunity
from app.discovery.sources import OFFICIAL
from app.integrations.tinyfish import TinyFishAdapter
from app.main import app
from app.models import (
    DiscoveryRun,
    Opportunity,
    SavedOpportunity,
    SourceObservation,
)
from app.repositories.discovery import DiscoveryRepository, serialized_write
from app.schemas.discovery import DiscoveryRequest
from app.services.discovery import DiscoveryService, execute_discovery


def auth(user_id):
    return {
        "Authorization": "Bearer "
        + jwt.encode(
            {"sub": user_id, "aud": "authenticated", "exp": 4102444800},
            "test-secret",
            algorithm="HS256",
        )
    }


@pytest.fixture
def api(discovery_db, discovery_settings, listing):
    sdk = Mock()
    sdk.__aenter__ = AsyncMock(return_value=sdk)
    sdk.__aexit__ = AsyncMock(return_value=False)
    sdk.search.query = AsyncMock(
        return_value=SimpleNamespace(
            model_dump=lambda: {
                "query": "Python",
                "page": 0,
                "total_results": 2,
                "results": [
                    {
                        "position": 1,
                        "site_name": "canonical.com",
                        "snippet": "Fixture only",
                        "title": "Python intern",
                        "url": "https://canonical.com/careers/123?utm_source=test",
                    },
                    {
                        "position": 2,
                        "site_name": "evil.invalid",
                        "snippet": "Not a listing",
                        "title": "Reject",
                        "url": "https://evil.invalid/jobs/1",
                    },
                ],
            }
        )
    )
    fetcher = Mock()
    fetcher.fetch.return_value = listing()

    def adapter_factory(settings):
        return TinyFishAdapter(
            settings, client_factory=Mock(return_value=sdk), sleep=lambda _: None
        )

    class InlineExecutor:
        def __init__(self):
            self.calls = 0

        def submit(self, run_id):
            self.calls += 1
            execute_discovery(
                run_id, discovery_db, discovery_settings, adapter_factory, lambda: fetcher
            )

    runner = InlineExecutor()

    def override_db():
        with discovery_db() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: discovery_settings
    with TestClient(app) as client:
        app.state.discovery_executor.close()
        app.state.discovery_executor = runner
        yield client, runner, sdk, fetcher
        # Restore a no-op compatible lifecycle close method.
        runner.close = lambda: None
    app.dependency_overrides.clear()


def test_end_to_end_discovery_saved_pagination_and_ownership(api, discovery_db):
    client, runner, sdk, fetcher = api
    user = f"discovery-{uuid.uuid4()}"
    other = f"other-{uuid.uuid4()}"
    headers = {**auth(user), "Idempotency-Key": "workflow-first-key"}
    body = {
        "query": "Python Developer Intern",
        "location": "Delhi NCR",
        "employment_type": "internship",
        "experience_level": "fresher",
        "skills": ["Python", "SQL"],
    }
    response = client.post("/api/v1/opportunity-discoveries", json=body, headers=headers)
    assert response.status_code == 202, response.text
    run_id = response.json()["id"]
    replay = client.post("/api/v1/opportunity-discoveries", json=body, headers=headers)
    assert replay.status_code == 202 and replay.json()["id"] == run_id
    assert runner.calls == 1
    status = client.get(f"/api/v1/opportunity-discoveries/{run_id}", headers=auth(user)).json()
    assert status["status"] == "partially_completed"
    assert (status["total_results"], status["accepted_results"], status["rejected_results"]) == (
        2,
        1,
        1,
    )
    assert sdk.search.query.await_count == 1
    assert fetcher.fetch.call_count == 1  # Unapproved URL never reaches the fetcher.
    results = client.get(
        f"/api/v1/opportunity-discoveries/{run_id}/results?limit=1", headers=auth(user)
    )
    assert results.status_code == 200, results.text
    page = results.json()
    assert page["total"] == 1 and page["limit"] == 1 and not page["has_more"]
    job = page["items"][0]
    assert job["salary_min"] is None and job["deadline"] is None
    assert any("?utm_source=test" in source["original_url"] for source in job["sources"])
    assert "discovery_run_id" not in job["sources"][0]
    assert (
        client.get(f"/api/v1/opportunity-discoveries/{run_id}", headers=auth(other)).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/opportunity-discoveries/{run_id}/results", headers=auth(other)
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/opportunity-discoveries",
            json={**body, "query": "Different job"},
            headers=headers,
        ).status_code
        == 409
    )
    oid = job["id"]
    for _ in range(2):
        assert (
            client.post(f"/api/v1/opportunities/{oid}/save", headers=auth(user)).status_code == 200
        )
    assert client.get("/api/v1/opportunities/saved", headers=auth(user)).json()["total"] == 1
    assert client.get("/api/v1/opportunities/saved", headers=auth(other)).json()["items"] == []
    assert (
        client.delete(f"/api/v1/opportunities/{oid}/save", headers=auth(other)).status_code == 200
    )
    assert client.get("/api/v1/opportunities/saved", headers=auth(user)).json()["total"] == 1
    assert client.delete(f"/api/v1/opportunities/{oid}/save", headers=auth(user)).status_code == 200
    assert client.get(f"/api/v1/opportunities/{oid}", headers=auth(user)).status_code == 200
    with discovery_db() as session:
        assert (
            session.scalar(
                select(func.count())
                .select_from(SourceObservation)
                .where(SourceObservation.discovery_run_id == uuid.UUID(run_id))
            )
            == 2
        )
        rejected = session.scalar(
            select(SourceObservation).where(
                SourceObservation.discovery_run_id == uuid.UUID(run_id),
                SourceObservation.validation_status == "rejected",
            )
        )
        assert rejected.original_url is None
        assert rejected.raw_payload["representation"] == "hash_only"


@pytest.mark.parametrize(
    "body",
    [
        {"query": "x"},
        {"query": "Python", "user_id": "victim"},
        {"query": "https://localhost"},
        {"query": "Python", "sources": ["linkedin_jobs"]},
        {"query": "Python", "sources": ["not-a-source"]},
    ],
)
def test_invalid_requests_and_restricted_sources(api, body):
    client, runner, _, _ = api
    response = client.post(
        "/api/v1/opportunity-discoveries",
        json=body,
        headers={**auth("validation-user"), "Idempotency-Key": "validation-test-key"},
    )
    assert response.status_code == 422
    assert runner.calls == 0


def test_auth_required_and_invalid_opportunity_cannot_be_saved(api):
    client, _, _, _ = api
    assert (
        client.post("/api/v1/opportunity-discoveries", json={"query": "Python"}).status_code == 401
    )
    assert client.get("/api/v1/opportunities/saved").status_code == 401
    assert (
        client.post(
            f"/api/v1/opportunities/{uuid.uuid4()}/save", headers=auth("save-user")
        ).status_code
        == 404
    )
    assert (
        client.get("/api/v1/opportunities/saved?limit=101", headers=auth("save-user")).status_code
        == 422
    )


def test_dedup_preserves_tracking_variants_external_ids_and_distinct_jobs(discovery_db, listing):
    repository = DiscoveryRepository()
    with discovery_db() as session:
        serialized_write(session)
        source = repository.source(session, f"test-source-{uuid.uuid4()}", "canonical.com")
        job_id = str(uuid.uuid4().int)
        base_url = f"https://canonical.com/careers/{job_id}"
        base = extract_opportunity(listing(job_id), base_url, OFFICIAL)
        first = repository.accept(session, source, base_url, base)
        first_id = first.id
        tracked_url = base_url + "?utm_source=other"
        tracked = extract_opportunity(listing(job_id), tracked_url, OFFICIAL)
        assert repository.accept(session, source, tracked_url, tracked).id == first_id
        alternate = {**base, "canonical_url": f"https://canonical.com/careers/{uuid.uuid4().int}"}
        assert (
            repository.accept(session, source, alternate["canonical_url"], alternate).id == first_id
        )
        distinct_id = str(uuid.uuid4().int)
        distinct_url = f"https://canonical.com/careers/{distinct_id}"
        distinct = extract_opportunity(listing(distinct_id), distinct_url, OFFICIAL)
        assert repository.accept(session, source, distinct_url, distinct).id != first_id
        session.commit()


def test_cross_source_fingerprint_merges_but_keeps_observations(
    discovery_db, discovery_settings, listing
):
    user = AuthenticatedUser(f"cross-{uuid.uuid4()}", None, {})
    with discovery_db() as session:
        service = DiscoveryService(discovery_settings)
        run, _ = service.create(session, user, DiscoveryRequest(query="Python"), "cross-source-key")
        repository = DiscoveryRepository()
        serialized_write(session)
        source = repository.source(session, f"cross-a-{uuid.uuid4()}", "canonical.com")
        other = repository.source(session, f"cross-b-{uuid.uuid4()}", "canonical.com")
        data = extract_opportunity(listing(), "https://canonical.com/careers/123", OFFICIAL)
        data["canonical_url"] = f"https://canonical.com/careers/{uuid.uuid4().int}"
        # Unique test fingerprint isolates this case from existing shared listings.
        data["fingerprint"] = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()
        first = repository.accept(session, source, data["canonical_url"], data)
        repository.observe(
            session,
            run,
            source,
            original_url=data["canonical_url"],
            data=data,
            error=None,
            payload_hash=data["content_hash"],
            opportunity=first,
        )
        next_data = {
            **data,
            "canonical_url": f"https://canonical.com/careers/{uuid.uuid4().int}",
            "source_external_id": "other-id",
        }
        second = repository.accept(session, other, next_data["canonical_url"], next_data)
        assert first.id == second.id
        repository.observe(
            session,
            run,
            other,
            original_url=next_data["canonical_url"],
            data=next_data,
            error=None,
            payload_hash=next_data["content_hash"],
            opportunity=second,
        )
        session.commit()
        assert len(repository.details(session, first.id).sources) >= 2


def test_transaction_failure_rolls_back_listing_and_persists_failure(
    discovery_db, discovery_settings, listing, monkeypatch
):
    user = AuthenticatedUser(f"rollback-{uuid.uuid4()}", None, {})
    with discovery_db() as session:
        run, _ = DiscoveryService(discovery_settings).create(
            session, user, DiscoveryRequest(query="Python"), "rollback-test-key"
        )
        run_id = run.id
    candidate = SimpleNamespace(url=f"https://canonical.com/careers/{uuid.uuid4().int}")
    fake = SimpleNamespace(attempt_count=1, search=lambda *a, **kw: [candidate])
    page = listing(candidate.url.split("/")[-1])

    def reject(*args, **kwargs):
        raise RuntimeError("SECRET_SENTINEL")

    monkeypatch.setattr(DiscoveryRepository, "observe", reject)
    execute_discovery(
        run_id,
        discovery_db,
        discovery_settings,
        lambda _: fake,
        lambda: SimpleNamespace(fetch=lambda *a: page),
    )
    with discovery_db() as session:
        run = session.get(DiscoveryRun, run_id)
        assert run.status == "failed" and run.error_code == "internal_failure"
        assert "SECRET_SENTINEL" not in run.safe_error_message
        assert (
            session.scalar(select(Opportunity).where(Opportunity.canonical_url == candidate.url))
            is None
        )


def test_foreign_keys_and_saved_unique_association(discovery_db):
    with discovery_db() as session:
        session.add(
            SavedOpportunity(
                user_id="nonexistent", opportunity_id=uuid.uuid4(), created_at=datetime.now(UTC)
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_expired_execution_lease_fails_safely(discovery_db, discovery_settings):
    with discovery_db() as session:
        user = AuthenticatedUser(f"expired-{uuid.uuid4()}", None, {})
        service = DiscoveryService(discovery_settings)
        run, _ = service.create(session, user, DiscoveryRequest(query="Python"), "expired-test-key")
        run.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        session.commit()
        assert service.owned_run(session, user.id, run.id).error_code == "execution_abandoned"


def test_schema_and_indexes_match_migration(migrated_postgres):
    inspector = inspect(migrated_postgres)
    assert {
        "opportunity_discovery_runs",
        "opportunity_source_observations",
        "saved_opportunities",
    } <= set(inspector.get_table_names())
    assert "ix_opportunities_fingerprint" in {
        i["name"] for i in inspector.get_indexes("opportunities")
    }
    assert "uq_discovery_user_key" in {
        i["name"] for i in inspector.get_unique_constraints("opportunity_discovery_runs")
    }
    assert "ck_discovery_status" in {
        i["name"] for i in inspector.get_check_constraints("opportunity_discovery_runs")
    }


def test_failed_reverification_records_attempt_without_asserting_freshness(
    discovery_db, discovery_settings, listing
):
    user = AuthenticatedUser(f"reverify-{uuid.uuid4()}", None, {})
    with discovery_db() as session:
        run, _ = DiscoveryService(discovery_settings).create(
            session, user, DiscoveryRequest(query="Python"), "reverification-key"
        )
        repo = DiscoveryRepository()
        serialized_write(session)
        source = repo.source(session, f"reverify-source-{uuid.uuid4()}", "canonical.com")
        job_id = str(uuid.uuid4().int)
        url = f"https://canonical.com/careers/{job_id}"
        data = extract_opportunity(listing(job_id), url, OFFICIAL)
        job = repo.accept(session, source, url, data)
        job_id = job.id
        previous = datetime.now(UTC) - timedelta(days=1)
        job.last_verified_at = previous
        session.commit()
        repo.observe(
            session,
            run,
            source,
            original_url=url,
            data=None,
            error="source_fetch_failed",
            payload_hash=hashlib.sha256(url.encode()).hexdigest(),
            opportunity=None,
            canonical_url=url,
        )
        session.commit()
        session.refresh(job)
        assert job.last_verified_at.replace(tzinfo=UTC) == previous
        assert job.last_attempted_at.replace(tzinfo=UTC) > previous
        assert run.accepted_results == 0 and run.rejected_results == 1
        assert repo.details(session, job_id).status == "validated"
