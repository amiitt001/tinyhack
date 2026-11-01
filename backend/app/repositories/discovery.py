import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.core.security import AuthenticatedUser
from app.discovery.errors import DiscoveryError
from app.models import (
    DiscoveryRun,
    Opportunity,
    OpportunityIdentity,
    OpportunitySource,
    SavedOpportunity,
    SourceObservation,
    User,
)
from app.schemas.discovery import ObservationResponse, OpportunityPage, OpportunityResponse


def serialized_write(session: Session) -> None:
    # Low-volume foundation: serialize discovery writes across processes, not just Python threads.
    # Database constraints remain the final guard. SQLite is a single-writer unit-test double.
    if session.get_bind().dialect.name == "postgresql":
        session.execute(text("SET LOCAL statement_timeout = 5000"))
        session.execute(text("SET LOCAL lock_timeout = 5000"))
        session.execute(text("SELECT pg_advisory_xact_lock(731942018)"))


def ensure_user(session: Session, user: AuthenticatedUser) -> None:
    if session.get(User, user.id) is None:
        session.add(User(id=user.id, email=user.email))
        session.flush()


class DiscoveryRepository:
    def owned_run(self, session: Session, user_id: str, run_id: uuid.UUID) -> DiscoveryRun:
        run = session.scalar(
            select(DiscoveryRun).where(DiscoveryRun.id == run_id, DiscoveryRun.user_id == user_id)
        )
        if run is None:
            raise DiscoveryError("not_found", "Discovery run not found", 404)
        return run

    def source(self, session: Session, name: str, domain: str) -> OpportunitySource:
        source = session.scalar(select(OpportunitySource).where(OpportunitySource.name == name))
        if source is None:
            source = OpportunitySource(name=name, base_url=f"https://{domain}")
            session.add(source)
            session.flush()
        return source

    def accept(
        self, session: Session, source: OpportunitySource, original_url: str, data: dict
    ) -> Opportunity:
        identities = {
            hashlib.sha256(f"url:{data['canonical_url']}".encode()).hexdigest(): None,
            hashlib.sha256(
                f"source:{source.id}:{data['source_external_id']}".encode()
            ).hexdigest(): source.id,
        }
        known_ids = select(OpportunityIdentity.opportunity_id).where(
            OpportunityIdentity.identity_key.in_(identities)
        )
        # Observations also preserve complete per-run source attribution.
        observed = select(SourceObservation.opportunity_id).where(
            SourceObservation.validation_status == "accepted",
            or_(
                SourceObservation.canonical_url == data["canonical_url"],
                (SourceObservation.source_id == source.id)
                & (SourceObservation.source_external_id == data["source_external_id"]),
            ),
        )
        existing = session.scalar(
            select(Opportunity).where(
                or_(
                    Opportunity.canonical_url == data["canonical_url"],
                    Opportunity.source_url == original_url,
                    (Opportunity.source_id == source.id)
                    & (Opportunity.source_external_id == data["source_external_id"]),
                    Opportunity.id.in_(observed),
                    Opportunity.id.in_(known_ids),
                )
            )
        )
        if existing is None:
            # Exact business fingerprint only across different sources; distinct same-source IDs stay distinct.
            candidates = list(
                session.scalars(
                    select(Opportunity).where(
                        Opportunity.fingerprint == data["fingerprint"],
                        Opportunity.source_id != source.id,
                        ~Opportunity.id.in_(
                            select(OpportunityIdentity.opportunity_id).where(
                                OpportunityIdentity.source_id == source.id,
                                OpportunityIdentity.source_external_id
                                != data["source_external_id"],
                            )
                        ),
                    )
                )
            )
            existing = candidates[0] if len(candidates) == 1 else None
        now = datetime.now(UTC)
        if existing is None:
            existing = Opportunity(
                source_id=source.id, source_url=original_url, discovered_at=now, **data
            )
            session.add(existing)
        elif existing.source_id == source.id:
            for key, value in data.items():
                setattr(existing, key, value)
        existing.status = "validated"
        existing.extraction_status = "validated"
        existing.verified_at = existing.last_verified_at = existing.last_attempted_at = now
        session.flush()
        for key, source_id in identities.items():
            identity = session.get(OpportunityIdentity, key)
            if identity is None:
                session.add(
                    OpportunityIdentity(
                        identity_key=key,
                        opportunity_id=existing.id,
                        source_id=source_id,
                        source_external_id=data["source_external_id"] if source_id else None,
                        canonical_url=data["canonical_url"] if source_id is None else None,
                    )
                )
            elif identity.opportunity_id != existing.id:
                raise DiscoveryError(
                    "dedup_identity_conflict", "Conflicting listing identities require review"
                )
        session.flush()
        return existing

    def observe(
        self,
        session: Session,
        run: DiscoveryRun,
        source: OpportunitySource,
        *,
        original_url: str | None,
        data: dict | None,
        error: str | None,
        payload_hash: str,
        opportunity: Opportunity | None,
        canonical_url: str | None = None,
    ) -> bool:
        identity = hashlib.sha256(f"{original_url}:{payload_hash}:{error}".encode()).hexdigest()
        duplicate = session.scalar(
            select(SourceObservation.id).where(
                SourceObservation.discovery_run_id == run.id,
                SourceObservation.source_id == source.id,
                SourceObservation.content_hash == identity,
            )
        )
        if duplicate:
            return False
        canonical_url = data["canonical_url"] if data else canonical_url
        attempted = opportunity
        if attempted is None and canonical_url:
            aliases = select(OpportunityIdentity.opportunity_id).where(
                OpportunityIdentity.canonical_url == canonical_url
            )
            attempted = session.scalar(
                select(Opportunity).where(
                    or_(Opportunity.canonical_url == canonical_url, Opportunity.id.in_(aliases))
                )
            )
            if attempted is not None:
                attempted.last_attempted_at = datetime.now(UTC)
        session.add(
            SourceObservation(
                opportunity_id=attempted.id if attempted else None,
                source_id=source.id,
                discovery_run_id=run.id,
                original_url=original_url,
                canonical_url=canonical_url,
                source_external_id=data["source_external_id"] if data else None,
                content_hash=identity,
                observed_at=datetime.now(UTC),
                # Representation, not raw content: no bodies, provider errors, credentials or injected text.
                raw_payload={"sha256": payload_hash, "representation": "hash_only"},
                validation_status="accepted" if opportunity else "rejected",
                extraction_error=error,
            )
        )
        run.total_results += 1
        if opportunity:
            run.accepted_results += 1
        else:
            run.rejected_results += 1
        session.flush()
        return True

    def details(self, session: Session, opportunity_id: uuid.UUID) -> OpportunityResponse:
        opportunity = session.get(Opportunity, opportunity_id)
        if (
            opportunity is None
            or opportunity.status != "validated"
            or opportunity.extraction_status != "validated"
        ):
            raise DiscoveryError("not_found", "Validated opportunity not found", 404)
        result = OpportunityResponse.model_validate(opportunity)
        result.sources = [
            ObservationResponse.model_validate(observation)
            for observation in session.scalars(
                select(SourceObservation)
                .where(
                    SourceObservation.opportunity_id == opportunity.id,
                    SourceObservation.validation_status == "accepted",
                )
                .order_by(SourceObservation.observed_at, SourceObservation.id)
            )
        ]
        return result

    def page(
        self,
        session: Session,
        user_id: str,
        limit: int,
        offset: int,
        run_id: uuid.UUID | None = None,
    ) -> OpportunityPage:
        ids: Select
        if run_id is not None:
            self.owned_run(session, user_id, run_id)
            ids = select(SourceObservation.opportunity_id).where(
                SourceObservation.discovery_run_id == run_id,
                SourceObservation.validation_status == "accepted",
            )
        else:
            ids = select(SavedOpportunity.opportunity_id).where(SavedOpportunity.user_id == user_id)
        query = select(Opportunity.id).where(
            Opportunity.id.in_(ids), Opportunity.status == "validated"
        )
        total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
        page_ids = session.scalars(
            query.order_by(Opportunity.created_at.desc(), Opportunity.id)
            .offset(offset)
            .limit(limit)
        )
        return OpportunityPage(
            items=[self.details(session, oid) for oid in page_ids],
            total=total,
            offset=offset,
            limit=limit,
            has_more=offset + limit < total,
        )

    def save(self, session: Session, user: AuthenticatedUser, opportunity_id: uuid.UUID) -> None:
        serialized_write(session)
        opportunity = self.details(session, opportunity_id)
        if opportunity.expires_at and opportunity.expires_at.replace(tzinfo=UTC) <= datetime.now(
            UTC
        ):
            raise DiscoveryError("listing_expired", "An expired listing cannot be saved", 409)
        ensure_user(session, user)
        if session.get(SavedOpportunity, (user.id, opportunity_id)) is None:
            try:
                with session.begin_nested():
                    session.add(
                        SavedOpportunity(
                            user_id=user.id,
                            opportunity_id=opportunity_id,
                            created_at=datetime.now(UTC),
                        )
                    )
                    session.flush()
            except IntegrityError:
                if session.get(SavedOpportunity, (user.id, opportunity_id)) is None:
                    raise
        session.commit()

    def unsave(self, session: Session, user_id: str, opportunity_id: uuid.UUID) -> None:
        saved = session.get(SavedOpportunity, (user_id, opportunity_id))
        if saved is not None:
            session.delete(saved)
        session.commit()
