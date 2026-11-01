"""Prevent duplicate successful career-analysis executions."""

from alembic import op

revision = "0004_career_analysis_idempotency"
down_revision = "0003_agent_attempt_count"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_career_analysis_execution",
        "career_analyses",
        ["user_id", "resume_id", "model_version", "prompt_version"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_career_analysis_execution", "career_analyses", type_="unique")
