"""merge heads

Revision ID: 1ee1c4bb5dd6
Revises: v8w9x0y1z234, w1x2y3z4a02
Create Date: 2026-06-30 15:49:27.460080

"""

from collections.abc import Sequence

revision: str = '1ee1c4bb5dd6'
down_revision: str | Sequence[str] | None = ('v8w9x0y1z234', 'w1x2y3z4a02')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
