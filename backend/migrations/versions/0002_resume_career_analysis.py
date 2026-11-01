"""Add resume parsing and career analysis persistence."""

import sqlalchemy as sa
from alembic import op

revision = "0002_resume_career_analysis"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resumes", sa.Column("parsed_data", sa.JSON()))
    op.add_column("resumes", sa.Column("parse_error", sa.Text()))
    op.add_column("agent_runs", sa.Column("model_version", sa.String(128)))
    op.add_column("agent_runs", sa.Column("prompt_version", sa.String(64)))
    op.add_column("agent_runs", sa.Column("error", sa.Text()))
    op.create_table(
        "career_analyses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(128),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("resume_id", sa.Uuid(), sa.ForeignKey("resumes.id", ondelete="SET NULL")),
        sa.Column("output", sa.JSON(), nullable=False),
        sa.Column("model_version", sa.String(128), nullable=False),
        sa.Column("prompt_version", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="succeeded"),
        sa.Column("error", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_career_analyses_user_id", "career_analyses", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_career_analyses_user_id", table_name="career_analyses")
    op.drop_table("career_analyses")
    op.drop_column("agent_runs", "error")
    op.drop_column("agent_runs", "prompt_version")
    op.drop_column("agent_runs", "model_version")
    op.drop_column("resumes", "parse_error")
    op.drop_column("resumes", "parsed_data")
