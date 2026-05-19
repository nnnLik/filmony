"""movie_card audio vibe fields

Revision ID: b5c6d7e8f901
Revises: m3n4o5p89012
Create Date: 2026-05-19

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'b5c6d7e8f901'
down_revision: str | Sequence[str] | None = 'm3n4o5p89012'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'movie_card',
        sa.Column('audio_url', sa.String(length=2048), nullable=True),
    )
    op.add_column(
        'movie_card',
        sa.Column(
            'audio_repeat_enabled',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        'movie_card',
        sa.Column(
            'audio_repeat_delay_ms',
            sa.Integer(),
            nullable=False,
            server_default='0',
        ),
    )


def downgrade() -> None:
    op.drop_column('movie_card', 'audio_repeat_delay_ms')
    op.drop_column('movie_card', 'audio_repeat_enabled')
    op.drop_column('movie_card', 'audio_url')
