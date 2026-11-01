"""Track bounded agent retry attempts."""

import sqlalchemy as sa
from alembic import op

revision = "0003_agent_attempt_count"
down_revision = "0002_resume_career_analysis"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_runs",
        sa.Column("attempt_count", sa.Integer(), server_default="1", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("agent_runs", "attempt_count")
