import hashlib
import logging
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import ConfigurationError
from app.core.security import AuthenticatedUser
from app.discovery.errors import DiscoveryError
from app.discovery.extraction import extract_opportunity
from app.discovery.security import DetailFetcher, validate_url
from app.discovery.sources import require_sources
from app.integrations.tinyfish import TinyFishAdapter, TinyFishProviderError
from app.models import DiscoveryRun
from app.repositories.discovery import DiscoveryRepository, ensure_user, serialized_write
from app.schemas.discovery import DiscoveryRequest

logger = logging.getLogger(__name__)
TERMINAL = {"completed", "partially_completed", "failed", "cancelled"}


class DiscoveryService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.repository = DiscoveryRepository()

    def create(
        self, session: Session, user: AuthenticatedUser, request: DiscoveryRequest, key: str
    ) -> tuple[DiscoveryRun, bool]:
        request_hash = hashlib.sha256(request.model_dump_json().encode()).hexdigest()
        serialized_write(session)
        existing = session.scalar(
            select(DiscoveryRun).where(
                DiscoveryRun.user_id == user.id, DiscoveryRun.idempotency_key == key
            )
        )
        if existing is not None:
            if existing.request_hash != request_hash:
                raise DiscoveryError(
                    "idempotency_conflict", "Idempotency key was used for a different request", 409
                )
            return existing, False
        require_sources(request.sources, self.settings)
        try:
            TinyFishAdapter(self.settings)
        except ConfigurationError:
            raise DiscoveryError(
                "provider_not_configured", "TinyFish configuration is unavailable or invalid", 503
            ) from None
        session.execute(
            update(DiscoveryRun)
            .where(
                DiscoveryRun.user_id == user.id,
                DiscoveryRun.status.in_(["pending", "running"]),
                DiscoveryRun.expires_at < datetime.now(UTC),
            )
            .values(
                status="failed",
                error_code="execution_abandoned",
                safe_error_message="Execution lease expired",
                completed_at=datetime.now(UTC),
            )
        )
        active = (
            session.scalar(
                select(func.count())
                .select_from(DiscoveryRun)
                .where(
                    DiscoveryRun.user_id == user.id, DiscoveryRun.status.in_(["pending", "running"])
                )
            )
            or 0
        )
        if active >= 2:
            raise DiscoveryError("discovery_limit", "At most two active discoveries per user", 429)
        ensure_user(session, user)
        run = DiscoveryRun(
            user_id=user.id,
            idempotency_key=key,
            request_hash=request_hash,
            query=request.query,
            location=request.location,
            employment_type=request.employment_type,
            experience_level=request.experience_level,
            skills=request.skills,
            requested_sources=request.sources,
            status="pending",
            total_results=0,
            accepted_results=0,
            rejected_results=0,
            attempt_count=0,
            expires_at=datetime.now(UTC)
            + timedelta(seconds=self.settings.discovery_timeout_seconds + 10),
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        return run, True

    def owned_run(self, session: Session, user_id: str, run_id: uuid.UUID) -> DiscoveryRun:
        run = self.repository.owned_run(session, user_id, run_id)
        if (
            run.status not in TERMINAL
            and run.expires_at
            and run.expires_at.replace(tzinfo=UTC) < datetime.now(UTC)
        ):
            session.execute(
                update(DiscoveryRun)
                .where(DiscoveryRun.id == run_id, DiscoveryRun.status.in_(["pending", "running"]))
                .values(
                    status="failed",
                    error_code="execution_abandoned",
                    safe_error_message="Execution lease expired; submit a new discovery",
                    completed_at=datetime.now(UTC),
                )
            )
            session.commit()
            session.refresh(run)
        return run


def fail_run(
    factory: Callable[[], Session], run_id: uuid.UUID, code: str, attempts: int = 0
) -> None:
    with factory() as session:
        serialized_write(session)
        run = session.scalar(
            select(DiscoveryRun).where(DiscoveryRun.id == run_id).with_for_update()
        )
        if run and run.status not in TERMINAL:
            run.status = "partially_completed" if run.accepted_results else "failed"
            run.error_code = code
            run.safe_error_message = "Discovery could not complete; see the safe error code"
            run.attempt_count = attempts
            run.completed_at = datetime.now(UTC)
            session.commit()


def execute_discovery(
    run_id: uuid.UUID,
    factory: Callable[[], Session],
    settings: Settings,
    adapter_factory: Callable = TinyFishAdapter,
    fetcher_factory: Callable = DetailFetcher,
) -> None:
    repository = DiscoveryRepository()
    adapter = None
    deadline = time.monotonic() + settings.discovery_timeout_seconds
    try:
        with factory() as session:
            claimed = session.execute(
                update(DiscoveryRun)
                .where(DiscoveryRun.id == run_id, DiscoveryRun.status == "pending")
                .values(
                    status="running",
                    started_at=datetime.now(UTC),
                    expires_at=datetime.now(UTC)
                    + timedelta(seconds=settings.discovery_timeout_seconds + 10),
                )
            )
            session.commit()
            if claimed.rowcount != 1:
                return
            run = session.scalar(
                select(DiscoveryRun).where(DiscoveryRun.id == run_id).with_for_update()
            )
            if run is None:
                return
            policies = require_sources(run.requested_sources, settings)
            query = " ".join(
                part
                for part in [run.query, run.employment_type, run.experience_level, *run.skills]
                if part
            )
            location = run.location
        adapter = adapter_factory(settings)
        fetcher = fetcher_factory()
        processed = 0
        for policy in policies:
            for page in range(settings.discovery_search_pages):
                candidates = adapter.search(
                    query,
                    location=location,
                    domains=policy.allowed_domains,
                    page=page,
                    deadline=deadline,
                )
                if not candidates:
                    break
                for candidate in candidates:
                    if processed >= settings.discovery_max_results:
                        break
                    if time.monotonic() >= deadline:
                        raise DiscoveryError("execution_timeout", "Execution budget exhausted")
                    processed += 1
                    data = None
                    error = None
                    original_url = None
                    candidate_canonical = None
                    payload_hash = hashlib.sha256(candidate.url.encode()).hexdigest()
                    try:
                        candidate_canonical = validate_url(candidate.url, policy)
                        original_url = candidate.url
                        detail = fetcher.fetch(candidate.url, policy, deadline)
                        payload_hash = hashlib.sha256(detail.encode()).hexdigest()
                        data = extract_opportunity(detail, candidate.url, policy)
                    except DiscoveryError as exc:
                        error = exc.code
                    with factory() as session:
                        serialized_write(session)
                        run = session.scalar(
                            select(DiscoveryRun).where(DiscoveryRun.id == run_id).with_for_update()
                        )
                        if run is None or run.status != "running":
                            return
                        source = repository.source(session, policy.name, policy.allowed_domains[0])
                        opportunity = (
                            repository.accept(session, source, original_url, data)
                            if data and original_url
                            else None
                        )
                        repository.observe(
                            session,
                            run,
                            source,
                            original_url=original_url,
                            data=data,
                            error=error,
                            payload_hash=payload_hash,
                            opportunity=opportunity,
                            canonical_url=candidate_canonical,
                        )
                        run.attempt_count = adapter.attempt_count
                        session.commit()
                if processed >= settings.discovery_max_results:
                    break
        with factory() as session:
            serialized_write(session)
            run = session.scalar(
                select(DiscoveryRun).where(DiscoveryRun.id == run_id).with_for_update()
            )
            if run is not None and run.status == "running":
                if run.rejected_results and not run.accepted_results:
                    run.status = "failed"
                    run.error_code = "no_validated_results"
                    run.safe_error_message = "All observed candidates were rejected; source evidence could not be validated"
                else:
                    run.status = "partially_completed" if run.rejected_results else "completed"
                run.attempt_count = adapter.attempt_count
                run.completed_at = datetime.now(UTC)
                session.commit()
        logger.info(
            "discovery_finished run_id=%s attempts=%d",
            run_id,
            adapter.attempt_count,
            extra={"request_id": str(run_id)},
        )
    except (TinyFishProviderError, DiscoveryError, ConfigurationError) as exc:
        code = exc.code if hasattr(exc, "code") else "provider_not_configured"
        fail_run(factory, run_id, code, adapter.attempt_count if adapter else 0)
        logger.warning(
            "discovery_failed run_id=%s code=%s", run_id, code, extra={"request_id": str(run_id)}
        )
    except Exception:
        # Reliability boundary only: never log an untrusted provider body or database parameters.
        fail_run(factory, run_id, "internal_failure", adapter.attempt_count if adapter else 0)
        logger.error(
            "discovery_failed run_id=%s code=internal_failure",
            run_id,
            extra={"request_id": str(run_id)},
        )
