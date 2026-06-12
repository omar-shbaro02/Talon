"""add meeting provider fields

Revision ID: 202606040001
Revises: 202606030001
Create Date: 2026-06-04 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "202606040001"
down_revision: str | None = "202606030001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("scheduled_events", sa.Column("meeting_provider", sa.String(length=50), nullable=False, server_default="google_meet"))
    op.add_column("scheduled_events", sa.Column("meeting_link", sa.Text(), nullable=True))
    op.add_column("scheduled_events", sa.Column("invite_status", sa.String(length=50), nullable=False, server_default="not_sent"))
    op.add_column("scheduled_events", sa.Column("invite_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("meetings", sa.Column("meeting_provider", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("meetings", "meeting_provider")
    op.drop_column("scheduled_events", "invite_sent_at")
    op.drop_column("scheduled_events", "invite_status")
    op.drop_column("scheduled_events", "meeting_link")
    op.drop_column("scheduled_events", "meeting_provider")
