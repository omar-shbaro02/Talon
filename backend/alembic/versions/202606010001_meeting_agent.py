"""meeting agent tables

Revision ID: 202606010001
Revises: 202605260002
Create Date: 2026-06-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "202606010001"
down_revision: Union[str, None] = "202605260002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def json_type():
    return postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def uuid_type():
    return postgresql.UUID(as_uuid=True).with_variant(sa.String(36), "sqlite")


def upgrade() -> None:
    op.add_column("meetings", sa.Column("meeting_url", sa.Text()))
    op.add_column("meetings", sa.Column("transcript_status", sa.String(50), nullable=False, server_default="pending"))
    op.add_column("meetings", sa.Column("recording_status", sa.String(50), nullable=False, server_default="pending"))
    op.add_column("meetings", sa.Column("transcript_full", sa.Text()))
    op.add_column("meetings", sa.Column("analysis_status", sa.String(50), nullable=False, server_default="pending"))
    op.add_column("meetings", sa.Column("leadership_patterns", json_type(), nullable=False, server_default="[]"))
    op.add_column("meetings", sa.Column("emotional_tone", sa.Text()))
    op.add_column("meetings", sa.Column("risks_or_blockers", json_type(), nullable=False, server_default="[]"))

    op.create_table(
        "meeting_bots",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("coach_id", uuid_type(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("client_id", uuid_type(), sa.ForeignKey("clients.id")),
        sa.Column("meeting_id", uuid_type(), sa.ForeignKey("meetings.id"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False, server_default="recall.ai"),
        sa.Column("external_bot_id", sa.String(255)),
        sa.Column("meeting_url", sa.Text(), nullable=False),
        sa.Column("bot_name", sa.String(100), nullable=False, server_default="TALON Assistant"),
        sa.Column("status", sa.String(50), nullable=False, server_default="created"),
        sa.Column("joined_at", sa.DateTime(timezone=True)),
        sa.Column("left_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "meeting_recordings",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("meeting_id", uuid_type(), sa.ForeignKey("meetings.id"), nullable=False),
        sa.Column("recording_url", sa.Text()),
        sa.Column("audio_url", sa.Text()),
        sa.Column("video_url", sa.Text()),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("provider", sa.String(50), nullable=False, server_default="recall.ai"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "meeting_transcript_segments",
        sa.Column("id", uuid_type(), primary_key=True),
        sa.Column("meeting_id", uuid_type(), sa.ForeignKey("meetings.id"), nullable=False),
        sa.Column("speaker_name", sa.String(255)),
        sa.Column("speaker_email", sa.String(255)),
        sa.Column("start_time_seconds", sa.Numeric(10, 3)),
        sa.Column("end_time_seconds", sa.Numeric(10, 3)),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("meeting_transcript_segments")
    op.drop_table("meeting_recordings")
    op.drop_table("meeting_bots")
    for column in [
        "risks_or_blockers",
        "emotional_tone",
        "leadership_patterns",
        "analysis_status",
        "transcript_full",
        "recording_status",
        "transcript_status",
        "meeting_url",
    ]:
        op.drop_column("meetings", column)
