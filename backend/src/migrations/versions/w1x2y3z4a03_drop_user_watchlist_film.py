"""Drop legacy user_watchlist_film after migration to watchlist_entry.

Revision ID: w1x2y3z4a03
Revises: w1x2y3z4a02
"""

from collections.abc import Sequence

from alembic import op

revision: str = 'w1x2y3z4a03'
down_revision: str | Sequence[str] | None = 'w1x2y3z4a02'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('DROP TABLE IF EXISTS user_watchlist_film CASCADE')


def downgrade() -> None:
    pass
