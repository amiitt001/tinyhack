import asyncio
import threading
import time
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from sqlalchemy import func, select
from tinyfish import BadRequestError

from app.core.security import AuthenticatedUser
from app.discovery.errors import DiscoveryError
from app.discovery.execution import DiscoveryExecutor
from app.integrations.tinyfish import TinyFishAdapter, TinyFishProviderError, TinyFishTimeoutError
from app.models import DiscoveryRun, SourceObservation
from app.schemas.discovery import DiscoveryRequest
from app.services.discovery import DiscoveryService, execute_discovery


def test_executor_enforces_capacity_and_shutdown(discovery_settings, monkeypatch):
    entered = threading.Event()
    release = threading.Event()

    def block(*args):
        entered.set()
        release.wait(timeout=3)

    failed = Mock()
    monkeypatch.setattr("app.discovery.execution.execute_discovery", block)
    monkeypatch.setattr("app.discovery.execution.fail_run", failed)
    discovery_settings.discovery_workers = 1
    discovery_settings.discovery_queue_size = 0
    executor = DiscoveryExecutor(discovery_settings)
    executor.submit(uuid.uuid4())
    assert entered.wait(timeout=1)
    with pytest.raises(DiscoveryError, match="capacity"):
        executor.submit(uuid.uuid4())
    assert failed.call_count == 1
    release.set()
    executor.close()
    executor.pool.shutdown(wait=True)
    with pytest.raises(DiscoveryError):
        executor.submit(uuid.uuid4())


def test_provider_has_wall_clock_timeout_not_only_idle_timeout(discovery_settings):
    client = Mock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    cancelled = []

    async def slow(*args, **kwargs):
        try:
            await asyncio.sleep(5)
        finally:
            cancelled.append(True)

    client.search.query = slow
    adapter = TinyFishAdapter(discovery_settings, client_factory=Mock(return_value=client))
    started = time.monotonic()
    with pytest.raises(TinyFishTimeoutError):
        adapter.search("Python", deadline=started + 0.03)
    assert time.monotonic() - started < 1
    assert cancelled == [True]


def test_malformed_request_is_never_retried(discovery_settings):
    client = Mock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    client.search.query = AsyncMock(
        side_effect=BadRequestError("SECRET", response=httpx.Response(400))
    )
    adapter = TinyFishAdapter(discovery_settings, client_factory=Mock(return_value=client))
    with pytest.raises(TinyFishProviderError):
        adapter.search("Python")
    assert adapter.attempt_count == 1


def test_duplicate_worker_claim_does_not_repeat_provider(discovery_db, discovery_settings):
    user = AuthenticatedUser(f"claim-{uuid.uuid4()}", None, {})
    with discovery_db() as session:
        run, _ = DiscoveryService(discovery_settings).create(
            session, user, DiscoveryRequest(query="Python"), "worker-claim-key"
        )
        run_id = run.id
    provider = SimpleNamespace(attempt_count=1, search=Mock(return_value=[]))
    for _ in range(2):
        execute_discovery(run_id, discovery_db, discovery_settings, lambda _: provider, Mock())
    assert provider.search.call_count == 1
    with discovery_db() as session:
        assert session.get(DiscoveryRun, run_id).status == "completed"


def test_provider_failure_after_committed_results_is_partial(
    discovery_db, discovery_settings, listing
):
    user = AuthenticatedUser(f"partial-{uuid.uuid4()}", None, {})
    with discovery_db() as session:
        run, _ = DiscoveryService(discovery_settings).create(
            session, user, DiscoveryRequest(query="Python"), "partial-results-key"
        )
        run_id = run.id
    candidate = SimpleNamespace(url="https://canonical.com/careers/123")
    provider = SimpleNamespace(
        attempt_count=2, search=Mock(side_effect=[[candidate], TinyFishProviderError()])
    )
    discovery_settings.discovery_search_pages = 2
    execute_discovery(
        run_id,
        discovery_db,
        discovery_settings,
        lambda _: provider,
        lambda: SimpleNamespace(fetch=lambda *a: listing()),
    )
    with discovery_db() as session:
        run = session.get(DiscoveryRun, run_id)
        assert run.status == "partially_completed" and run.error_code == "provider_error"
        assert run.accepted_results == 1
        assert (
            session.scalar(
                select(func.count())
                .select_from(SourceObservation)
                .where(SourceObservation.discovery_run_id == run_id)
            )
            == 1
        )


def test_pending_quota_is_enforced_per_user(discovery_db, discovery_settings):
    user = AuthenticatedUser(f"quota-{uuid.uuid4()}", None, {})
    with discovery_db() as session:
        service = DiscoveryService(discovery_settings)
        for index in range(2):
            service.create(session, user, DiscoveryRequest(query="Python"), f"quota-key-{index}")
        with pytest.raises(DiscoveryError, match="two active"):
            service.create(session, user, DiscoveryRequest(query="Python"), "quota-third-key")


def test_openapi_has_typed_pagination_and_required_idempotency():
    from app.main import app

    schema = app.openapi()
    create = schema["paths"]["/api/v1/opportunity-discoveries"]["post"]
    assert any(p["name"] == "idempotency-key" and p["required"] for p in create["parameters"])
    assert "OpportunityPage" in schema["components"]["schemas"]
    assert "DiscoveryRequest" in schema["components"]["schemas"]
    assert "RunStatus" not in schema["components"]["schemas"]  # Inline literal values are stable.


def test_concurrent_idempotent_creation_on_postgres(migrated_postgres, discovery_settings):
    from concurrent.futures import ThreadPoolExecutor

    from sqlalchemy.orm import sessionmaker

    factory = sessionmaker(bind=migrated_postgres, expire_on_commit=False)
    user = AuthenticatedUser(f"race-{uuid.uuid4()}", None, {})
    barrier = threading.Barrier(2)

    def create():
        barrier.wait(timeout=3)
        with factory() as session:
            run, created = DiscoveryService(discovery_settings).create(
                session, user, DiscoveryRequest(query="Python"), "concurrent-key"
            )
            return run.id, created

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: create(), range(2)))
    assert results[0][0] == results[1][0]
    assert sum(created for _, created in results) == 1
