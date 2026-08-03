"""user_card.watch_note unlimited Text

Revision ID: f1e2d3c4b567
Revises: e6f7a8b90123
Create Date: 2026-08-04

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'f1e2d3c4b567'
down_revision: str | Sequence[str] | None = 'e6f7a8b90123'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        'user_card',
        'watch_note',
        existing_type=sa.String(length=1000),
        type_=sa.Text(),
        existing_nullable=False,
        existing_server_default=sa.text("''"),
    )


def downgrade() -> None:
    op.alter_column(
        'user_card',
        'watch_note',
        existing_type=sa.Text(),
        type_=sa.String(length=1000),
        existing_nullable=False,
        existing_server_default=sa.text("''"),
    )
