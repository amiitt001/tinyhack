"""Additive discovery tables; shared listings are separate from user-owned runs/saves."""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.entities import TimestampMixin


class DiscoveryRun(TimestampMixin, Base):
    __tablename__ = "opportunity_discovery_runs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    request_hash: Mapped[str] = mapped_column(String(64))
    query: Mapped[str] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    employment_type: Mapped[str | None] = mapped_column(String(32))
    experience_level: Mapped[str | None] = mapped_column(String(64))
    skills: Mapped[list] = mapped_column(JSON, default=list)
    requested_sources: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    total_results: Mapped[int] = mapped_column(Integer, default=0)
    accepted_results: Mapped[int] = mapped_column(Integer, default=0)
    rejected_results: Mapped[int] = mapped_column(Integer, default=0)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))
    safe_error_message: Mapped[str | None] = mapped_column(String(255))
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_discovery_user_key"),
        CheckConstraint(
            "status IN ('pending','running','completed','partially_completed','failed','cancelled')",
            name="ck_discovery_status",
        ),
        CheckConstraint(
            "total_results >= 0 AND accepted_results >= 0 AND rejected_results >= 0 AND total_results = accepted_results + rejected_results",
            name="ck_discovery_counts",
        ),
        Index("ix_discovery_status_expires", "status", "expires_at"),
    )


class SourceObservation(Base):
    __tablename__ = "opportunity_source_observations"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("opportunities.id", ondelete="RESTRICT"), index=True
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("opportunity_sources.id", ondelete="RESTRICT")
    )
    discovery_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("opportunity_discovery_runs.id", ondelete="CASCADE"), index=True
    )
    source_external_id: Mapped[str | None] = mapped_column(String(255))
    original_url: Mapped[str | None] = mapped_column(String(2048))
    canonical_url: Mapped[str | None] = mapped_column(String(2048))
    provider_request_id: Mapped[str | None] = mapped_column(String(128))
    raw_payload: Mapped[dict] = mapped_column(JSON)
    content_hash: Mapped[str] = mapped_column(String(64))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    validation_status: Mapped[str] = mapped_column(String(32))
    extraction_error: Mapped[str | None] = mapped_column(String(64))
    __table_args__ = (
        UniqueConstraint(
            "discovery_run_id", "source_id", "content_hash", name="uq_observation_run_source_hash"
        ),
        CheckConstraint(
            "validation_status IN ('accepted','rejected')", name="ck_observation_validation"
        ),
        Index("ix_observation_external", "source_id", "source_external_id"),
    )


class SavedOpportunity(Base):
    __tablename__ = "saved_opportunities"
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class OpportunityIdentity(Base):
    """Unique aliases keep dedup stable across URL changes and multiple source records."""

    __tablename__ = "opportunity_identities"
    identity_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), index=True
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("opportunity_sources.id", ondelete="RESTRICT")
    )
    source_external_id: Mapped[str | None] = mapped_column(String(255))
    canonical_url: Mapped[str | None] = mapped_column(String(2048))
    __table_args__ = (Index("ix_identity_source_external", "source_id", "source_external_id"),)
