"""movie_card_comment.image_url

Revision ID: n0o1p2q3r678
Revises: m5n6o7p8q901
Create Date: 2026-05-13

"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = 'n0o1p2q3r678'
down_revision: str | Sequence[str] | None = 'm5n6o7p8q901'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'movie_card_comment',
        sa.Column('image_url', sa.String(length=2048), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('movie_card_comment', 'image_url')
