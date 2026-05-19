"""drop movie_card audio repeat columns

Revision ID: c9d0e1f2a345
Revises: b5c6d7e8f901
Create Date: 2026-05-19

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = 'c9d0e1f2a345'
down_revision = 'b5c6d7e8f901'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('movie_card', 'audio_repeat_delay_ms')
    op.drop_column('movie_card', 'audio_repeat_enabled')


def downgrade() -> None:
    op.add_column(
        'movie_card',
        sa.Column(
            'audio_repeat_enabled',
            sa.Boolean(),
            server_default=sa.text('false'),
            nullable=False,
        ),
    )
    op.add_column(
        'movie_card',
        sa.Column(
            'audio_repeat_delay_ms',
            sa.Integer(),
            server_default=sa.text('0'),
            nullable=False,
        ),
    )
