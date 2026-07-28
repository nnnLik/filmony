"""Add link_card_id to weekly_controversy_state.

Revision ID: e6f7a8b90123
Revises: d5e6f7a8b901
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'e6f7a8b90123'
down_revision: str | Sequence[str] | None = 'd5e6f7a8b901'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'weekly_controversy_state',
        sa.Column('link_card_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_weekly_controversy_state_link_card_id_user_card',
        'weekly_controversy_state',
        'user_card',
        ['link_card_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_weekly_controversy_state_link_card_id_user_card',
        'weekly_controversy_state',
        type_='foreignkey',
    )
    op.drop_column('weekly_controversy_state', 'link_card_id')
