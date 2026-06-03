"""session invite fields

Revision ID: 202605260002
Revises: 202605260001
Create Date: 2026-05-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202605260002"
down_revision: Union[str, None] = "202605260001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"))
    op.add_column("sessions", sa.Column("location", sa.String(length=500), nullable=True))
    op.add_column("sessions", sa.Column("invite_status", sa.String(length=50), nullable=False, server_default="not_sent"))
    op.add_column("sessions", sa.Column("invite_sent_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "invite_sent_at")
    op.drop_column("sessions", "invite_status")
    op.drop_column("sessions", "location")
    op.drop_column("sessions", "duration_minutes")
