"""user_card.watch_note max length 500 -> 1000

Revision ID: z1a2b3c4d567
Revises: y3z4a5b6c789
Create Date: 2026-07-06

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'z1a2b3c4d567'
down_revision: str | Sequence[str] | None = 'y3z4a5b6c789'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        'user_card',
        'watch_note',
        existing_type=sa.String(length=500),
        type_=sa.String(length=1000),
        existing_nullable=False,
        existing_server_default=sa.text("''"),
    )


def downgrade() -> None:
    op.alter_column(
        'user_card',
        'watch_note',
        existing_type=sa.String(length=1000),
        type_=sa.String(length=500),
        existing_nullable=False,
        existing_server_default=sa.text("''"),
    )
