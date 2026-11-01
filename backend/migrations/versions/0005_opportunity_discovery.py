"""Milestone 4: Opportunity Discovery Foundation tables.

Creates:
- discovery_runs
- opportunity_details
- opportunity_source_observations
- saved_opportunities

Revision ID: 0005_opportunity_discovery
Depends on:  0004_career_analysis_idempotency
"""

import sqlalchemy as sa
from alembic import op

revision = "0005_opportunity_discovery"
down_revision = "0004_career_analysis_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # discovery_runs
    # ------------------------------------------------------------------
    op.create_table(
        "discovery_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(128),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column("query", sa.String(512), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("employment_type", sa.String(64), nullable=True),
        sa.Column("experience_level", sa.String(64), nullable=True),
        sa.Column("requested_sources", sa.JSON(), nullable=True),
        sa.Column("requested_skills", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("total_results", sa.Integer(), nullable=True),
        sa.Column("accepted_results", sa.Integer(), nullable=True),
        sa.Column("rejected_results", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("safe_error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_discovery_run_idempotency"),
    )
    op.create_index("ix_discovery_runs_user_id", "discovery_runs", ["user_id"])
    op.create_index("ix_discovery_runs_user_status", "discovery_runs", ["user_id", "status"])

    # ------------------------------------------------------------------
    # opportunity_details
    # ------------------------------------------------------------------
    op.create_table(
        "opportunity_details",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "opportunity_id",
            sa.Uuid(),
            sa.ForeignKey("opportunities.id", ondelete="SET NULL"),
            unique=True,
            nullable=True,
        ),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("company_name", sa.String(512), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(512), nullable=True),
        sa.Column("work_mode", sa.String(64), nullable=True),
        sa.Column("employment_type", sa.String(64), nullable=True),
        sa.Column("experience_requirement", sa.String(128), nullable=True),
        sa.Column("required_skills", sa.JSON(), nullable=True),
        sa.Column("preferred_skills", sa.JSON(), nullable=True),
        sa.Column("salary_min", sa.Numeric(14, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(14, 2), nullable=True),
        sa.Column("salary_currency", sa.String(8), nullable=True),
        sa.Column("stipend", sa.String(255), nullable=True),
        sa.Column("application_url", sa.String(2048), nullable=True),
        sa.Column("canonical_url", sa.String(2048), nullable=True),
        sa.Column("source_url", sa.String(2048), nullable=False),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("opportunity_sources.id"), nullable=True),
        sa.Column("source_external_id", sa.String(512), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "discovered_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="unknown"),
        sa.Column("extraction_status", sa.String(32), nullable=False, server_default="unextracted"),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("canonical_url", name="uq_opportunity_detail_canonical_url"),
    )
    op.create_index("ix_opportunity_details_content_hash", "opportunity_details", ["content_hash"])
    op.create_index("ix_opportunity_detail_company", "opportunity_details", ["company_name"])
    op.create_index(
        "ix_opportunity_detail_employment_type", "opportunity_details", ["employment_type"]
    )
    op.create_index("ix_opportunity_detail_status", "opportunity_details", ["status"])

    # ------------------------------------------------------------------
    # opportunity_source_observations
    # ------------------------------------------------------------------
    op.create_table(
        "opportunity_source_observations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "opportunity_detail_id",
            sa.Uuid(),
            sa.ForeignKey("opportunity_details.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "discovery_run_id",
            sa.Uuid(),
            sa.ForeignKey("discovery_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("opportunity_sources.id"), nullable=True),
        sa.Column("original_url", sa.String(2048), nullable=False),
        sa.Column("canonical_url", sa.String(2048), nullable=True),
        sa.Column("provider_request_id", sa.String(255), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column(
            "observed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("validation_status", sa.String(64), nullable=False, server_default="pending"),
        sa.Column("extraction_error", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_source_observations_opportunity_detail_id",
        "opportunity_source_observations",
        ["opportunity_detail_id"],
    )
    op.create_index(
        "ix_source_observations_discovery_run_id",
        "opportunity_source_observations",
        ["discovery_run_id"],
    )

    # ------------------------------------------------------------------
    # saved_opportunities
    # ------------------------------------------------------------------
    op.create_table(
        "saved_opportunities",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(128),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "opportunity_detail_id",
            sa.Uuid(),
            sa.ForeignKey("opportunity_details.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id",
            "opportunity_detail_id",
            name="uq_saved_opportunity_user_detail",
        ),
    )
    op.create_index("ix_saved_opportunities_user_id", "saved_opportunities", ["user_id"])


def downgrade() -> None:
    op.drop_table("saved_opportunities")
    op.drop_table("opportunity_source_observations")
    op.drop_table("opportunity_details")
    op.drop_table("discovery_runs")
