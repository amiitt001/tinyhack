"""Add opportunity discovery without changing or dropping historical data."""

import sqlalchemy as sa
from alembic import op

revision = "0005_opportunity_discovery"
down_revision = "0004_career_analysis_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("opportunities", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("opportunities", sa.Column("location", sa.String(length=255), nullable=True))
    op.add_column("opportunities", sa.Column("work_mode", sa.String(length=32), nullable=True))
    op.add_column(
        "opportunities", sa.Column("employment_type", sa.String(length=32), nullable=True)
    )
    op.add_column("opportunities", sa.Column("experience_requirement", sa.Text(), nullable=True))
    op.add_column("opportunities", sa.Column("required_skills", sa.JSON(), nullable=True))
    op.add_column("opportunities", sa.Column("preferred_skills", sa.JSON(), nullable=True))
    op.add_column(
        "opportunities", sa.Column("salary_min", sa.Numeric(precision=14, scale=2), nullable=True)
    )
    op.add_column(
        "opportunities", sa.Column("salary_max", sa.Numeric(precision=14, scale=2), nullable=True)
    )
    op.add_column("opportunities", sa.Column("salary_currency", sa.String(length=3), nullable=True))
    op.add_column("opportunities", sa.Column("salary_unit", sa.String(32), nullable=True))
    op.add_column("opportunities", sa.Column("stipend", sa.String(length=255), nullable=True))
    op.add_column(
        "opportunities", sa.Column("application_url", sa.String(length=2048), nullable=True)
    )
    op.add_column(
        "opportunities", sa.Column("canonical_url", sa.String(length=2048), nullable=True)
    )
    op.add_column(
        "opportunities", sa.Column("source_external_id", sa.String(length=255), nullable=True)
    )
    op.add_column("opportunities", sa.Column("deadline", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "opportunities", sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "opportunities", sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "opportunities", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "opportunities", sa.Column("extraction_status", sa.String(length=32), nullable=True)
    )
    op.add_column("opportunities", sa.Column("content_hash", sa.String(length=64), nullable=True))
    op.add_column("opportunities", sa.Column("fingerprint", sa.String(length=64), nullable=True))
    op.create_unique_constraint("uq_opportunity_canonical_url", "opportunities", ["canonical_url"])
    op.create_unique_constraint(
        "uq_opportunity_source_external", "opportunities", ["source_id", "source_external_id"]
    )
    op.create_index("ix_opportunities_fingerprint", "opportunities", ["fingerprint"])
    op.create_table(
        "opportunity_discovery_runs",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column(
            "user_id",
            sa.String(length=128),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("query", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("employment_type", sa.String(length=32), nullable=True),
        sa.Column("experience_level", sa.String(length=64), nullable=True),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("requested_sources", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("total_results", sa.Integer(), nullable=False),
        sa.Column("accepted_results", sa.Integer(), nullable=False),
        sa.Column("rejected_results", sa.Integer(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("safe_error_message", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "total_results >= 0 AND accepted_results >= 0 AND rejected_results >= 0 AND total_results = accepted_results + rejected_results",
            name="ck_discovery_counts",
        ),
        sa.CheckConstraint(
            "status IN ('pending','running','completed','partially_completed','failed','cancelled')",
            name="ck_discovery_status",
        ),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_discovery_user_key"),
    )
    op.create_index(
        "ix_discovery_status_expires", "opportunity_discovery_runs", ["status", "expires_at"]
    )
    op.create_index(
        "ix_opportunity_discovery_runs_user_id", "opportunity_discovery_runs", ["user_id"]
    )
    op.create_table(
        "opportunity_source_observations",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column(
            "opportunity_id",
            sa.Uuid(),
            sa.ForeignKey("opportunities.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "source_id",
            sa.Uuid(),
            sa.ForeignKey("opportunity_sources.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "discovery_run_id",
            sa.Uuid(),
            sa.ForeignKey("opportunity_discovery_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_external_id", sa.String(length=255), nullable=True),
        sa.Column("original_url", sa.String(length=2048), nullable=True),
        sa.Column("canonical_url", sa.String(length=2048), nullable=True),
        sa.Column("provider_request_id", sa.String(length=128), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("validation_status", sa.String(length=32), nullable=False),
        sa.Column("extraction_error", sa.String(length=64), nullable=True),
        sa.CheckConstraint(
            "validation_status IN ('accepted','rejected')", name="ck_observation_validation"
        ),
        sa.UniqueConstraint(
            "discovery_run_id", "source_id", "content_hash", name="uq_observation_run_source_hash"
        ),
    )
    op.create_index(
        "ix_observation_external",
        "opportunity_source_observations",
        ["source_id", "source_external_id"],
    )
    op.create_index(
        "ix_opportunity_source_observations_discovery_run_id",
        "opportunity_source_observations",
        ["discovery_run_id"],
    )
    op.create_index(
        "ix_opportunity_source_observations_opportunity_id",
        "opportunity_source_observations",
        ["opportunity_id"],
    )
    op.create_table(
        "saved_opportunities",
        sa.Column(
            "user_id",
            sa.String(length=128),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column(
            "opportunity_id",
            sa.Uuid(),
            sa.ForeignKey("opportunities.id", ondelete="CASCADE"),
            nullable=False,
            primary_key=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "opportunity_identities",
        sa.Column("identity_key", sa.String(64), primary_key=True),
        sa.Column(
            "opportunity_id",
            sa.Uuid(),
            sa.ForeignKey("opportunities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_id", sa.Uuid(), sa.ForeignKey("opportunity_sources.id", ondelete="RESTRICT")
        ),
        sa.Column("source_external_id", sa.String(255)),
        sa.Column("canonical_url", sa.String(2048)),
    )
    op.create_index(
        "ix_opportunity_identities_opportunity_id", "opportunity_identities", ["opportunity_id"]
    )
    op.create_index(
        "ix_identity_source_external", "opportunity_identities", ["source_id", "source_external_id"]
    )


def downgrade() -> None:
    raise RuntimeError(
        "Forward-only migration: data removal requires a separately reviewed migration"
    )
