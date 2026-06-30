"""Add watchlist_entry.watch_with_user_ids JSONB for multi-invite.

Revision ID: w1x2y3z4a05
Revises: w1x2y3z4a04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'w1x2y3z4a05'
down_revision: str | Sequence[str] | None = 'w1x2y3z4a04'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'watchlist_entry',
        sa.Column(
            'watch_with_user_ids',
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
    )
    op.execute(
        """
        UPDATE watchlist_entry
        SET watch_with_user_ids = json_build_array(watch_with_user_id::text)
        WHERE watch_with_user_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_column('watchlist_entry', 'watch_with_user_ids')
