"""TinyFish Agent execution metadata and field evidence.

Revision ID: 0006_tinyfish_agent_evidence
Revises: 0005_opportunity_discovery
"""

import sqlalchemy as sa
from alembic import op

revision = "0006_tinyfish_agent_evidence"
down_revision = "0005_opportunity_discovery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "discovery_runs",
        sa.Column("refresh_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "tinyfish_executions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "discovery_run_id",
            sa.Uuid(),
            sa.ForeignKey("discovery_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_url", sa.String(2048), nullable=False),
        sa.Column("provider_run_id", sa.String(255)),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("steps", sa.Integer()),
        sa.Column("jobs_returned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("safe_error_code", sa.String(64)),
        sa.Column("result_json", sa.JSON()),
    )
    op.create_index(
        "ix_tinyfish_executions_discovery_run_id", "tinyfish_executions", ["discovery_run_id"]
    )
    op.create_index("ix_tinyfish_executions_source_url", "tinyfish_executions", ["source_url"])
    op.create_table(
        "opportunity_evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "opportunity_detail_id",
            sa.Uuid(),
            sa.ForeignKey("opportunity_details.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "execution_id",
            sa.Uuid(),
            sa.ForeignKey("tinyfish_executions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("field_name", sa.String(64), nullable=False),
        sa.Column("field_value", sa.Text(), nullable=False),
        sa.Column("evidence_url", sa.String(2048), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        sa.Column("confidence", sa.String(16), nullable=False),
        sa.Column(
            "observed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_opportunity_evidence_opportunity_detail_id",
        "opportunity_evidence",
        ["opportunity_detail_id"],
    )


def downgrade() -> None:
    op.drop_table("opportunity_evidence")
    op.drop_index("ix_tinyfish_executions_source_url", table_name="tinyfish_executions")
    op.drop_index("ix_tinyfish_executions_discovery_run_id", table_name="tinyfish_executions")
    op.drop_table("tinyfish_executions")
    op.drop_column("discovery_runs", "refresh_requested")
