"""SQLAlchemy models for Milestone 4: Opportunity Discovery Foundation."""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.entities import TimestampMixin

# ---------------------------------------------------------------------------
# Discovery Run
# ---------------------------------------------------------------------------


class DiscoveryRun(TimestampMixin, Base):
    """Persistent record of a single opportunity-discovery execution.

    One run is created per API request. The run transitions through
    explicit statuses: pending → running → completed/partially_completed/failed.
    """

    __tablename__ = "discovery_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Caller-supplied idempotency key to prevent duplicate submissions.
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    query: Mapped[str] = mapped_column(String(512), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    employment_type: Mapped[str | None] = mapped_column(String(64))
    experience_level: Mapped[str | None] = mapped_column(String(64))
    refresh_requested: Mapped[bool] = mapped_column(default=False, nullable=False)
    # Requested source keys stored as JSON array.
    requested_sources: Mapped[list | None] = mapped_column(JSON)
    # requested_skills stored as JSON array of strings.
    requested_skills: Mapped[list | None] = mapped_column(JSON)

    # Status: pending | running | completed | partially_completed | failed | cancelled
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")

    total_results: Mapped[int | None] = mapped_column(Integer)
    accepted_results: Mapped[int | None] = mapped_column(Integer)
    rejected_results: Mapped[int | None] = mapped_column(Integer)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Error information — never expose raw provider errors to callers.
    error_code: Mapped[str | None] = mapped_column(String(64))
    safe_error_message: Mapped[str | None] = mapped_column(Text)

    source_observations: Mapped[list["OpportunitySourceObservation"]] = relationship(
        back_populates="discovery_run",
        cascade="all, delete-orphan",
    )
    tinyfish_executions: Mapped[list["TinyFishExecution"]] = relationship(
        back_populates="discovery_run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_discovery_run_idempotency"),
        Index("ix_discovery_runs_user_status", "user_id", "status"),
    )


# ---------------------------------------------------------------------------
# Extended Opportunity (adds richly-typed fields to existing slim model)
# ---------------------------------------------------------------------------


class OpportunityDetail(TimestampMixin, Base):
    """Rich normalised opportunity data linked to the base Opportunity.

    The base ``opportunities`` table is preserved unchanged to avoid data loss.
    This table extends it with the full field set required for Milestone 4.
    """

    __tablename__ = "opportunity_details"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Link to existing Opportunity row — 1-to-1; nullable to allow standalone use.
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("opportunities.id", ondelete="SET NULL"), unique=True, nullable=True
    )

    # Core identity
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)

    # Location / mode
    location: Mapped[str | None] = mapped_column(String(512))
    work_mode: Mapped[str | None] = mapped_column(String(64))  # remote|hybrid|onsite|unknown

    # Employment characteristics
    employment_type: Mapped[str | None] = mapped_column(
        String(64)
    )  # fulltime|parttime|internship|contract
    experience_requirement: Mapped[str | None] = mapped_column(String(128))

    # Skills — stored as JSON arrays of strings.
    required_skills: Mapped[list | None] = mapped_column(JSON)
    preferred_skills: Mapped[list | None] = mapped_column(JSON)

    # Compensation
    salary_min: Mapped[float | None] = mapped_column(Numeric(14, 2))
    salary_max: Mapped[float | None] = mapped_column(Numeric(14, 2))
    salary_currency: Mapped[str | None] = mapped_column(String(8))
    stipend: Mapped[str | None] = mapped_column(String(255))

    # URLs
    application_url: Mapped[str | None] = mapped_column(String(2048))
    canonical_url: Mapped[str | None] = mapped_column(String(2048))
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)

    # Source tracking
    source_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("opportunity_sources.id"))
    source_external_id: Mapped[str | None] = mapped_column(String(512))

    # Lifecycle timestamps
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Status / extraction state
    # active | expired | removed | unknown
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    # unextracted | extracted | failed | unsupported
    extraction_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unextracted"
    )

    # Deterministic fingerprint for deduplication.
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)

    # Relationships
    source_observations: Mapped[list["OpportunitySourceObservation"]] = relationship(
        back_populates="opportunity_detail",
    )
    saved_by: Mapped[list["SavedOpportunity"]] = relationship(
        back_populates="opportunity_detail",
        cascade="all, delete-orphan",
    )
    evidence: Mapped[list["OpportunityEvidence"]] = relationship(
        back_populates="opportunity_detail", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("canonical_url", name="uq_opportunity_detail_canonical_url"),
        Index("ix_opportunity_detail_company", "company_name"),
        Index("ix_opportunity_detail_employment_type", "employment_type"),
        Index("ix_opportunity_detail_status", "status"),
    )


