"""Discovery service — orchestrates the full opportunity-discovery workflow.

Execution flow
--------------
1. Validate and resolve requested sources against the source registry.
2. Enforce idempotency: return existing run if idempotency_key matches.
3. Create a persistent DiscoveryRun in 'pending' status.
4. Invoke TinyFish adapter for each enabled source.
5. Extract and validate each result.
6. Persist each accepted opportunity (with deduplication).
7. Record every observation (accepted and rejected) for provenance.
8. Update the run status (completed/partially_completed/failed).

Background execution model (Milestone 4)
-----------------------------------------
FastAPI ``BackgroundTasks`` are used for the discovery execution. This means:
* The HTTP response is returned immediately with run ID and 'pending' status.
* The actual discovery work happens after the response is sent.
* **Limitation**: if the process terminates during a background task, the run
  will remain in 'running' or 'pending' status permanently. There is no
  durable recovery mechanism in this milestone. A future milestone should
  integrate a proper job queue (e.g., ARQ with Redis or Celery) for durable,
  recoverable background execution.
* Concurrent discovery runs per user are not limited in this milestone beyond
  the SDK's inherent timeout. Rate-limiting should be added at the API layer
  in a future milestone.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import (
    TinyFishAuthenticationError,
    TinyFishConnectionError,
    TinyFishError,
    TinyFishPaymentError,
    TinyFishRateLimitError,
    TinyFishTimeoutError,
)
from app.core.security import AuthenticatedUser
from app.integrations.extraction import NormalisedOpportunity, extract_opportunities
from app.integrations.location import map_search_location
from app.integrations.source_registry import SourcePolicy, source_registry
from app.integrations.tinyfish import TinyFishAdapter
from app.integrations.tinyfish_agent import TinyFishAgentAdapter
from app.integrations.tinyfish_schemas import AgentInvestigation
from app.integrations.url_safety import validate_scraped_content, validate_url
from app.models.opportunity import DiscoveryRun, OpportunityEvidence, TinyFishExecution
from app.repositories.opportunity import (
    DiscoveryRunRepository,
    OpportunityDetailRepository,
    OpportunitySourceRepository,
    SavedOpportunityRepository,
    SourceObservationRepository,
)

logger = logging.getLogger(__name__)

_run_repo = DiscoveryRunRepository()
_opp_repo = OpportunityDetailRepository()
_obs_repo = SourceObservationRepository()
_saved_repo = SavedOpportunityRepository()
_source_repo = OpportunitySourceRepository()


def _error_code_from_exception(exc: TinyFishError) -> str:
    return exc.error_code or "unknown_error"


def _safe_message_from_exception(exc: TinyFishError) -> str:
    """Return a safe, non-sensitive error message suitable for storage."""
    if isinstance(exc, TinyFishAuthenticationError):
        return "Provider authentication failed. Check your API key configuration."
    if isinstance(exc, TinyFishPaymentError):
        return "Provider account balance exhausted."
    if isinstance(exc, TinyFishRateLimitError):
        return "Provider rate limit exceeded. Retry after a short delay."
    if isinstance(exc, TinyFishTimeoutError):
        return "Provider request timed out."
    if isinstance(exc, TinyFishConnectionError):
        return "Provider connection failed. Check network connectivity."
    return "An unexpected provider error occurred."


class DiscoveryService:
    """Orchestrates opportunity discovery end-to-end.

    Dependencies (settings) are injected at construction time.
    The SQLAlchemy Session is passed per-call to support request-scoped sessions.
    """

    def __init__(
        self,
        settings: Settings,
        adapter: TinyFishAdapter | None = None,
        agent_adapter: TinyFishAgentAdapter | None = None,
    ) -> None:
        self._adapter = adapter or TinyFishAdapter(settings)
        self._settings = settings
        self._agent = agent_adapter

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_run(
        self,
        session: Session,
        user: AuthenticatedUser,
        *,
        query: str,
        location: str | None = None,
        employment_type: str | None = None,
        experience_level: str | None = None,
        skills: list[str] | None = None,
        requested_sources: list[str] | None = None,
        idempotency_key: str | None = None,
        refresh: bool = False,
    ) -> tuple[DiscoveryRun, bool]:
        """Create a persistent discovery run and return it.

        Idempotency: if a run with the same user+idempotency_key exists,
        return the existing run without creating a duplicate.
        """
        if idempotency_key:
            existing = _run_repo.find_by_idempotency_key(
                session, user_id=user.id, idempotency_key=idempotency_key
            )
            if existing:
                logger.info("Idempotency hit: returning existing run run_id=%s", existing.id)
                session.commit()
                return existing, False

        usable_sources, rejected_sources = source_registry.resolve_requested(requested_sources)
        if rejected_sources:
            logger.info("Rejected requested sources: %s", rejected_sources)

        run = _run_repo.create(
            session,
            user_id=user.id,
            query=query,
            location=location,
            employment_type=employment_type,
            experience_level=experience_level,
            requested_sources=[s.key for s in usable_sources],
            requested_skills=skills or [],
            idempotency_key=idempotency_key,
            refresh_requested=refresh,
        )
        session.commit()

        logger.info(
            "Discovery run created run_id=%s user_id=%s sources=%s",
            run.id,
            user.id,
            [s.key for s in usable_sources],
        )
        return run, True

    def execute_run(self, run_id: uuid.UUID, session: Session) -> None:
        """Execute the discovery workflow for an existing run.

        This method is intended to be called from a background task.
        It manages all status transitions and persistence within transactions.

        The method uses its own database session transactions rather than
        relying on the calling context to avoid mixing request-scoped sessions
        with background-task-scoped execution.
        """
        run = session.get(DiscoveryRun, run_id)
        if run is None:
            logger.error("execute_run: run not found run_id=%s", run_id)
            return

        if not _run_repo.claim_pending(session, run_id):
            session.rollback()
            logger.warning(
                "execute_run: run is not pending or was claimed by another worker run_id=%s",
                run_id,
            )
            return
        session.commit()
        run = session.get(DiscoveryRun, run_id)
        if run is None:
            return

        requested_source_keys: list[str] = run.requested_sources or []  # type: ignore[assignment]
        if not requested_source_keys:
            requested_source_keys = [s.key for s in source_registry.list_enabled()]

        sources: list[SourcePolicy] = []
        for key in requested_source_keys:
            policy = source_registry.get(key)
            if policy and policy.is_usable:
                sources.append(policy)

        if not sources:
            _run_repo.mark_failed(
                session,
                run,
                error_code="no_usable_sources",
                safe_error_message="No usable discovery sources are configured.",
            )
            session.commit()
            return

        total_results = 0
        total_accepted = 0
        total_rejected = 0
        had_fatal_error = False

        for source_policy in sources:
            source = _source_repo.get_or_create(session, key=source_policy.key)
            try:
                location = map_search_location(run.location)
                search_query = _build_search_query(
                    query=run.query,
                    employment_type=run.employment_type,
                    skills=run.requested_skills or [],  # type: ignore[assignment]
                    location_constraint=location.query_constraint,
                )
                response = self._adapter.search(
                    search_query,
                    location=location.provider_country,
                    include_domains=source_policy.domain_include_param(),
                    page=0,
                )
            except TinyFishAuthenticationError as exc:
                logger.error("TinyFish authentication failure run_id=%s: %s", run_id, exc)
                _run_repo.mark_failed(
                    session,
                    run,
                    error_code=_error_code_from_exception(exc),
                    safe_error_message=_safe_message_from_exception(exc),
                )
                session.commit()
                return
            except TinyFishError as exc:
                logger.warning(
                    "TinyFish error source=%s run_id=%s: %s",
                    source_policy.key,
                    run_id,
                    type(exc).__name__,
                )
                had_fatal_error = True
                continue

            total_results += response.total_results
            accepted, rejected_records = extract_opportunities(response.results, source_policy)
            total_rejected += len(rejected_records)

            # Record rejected observations.
            for url, reason in rejected_records:
                _obs_repo.create(
                    session,
                    discovery_run_id=run.id,
                    opportunity_detail_id=None,
                    source_id=source.id,
                    original_url=url,
                    canonical_url=None,
                    raw_payload=None,
                    content_hash=None,
                    validation_status="rejected_validation",
                    extraction_error=reason,
                )

            # Persist accepted opportunities with deduplication.
            for opp in accepted:
                detail, _created = _opp_repo.upsert(session, opp, source_id=source.id)
                _obs_repo.create(
                    session,
                    discovery_run_id=run.id,
                    opportunity_detail_id=detail.id,
                    source_id=source.id,
                    original_url=opp.source_url,
                    canonical_url=opp.canonical_url,
                    raw_payload=opp.raw_payload,
                    content_hash=opp.content_hash,
                    validation_status="accepted",
                )
                total_accepted += 1

            # Agent is a first-class investigation step for approved public career URLs.
            # Search records remain candidates; only validated Agent detail evidence can
            # promote a listing to extracted/active.
            if self._settings.tinyfish_agent_enabled:
                for candidate in accepted[
                    : max(0, min(self._settings.tinyfish_max_companies_per_run, 10))
                ]:
                    try:
                        self._investigate_candidate(session, run, source, source_policy, candidate)
                    except TinyFishError as exc:
                        logger.info(
                            "Agent investigation failed run_id=%s code=%s", run_id, exc.error_code
                        )
                        now = datetime.now(UTC)
                        session.add(
                            TinyFishExecution(
                                discovery_run_id=run.id,
                                source_url=candidate.source_url,
                                provider_run_id=exc.provider_run_id,
                                stage="agent",
                                status="failed",
                                started_at=exc.started_at or now,
                                finished_at=now,
                                duration_ms=exc.duration_ms or 0,
                                jobs_returned=0,
                                safe_error_code=_error_code_from_exception(exc),
                            )
                        )
                        had_fatal_error = True
                    session.commit()

        if total_accepted == 0 and had_fatal_error:
            _run_repo.mark_failed(
                session,
                run,
                error_code="all_sources_failed",
                safe_error_message="All discovery sources failed. Please try again.",
            )
        else:
            _run_repo.mark_completed(
                session,
                run,
                total_results=total_results,
                accepted_results=total_accepted,
                rejected_results=total_rejected,
                partial=had_fatal_error,
            )

        session.commit()
        logger.info(
            "Discovery run complete run_id=%s accepted=%d rejected=%d",
            run_id,
            total_accepted,
            total_rejected,
        )

    def _investigate_candidate(self, session, run, source, policy, candidate) -> None:
        from sqlalchemy import select

        allowed = policy.allowed_domains or None
        if not validate_url(candidate.source_url, allowed_domains=allowed).is_valid:
            return
        cache_cutoff = datetime.now(UTC) - timedelta(
            hours=max(1, self._settings.tinyfish_cache_ttl_hours)
        )
        cached = (
            None
            if run.refresh_requested
            else session.scalar(
                select(TinyFishExecution)
                .where(
                    TinyFishExecution.source_url == candidate.source_url,
                    TinyFishExecution.status == "completed",
                    TinyFishExecution.finished_at >= cache_cutoff,
                )
                .order_by(TinyFishExecution.finished_at.desc())
                .limit(1)
            )
        )
        if cached and cached.result_json:
            result = AgentInvestigation.model_validate(cached.result_json)
            execution = TinyFishExecution(
                discovery_run_id=run.id,
                source_url=candidate.source_url,
                provider_run_id=cached.provider_run_id,
                stage="agent",
                status="cache_hit",
                started_at=cached.started_at,
                finished_at=cached.finished_at,
                duration_ms=0,
                steps=cached.steps,
                jobs_returned=len(result.jobs),
                result_json=cached.result_json,
            )
        else:
            agent = self._agent or TinyFishAgentAdapter(self._settings)
            call = agent.investigate(
                candidate.source_url, max_jobs=self._settings.tinyfish_max_jobs_per_company
            )
            result = call.investigation
            execution = TinyFishExecution(
                discovery_run_id=run.id,
                source_url=candidate.source_url,
                provider_run_id=call.run_id,
                stage="agent",
                status="completed"
                if result.execution_status == "completed"
                else result.execution_status,
                started_at=call.started_at,
                finished_at=call.finished_at,
                duration_ms=call.duration_ms,
                steps=call.num_of_steps,
                jobs_returned=len(result.jobs),
                result_json=result.model_dump(mode="json"),
            )
        session.add(execution)
        session.flush()

        for job in result.jobs[: max(0, min(self._settings.tinyfish_max_jobs_per_company, 15))]:
            job_check = validate_url(job.job_url, allowed_domains=allowed)
            if not job_check.is_valid:
                continue
            safe_evidence = []
            evidence_map: dict[str, str] = {}
            for item in job.evidence:
                checked = validate_url(item.evidence_url, allowed_domains=allowed)
                text_check = validate_scraped_content(item.evidence_text, field_name="evidence")
                value_check = validate_scraped_content(item.value, field_name=item.field)
                if not checked.is_valid or not text_check.is_safe or not value_check.is_safe:
                    continue
                if value_check.sanitised_text.lower() not in text_check.sanitised_text.lower():
                    continue
                safe_evidence.append(item)
                evidence_map[item.field] = value_check.sanitised_text

            title_check = validate_scraped_content(job.title, field_name="title")
            if not title_check.is_safe or not title_check.sanitised_text:
                continue
            if evidence_map.get("title", "").casefold() != title_check.sanitised_text.casefold():
                continue
            canonical = job_check.canonical_url or job.job_url
            application_url = None
            if job.application_url and "application_url" in evidence_map:
                app_check = validate_url(job.application_url, allowed_domains=allowed)
                if app_check.is_valid and evidence_map["application_url"].rstrip(
                    "/"
                ) == job.application_url.rstrip("/"):
                    application_url = app_check.canonical_url

            normalized = NormalisedOpportunity(
                title=title_check.sanitised_text[:512],
                company_name=evidence_map.get("company_name"),
                description=evidence_map.get("description"),
                location=evidence_map.get("location"),
                work_mode=evidence_map.get("remote_status"),
                employment_type=evidence_map.get("employment_type"),
                experience_requirement=evidence_map.get("experience_level"),
                required_skills=[
                    x
                    for x in job.required_skills
                    if any(
                        e.field == "required_skills" and x.lower() in e.value.lower()
                        for e in safe_evidence
                    )
                ],
                preferred_skills=[
                    x
                    for x in job.preferred_skills
                    if any(
                        e.field == "preferred_skills" and x.lower() in e.value.lower()
                        for e in safe_evidence
                    )
                ],
                salary_min=None,
                salary_max=None,
                salary_currency=None,
                stipend=evidence_map.get("salary"),
                application_url=application_url,
                canonical_url=canonical,
                source_url=job.job_url,
                source_attribution=policy.key,
                discovered_at=datetime.now(UTC),
                extraction_status="extracted",
                content_hash=hashlib.sha256(canonical.encode()).hexdigest(),
                raw_payload={
                    "provider_run_id": execution.provider_run_id,
                    "evidence_count": len(safe_evidence),
                },
            )
            detail, _ = _opp_repo.upsert(session, normalized, source_id=source.id)
            if (
                job.listing_status in {"active", "expired", "closed"}
                and "listing_status" in evidence_map
            ):
                detail.status = job.listing_status
            else:
                detail.status = "unknown"
            detail.last_verified_at = datetime.now(UTC) if safe_evidence else None
            for item in safe_evidence:
                session.add(
                    OpportunityEvidence(
                        opportunity_detail_id=detail.id,
                        execution_id=execution.id,
                        field_name=item.field,
                        field_value=evidence_map[item.field],
                        evidence_url=item.evidence_url,
                        evidence_text=item.evidence_text,
                        confidence=item.confidence,
                    )
                )
            _obs_repo.create(
                session,
                discovery_run_id=run.id,
                opportunity_detail_id=detail.id,
                source_id=source.id,
                original_url=job.job_url,
                canonical_url=canonical,
                raw_payload={
                    "agent_run_id": execution.provider_run_id,
                    "evidence_count": len(safe_evidence),
                },
                content_hash=normalized.content_hash,
                validation_status="accepted",
            )


def _build_search_query(
    query: str,
    employment_type: str | None,
    skills: list[str],
    location_constraint: str | None = None,
) -> str:
    """Build a search query string by composing user input and filters.

    The output is bounded and does not include user-controlled URLs or
    raw HTML. Skills are included as keywords up to a safe limit.
    """
    parts = [query.strip()]
    if employment_type:
        parts.append(employment_type)
    if skills:
        # Limit to first 5 skills to keep query manageable.
        parts.extend(skills[:5])
    if location_constraint:
        parts.append(location_constraint)
    # Append a general scope hint.
    parts.append("jobs site:careers")
    return " ".join(parts)[:500]  # hard cap — SDK accepts any string length
