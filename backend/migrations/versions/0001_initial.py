"""Create initial SkillSphere V3 tables.

Revision ID: 0001_initial
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(128), primary_key=True),
        sa.Column("email", sa.String(320), unique=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "career_profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(128),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("summary", sa.Text()),
        sa.Column("career_stage", sa.String(64)),
        sa.Column("completion_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "resumes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.String(128), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("storage_key", sa.String(512), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="uploaded"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_resumes_user_id", "resumes", ["user_id"])
    op.create_table(
        "skills",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(128), unique=True, nullable=False),
    )
    op.create_table(
        "user_skills",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.String(128), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "skill_id", sa.Uuid(), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("proficiency", sa.String(32)),
        sa.Column("source", sa.String(128)),
        sa.UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),
    )
    op.create_index("ix_user_skills_user_id", "user_skills", ["user_id"])
    op.create_table(
        "career_preferences",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(128),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("target_roles", sa.Text()),
        sa.Column("locations", sa.Text()),
        sa.Column("work_modes", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "opportunity_sources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(128), unique=True, nullable=False),
        sa.Column("base_url", sa.String(512)),
    )
    op.create_table(
        "opportunities",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("opportunity_sources.id")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("company_name", sa.String(255)),
        sa.Column("source_url", sa.String(2048), unique=True, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="unverified"),
        sa.Column(
            "discovered_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_opportunities_status_verified_at", "opportunities", ["status", "verified_at"]
    )
    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.String(128), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("opportunity_id", sa.Uuid(), sa.ForeignKey("opportunities.id")),
        sa.Column("status", sa.String(32), nullable=False, server_default="interested"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_applications_user_id", "applications", ["user_id"])
    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.String(128), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("title", sa.String(255)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.Uuid(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.String(128), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("workflow", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_agent_runs_user_id", "agent_runs", ["user_id"])
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.String(128), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("resource_type", sa.String(128), nullable=False),
        sa.Column("resource_id", sa.String(128)),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_audit_events_user_id", "audit_events", ["user_id"])
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.String(128), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    for table in (
        "notifications",
        "audit_events",
        "agent_runs",
        "messages",
        "conversations",
        "applications",
        "opportunities",
        "opportunity_sources",
        "career_preferences",
        "user_skills",
        "skills",
        "resumes",
        "career_profiles",
        "users",
    ):
        op.drop_table(table)