# ---------------------------------------------------------------------------
# Source Observation — one record per discovery-run × result
# ---------------------------------------------------------------------------


class OpportunitySourceObservation(Base):
    """Records each time a specific source returns a result for an opportunity.

    Multiple observations may point to the same ``OpportunityDetail``.
    Raw payloads are stored in bounded form and never contain credentials.
    """

    __tablename__ = "opportunity_source_observations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    opportunity_detail_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("opportunity_details.id", ondelete="SET NULL"), nullable=True
    )
    discovery_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("discovery_runs.id", ondelete="CASCADE"), nullable=False
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("opportunity_sources.id"), nullable=True
    )

    original_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    canonical_url: Mapped[str | None] = mapped_column(String(2048))

    # Provider-supplied request/result identifier, if any.
    provider_request_id: Mapped[str | None] = mapped_column(String(255))

    # Bounded raw payload (title + snippet from search result — never full HTML).
    # Max payload stored: 8 KB (enforced in service layer).
    raw_payload: Mapped[dict | None] = mapped_column(JSON)

    # Deduplication fingerprint of the original URL.
    content_hash: Mapped[str | None] = mapped_column(String(64))

    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # accepted | rejected_validation | rejected_domain | rejected_url | error
    validation_status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending")
    extraction_error: Mapped[str | None] = mapped_column(Text)

    # Relationships
    opportunity_detail: Mapped["OpportunityDetail | None"] = relationship(
        back_populates="source_observations"
    )
    discovery_run: Mapped["DiscoveryRun"] = relationship(back_populates="source_observations")

    __table_args__ = (
        Index("ix_source_observations_opportunity_detail_id", "opportunity_detail_id"),
        Index("ix_source_observations_discovery_run_id", "discovery_run_id"),
    )


# ---------------------------------------------------------------------------
# Saved Opportunity — user-scoped association
# ---------------------------------------------------------------------------


class SavedOpportunity(TimestampMixin, Base):
    """User's saved copy of an opportunity.

    The shared ``OpportunityDetail`` is never duplicated; only the association
    is user-scoped.  Notes and status are per-user.
    """

    __tablename__ = "saved_opportunities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    opportunity_detail_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("opportunity_details.id", ondelete="CASCADE"), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)

    opportunity_detail: Mapped["OpportunityDetail"] = relationship(back_populates="saved_by")

    __table_args__ = (
        UniqueConstraint(
            "user_id", "opportunity_detail_id", name="uq_saved_opportunity_user_detail"
        ),
        Index("ix_saved_opportunities_user_id", "user_id"),
    )


class TinyFishExecution(Base):
    """Safe Agent execution record; raw provider payloads and secrets are excluded."""

    __tablename__ = "tinyfish_executions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    discovery_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("discovery_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    provider_run_id: Mapped[str | None] = mapped_column(String(255))
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default="agent")
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    steps: Mapped[int | None] = mapped_column(Integer)
    jobs_returned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    safe_error_code: Mapped[str | None] = mapped_column(String(64))
    result_json: Mapped[dict | None] = mapped_column(JSON)

    discovery_run: Mapped["DiscoveryRun"] = relationship(back_populates="tinyfish_executions")


class OpportunityEvidence(Base):
    """Field-level verbatim evidence returned by the Agent, URL validated."""

    __tablename__ = "opportunity_evidence"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    opportunity_detail_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("opportunity_details.id", ondelete="CASCADE"), nullable=False, index=True
    )
    execution_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tinyfish_executions.id", ondelete="SET NULL"), nullable=True
    )
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    field_value: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(String(16), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    opportunity_detail: Mapped["OpportunityDetail"] = relationship(back_populates="evidence")
