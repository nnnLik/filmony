"""Movie card: optional text note about the viewing (watch_note).

Revision ID: g8h9i0j1k234
Revises: b2c3d4e5f6a7
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'g8h9i0j1k234'
down_revision: str | Sequence[str] | None = 'b2c3d4e5f6a7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'movie_card',
        sa.Column(
            'watch_note',
            sa.String(length=500),
            nullable=False,
            server_default=sa.text("''"),
        ),
    )
    op.alter_column('movie_card', 'watch_note', server_default=None)


def downgrade() -> None:
    op.drop_column('movie_card', 'watch_note')
