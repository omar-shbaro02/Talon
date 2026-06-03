"""initial schema

Revision ID: 202605260001
Revises:
Create Date: 2026-05-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "202605260001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def json_type():
    return postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def uuid_type():
    return postgresql.UUID(as_uuid=True).with_variant(sa.String(36), "sqlite")


def timestamps():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="coach"),
        *timestamps(),
    )
    op.create_table(
        "clients",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("coach_id", uuid_type(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(50)),
        sa.Column("company", sa.String(255)),
        sa.Column("job_title", sa.String(255)),
        sa.Column("industry", sa.String(255)),
        sa.Column("goals", sa.Text),
        sa.Column("challenges", sa.Text),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        *timestamps(),
    )
    op.create_table(
        "sessions",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("client_id", uuid_type(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("coach_id", uuid_type(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("session_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text),
        sa.Column("status", sa.String(50), nullable=False, server_default="scheduled"),
        *timestamps(),
    )
    op.create_table(
        "meetings",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("client_id", uuid_type(), sa.ForeignKey("clients.id")),
        sa.Column("coach_id", uuid_type(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("transcript", sa.Text, nullable=False),
        sa.Column("summary", sa.Text),
        sa.Column("key_topics", json_type(), nullable=False, server_default="[]"),
        sa.Column("decisions", json_type(), nullable=False, server_default="[]"),
        sa.Column("commitments", json_type(), nullable=False, server_default="[]"),
        sa.Column("coaching_observations", json_type(), nullable=False, server_default="[]"),
        sa.Column("recommended_next_steps", json_type(), nullable=False, server_default="[]"),
        sa.Column("follow_up_email", sa.Text),
        *timestamps(),
    )
    op.create_table(
        "action_items",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("client_id", uuid_type(), sa.ForeignKey("clients.id")),
        sa.Column("meeting_id", uuid_type(), sa.ForeignKey("meetings.id")),
        sa.Column("assigned_to", sa.String(255)),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("due_date", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(50), nullable=False, server_default="open"),
        sa.Column("priority", sa.String(50), nullable=False, server_default="medium"),
        *timestamps(),
    )
    op.create_table(
        "knowledge_documents",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("coach_id", uuid_type(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(255)),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("tags", json_type(), nullable=False, server_default="[]"),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="manual"),
        *timestamps(),
    )
    op.create_table(
        "content_generations",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("coach_id", uuid_type(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("client_id", uuid_type(), sa.ForeignKey("clients.id")),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("topic", sa.String(255), nullable=False),
        sa.Column("tone", sa.String(100), nullable=False),
        sa.Column("input_context", sa.Text),
        sa.Column("generated_output", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "ai_interactions",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("coach_id", uuid_type(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("client_id", uuid_type(), sa.ForeignKey("clients.id")),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("task_type", sa.String(100), nullable=False),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("response", json_type(), nullable=False),
        sa.Column("model", sa.String(100)),
        sa.Column("tokens_used", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "automation_workflows",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("coach_id", uuid_type(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("trigger_type", sa.String(100), nullable=False),
        sa.Column("workflow_steps", json_type(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.false()),
        *timestamps(),
    )
    op.create_table(
        "client_insights",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("client_id", uuid_type(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("coach_id", uuid_type(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("insight_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("confidence_score", sa.Float),
        sa.Column("source", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "assessments",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("client_id", uuid_type(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("coach_id", uuid_type(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assessment_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("results", json_type(), nullable=False, server_default="{}"),
        sa.Column("score", sa.Float),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "files",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("coach_id", uuid_type(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("client_id", uuid_type(), sa.ForeignKey("clients.id")),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(100)),
        sa.Column("file_url", sa.String(500)),
        sa.Column("extracted_text", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "files",
        "assessments",
        "client_insights",
        "automation_workflows",
        "ai_interactions",
        "content_generations",
        "knowledge_documents",
        "action_items",
        "meetings",
        "sessions",
        "clients",
        "users",
    ]:
        op.drop_table(table)

