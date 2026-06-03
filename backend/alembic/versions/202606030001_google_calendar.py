"""google calendar integration

Revision ID: 202606030001
Revises: 202606010001
Create Date: 2026-06-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "202606030001"
down_revision: Union[str, None] = "202606010001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def json_type():
    return postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def uuid_type():
    return postgresql.UUID(as_uuid=True).with_variant(sa.String(36), "sqlite")


def upgrade() -> None:
    op.create_table(
        "calendar_connections",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("user_id", uuid_type(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False, server_default="google"),
        sa.Column("google_account_email", sa.String(255)),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text()),
        sa.Column("token_expiry", sa.DateTime(timezone=True)),
        sa.Column("scopes", json_type(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "scheduled_events",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("coach_id", uuid_type(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("client_id", uuid_type(), sa.ForeignKey("clients.id")),
        sa.Column("meeting_id", uuid_type(), sa.ForeignKey("meetings.id")),
        sa.Column("google_event_id", sa.String(255)),
        sa.Column("calendar_id", sa.String(255), nullable=False, server_default="primary"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(100), nullable=False, server_default="Asia/Beirut"),
        sa.Column("location", sa.Text()),
        sa.Column("google_meet_link", sa.Text()),
        sa.Column("google_html_link", sa.Text()),
        sa.Column("attendees", json_type(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(50), nullable=False, server_default="scheduled"),
        sa.Column("talon_agent_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.add_column("meetings", sa.Column("scheduled_event_id", uuid_type(), sa.ForeignKey("scheduled_events.id")))
    op.add_column("meetings", sa.Column("google_event_id", sa.String(255)))
    op.add_column("meetings", sa.Column("google_meet_link", sa.Text()))
    op.add_column("meetings", sa.Column("scheduled_start_time", sa.DateTime(timezone=True)))
    op.add_column("meetings", sa.Column("scheduled_end_time", sa.DateTime(timezone=True)))
    op.add_column("meetings", sa.Column("timezone", sa.String(100)))


def downgrade() -> None:
    for column in [
        "timezone",
        "scheduled_end_time",
        "scheduled_start_time",
        "google_meet_link",
        "google_event_id",
        "scheduled_event_id",
    ]:
        op.drop_column("meetings", column)
    op.drop_table("scheduled_events")
    op.drop_table("calendar_connections")
