"""Repository layer for opportunity discovery persistence.

All database operations are centralised here. Route handlers and services
must not execute raw SQL or SQLAlchemy queries directly.

Conventions
-----------
* All methods receive a ``Session`` as the first argument (injected by FastAPI).
* User isolation is enforced at the repository level as a defence-in-depth
  measure in addition to service-layer checks.
* Shared ``OpportunityDetail`` records are never duplicated per-user;
  ``SavedOpportunity`` handles the user-scoped association.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.integrations.extraction import NormalisedOpportunity
from app.models.entities import OpportunitySource
from app.models.opportunity import (
    DiscoveryRun,
    OpportunityDetail,
    OpportunitySourceObservation,
    SavedOpportunity,
)


class DiscoveryRunRepository:
    """CRUD operations for DiscoveryRun records."""

    def create(
        self,
        session: Session,
        *,
        user_id: str,
        query: str,
        location: str | None = None,
        employment_type: str | None = None,
        experience_level: str | None = None,
        requested_sources: list[str] | None = None,
        requested_skills: list[str] | None = None,
        idempotency_key: str | None = None,
        refresh_requested: bool = False,
    ) -> DiscoveryRun:
        """Create and persist a new discovery run in 'pending' status."""
        run = DiscoveryRun(
            id=uuid.uuid4(),
            user_id=user_id,
            idempotency_key=idempotency_key,
            refresh_requested=refresh_requested,
            query=query,
            location=location,
            employment_type=employment_type,
            experience_level=experience_level,
            requested_sources=requested_sources or [],
            requested_skills=requested_skills or [],
            status="pending",
        )
        session.add(run)
        session.flush()
        return run

    def find_by_idempotency_key(
        self, session: Session, *, user_id: str, idempotency_key: str
    ) -> DiscoveryRun | None:
        """Find an existing run by idempotency key for a given user."""
        return session.scalar(
            select(DiscoveryRun).where(
                DiscoveryRun.user_id == user_id,
                DiscoveryRun.idempotency_key == idempotency_key,
            )
        )

    def get_for_user(
        self, session: Session, *, run_id: uuid.UUID, user_id: str
    ) -> DiscoveryRun | None:
        """Fetch a run by ID scoped to the authenticated user."""
        return session.scalar(
            select(DiscoveryRun).where(
                DiscoveryRun.id == run_id,
                DiscoveryRun.user_id == user_id,
            )
        )

    def get(self, session: Session, run_id: uuid.UUID) -> DiscoveryRun | None:
        return session.get(DiscoveryRun, run_id)

    def mark_running(self, session: Session, run: DiscoveryRun) -> None:
        run.status = "running"
        run.started_at = datetime.now(UTC)
        session.flush()

    def claim_pending(self, session: Session, run_id: uuid.UUID) -> bool:
        result = session.execute(
            update(DiscoveryRun)
            .where(DiscoveryRun.id == run_id, DiscoveryRun.status == "pending")
            .values(status="running", started_at=datetime.now(UTC))
        )
        return result.rowcount == 1

    def mark_completed(
        self,
        session: Session,
        run: DiscoveryRun,
        *,
        total_results: int,
        accepted_results: int,
        rejected_results: int,
        partial: bool = False,
    ) -> None:
        run.status = "partially_completed" if partial else "completed"
        run.completed_at = datetime.now(UTC)
        run.total_results = total_results
        run.accepted_results = accepted_results
        run.rejected_results = rejected_results
        session.flush()

    def mark_failed(
        self,
        session: Session,
        run: DiscoveryRun,
        *,
        error_code: str,
        safe_error_message: str,
    ) -> None:
        run.status = "failed"
        run.completed_at = datetime.now(UTC)
        run.error_code = error_code
        run.safe_error_message = safe_error_message
        session.flush()


class OpportunityDetailRepository:
    """CRUD and deduplication for OpportunityDetail records."""

    def find_by_canonical_url(
        self, session: Session, canonical_url: str
    ) -> OpportunityDetail | None:
        return session.scalar(
            select(OpportunityDetail).where(OpportunityDetail.canonical_url == canonical_url)
        )

    def find_by_content_hash(self, session: Session, content_hash: str) -> OpportunityDetail | None:
        return session.scalar(
            select(OpportunityDetail).where(OpportunityDetail.content_hash == content_hash).limit(1)
        )

    def get_by_id(self, session: Session, opportunity_id: uuid.UUID) -> OpportunityDetail | None:
        return session.scalar(
            select(OpportunityDetail).where(OpportunityDetail.id == opportunity_id)
        )

    def upsert(
        self,
        session: Session,
        opportunity: NormalisedOpportunity,
        source_id: uuid.UUID | None = None,
    ) -> tuple[OpportunityDetail, bool]:
        """Insert or return existing opportunity by canonical URL.

        Returns:
            (detail, created) where created=True if a new record was inserted.
        """
        existing: OpportunityDetail | None = None

        # Primary deduplication: canonical URL.
        if opportunity.canonical_url:
            existing = self.find_by_canonical_url(session, opportunity.canonical_url)

        # Secondary deduplication: content hash.
        if existing is None and opportunity.content_hash:
            existing = self.find_by_content_hash(session, opportunity.content_hash)

        if existing is not None:
            existing.last_attempted_at = datetime.now(UTC)
            if opportunity.extraction_status == "extracted":
                # Agent-backed evidence may enrich an earlier Search candidate
                # with the same canonical URL. Preserve useful existing values
                # when the new extraction did not provide them.
                for name in (
                    "title",
                    "company_name",
                    "description",
                    "location",
                    "work_mode",
                    "employment_type",
                    "experience_requirement",
                    "salary_min",
                    "salary_max",
                    "salary_currency",
                    "stipend",
                    "application_url",
                ):
                    value = getattr(opportunity, name)
                    if value is not None:
                        setattr(existing, name, value)
                if opportunity.required_skills:
                    existing.required_skills = opportunity.required_skills
                if opportunity.preferred_skills:
                    existing.preferred_skills = opportunity.preferred_skills
                existing.extraction_status = "extracted"
                existing.content_hash = opportunity.content_hash or existing.content_hash
                existing.source_id = source_id or existing.source_id
            session.flush()
            return existing, False

        detail = OpportunityDetail(
            id=uuid.uuid4(),
            title=opportunity.title,
            company_name=opportunity.company_name,
            description=opportunity.description,
            location=opportunity.location,
            work_mode=opportunity.work_mode,
            employment_type=opportunity.employment_type,
            experience_requirement=opportunity.experience_requirement,
            required_skills=opportunity.required_skills or [],
            preferred_skills=opportunity.preferred_skills or [],
            salary_min=opportunity.salary_min,
            salary_max=opportunity.salary_max,
            salary_currency=opportunity.salary_currency,
            stipend=opportunity.stipend,
            application_url=opportunity.application_url,
            canonical_url=opportunity.canonical_url,
            source_url=opportunity.source_url,
            source_id=source_id,
            source_external_id=None,
            deadline=opportunity.deadline if hasattr(opportunity, "deadline") else None,
            discovered_at=opportunity.discovered_at,
            last_attempted_at=datetime.now(UTC),
            status="unknown",
            extraction_status=opportunity.extraction_status,
            content_hash=opportunity.content_hash or None,
        )
        try:
            with session.begin_nested():
                session.add(detail)
                session.flush()
        except IntegrityError:
            # Race condition: another request inserted the same canonical URL.
            existing = self.find_by_canonical_url(session, opportunity.canonical_url)
            if existing is not None:
                return existing, False
            raise
        return detail, True

    def list_for_run(
        self,
        session: Session,
        *,
        run_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[OpportunityDetail]:
        """Return opportunities associated with a specific discovery run."""
        opportunity_ids = (
            select(OpportunitySourceObservation.opportunity_detail_id.label("opportunity_detail_id"))
            .where(OpportunitySourceObservation.discovery_run_id == run_id)
            .group_by(OpportunitySourceObservation.opportunity_detail_id)
            .subquery()
        )
        return list(
            session.scalars(
                select(OpportunityDetail)
                .join(opportunity_ids, opportunity_ids.c.opportunity_detail_id == OpportunityDetail.id)
                .order_by(OpportunityDetail.discovered_at.desc())
                .offset(offset)
                .limit(limit)
            )
        )

    def count_for_run(self, session: Session, *, run_id: uuid.UUID) -> int:
        from sqlalchemy import func

        row = session.execute(
            select(func.count(func.distinct(OpportunityDetail.id)))
            .select_from(OpportunityDetail)
            .join(
                OpportunitySourceObservation,
                OpportunitySourceObservation.opportunity_detail_id == OpportunityDetail.id,
            )
            .where(OpportunitySourceObservation.discovery_run_id == run_id)
        ).scalar()
        return row or 0

    def list_for_run_page(
        self,
        session: Session,
        *,
        run_id: uuid.UUID,
        limit: int,
        offset: int,
    ) -> list[OpportunityDetail]:
        opportunity_ids = (
            select(OpportunitySourceObservation.opportunity_detail_id.label("opportunity_detail_id"))
            .where(
                OpportunitySourceObservation.discovery_run_id == run_id,
                OpportunitySourceObservation.validation_status == "accepted",
            )
            .group_by(OpportunitySourceObservation.opportunity_detail_id)
            .subquery()
        )
        return list(
            session.scalars(
                select(OpportunityDetail)
                .join(opportunity_ids, opportunity_ids.c.opportunity_detail_id == OpportunityDetail.id)
                .order_by(OpportunityDetail.discovered_at.desc())
                .offset(offset)
                .limit(limit)
            )
        )


class OpportunitySourceRepository:
    """Resolve source provenance rows, creating them safely when absent."""

    def get_or_create(
        self, session: Session, *, key: str, base_url: str | None = None
    ) -> OpportunitySource:
        source = session.scalar(select(OpportunitySource).where(OpportunitySource.name == key))
        if source is not None:
            return source
        source = OpportunitySource(id=uuid.uuid4(), name=key, base_url=base_url)
        try:
            with session.begin_nested():
                session.add(source)
                session.flush()
        except IntegrityError:
            source = session.scalar(select(OpportunitySource).where(OpportunitySource.name == key))
            if source is None:
                raise
        return source


class SourceObservationRepository:
    """Persistence for OpportunitySourceObservation records."""

    def create(
        self,
        session: Session,
        *,
        discovery_run_id: uuid.UUID,
        opportunity_detail_id: uuid.UUID | None,
        source_id: uuid.UUID | None,
        original_url: str,
        canonical_url: str | None,
        raw_payload: dict | None,
        content_hash: str | None,
        validation_status: str,
        extraction_error: str | None = None,
    ) -> OpportunitySourceObservation:
        obs = OpportunitySourceObservation(
            id=uuid.uuid4(),
            discovery_run_id=discovery_run_id,
            opportunity_detail_id=opportunity_detail_id,
            source_id=source_id,
            original_url=original_url,
            canonical_url=canonical_url,
            raw_payload=raw_payload,
            content_hash=content_hash,
            validation_status=validation_status,
            extraction_error=extraction_error,
        )
        session.add(obs)
        session.flush()
        return obs


class SavedOpportunityRepository:
    """User-scoped saved opportunity management."""

    def save(
        self,
        session: Session,
        *,
        user_id: str,
        opportunity_detail_id: uuid.UUID,
        notes: str | None = None,
    ) -> SavedOpportunity:
        """Save an opportunity for a user; idempotent on duplicate."""
        existing = session.scalar(
            select(SavedOpportunity).where(
                SavedOpportunity.user_id == user_id,
                SavedOpportunity.opportunity_detail_id == opportunity_detail_id,
            )
        )
        if existing:
            return existing

        saved = SavedOpportunity(
            id=uuid.uuid4(),
            user_id=user_id,
            opportunity_detail_id=opportunity_detail_id,
            notes=notes,
        )
        session.add(saved)
        try:
            session.flush()
        except IntegrityError:
            session.rollback()
            existing = session.scalar(
                select(SavedOpportunity).where(
                    SavedOpportunity.user_id == user_id,
                    SavedOpportunity.opportunity_detail_id == opportunity_detail_id,
                )
            )
            if existing:
                return existing
            raise
        return saved

    def unsave(
        self,
        session: Session,
        *,
        user_id: str,
        opportunity_detail_id: uuid.UUID,
    ) -> bool:
        """Remove a saved opportunity; returns True if deleted, False if not found."""
        saved = session.scalar(
            select(SavedOpportunity).where(
                SavedOpportunity.user_id == user_id,
                SavedOpportunity.opportunity_detail_id == opportunity_detail_id,
            )
        )
        if not saved:
            return False
        session.delete(saved)
        session.flush()
        return True

    def list_saved(
        self,
        session: Session,
        *,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[SavedOpportunity]:
        return list(
            session.scalars(
                select(SavedOpportunity)
                .where(SavedOpportunity.user_id == user_id)
                .order_by(SavedOpportunity.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        )

    def count_saved(self, session: Session, *, user_id: str) -> int:
        from sqlalchemy import func

        return (
            session.execute(
                select(func.count())
                .select_from(SavedOpportunity)
                .where(SavedOpportunity.user_id == user_id)
            ).scalar()
            or 0
        )

    def is_saved(
        self,
        session: Session,
        *,
        user_id: str,
        opportunity_detail_id: uuid.UUID,
    ) -> bool:
        return (
            session.scalar(
                select(SavedOpportunity).where(
                    SavedOpportunity.user_id == user_id,
                    SavedOpportunity.opportunity_detail_id == opportunity_detail_id,
                )
            )
            is not None
        )
