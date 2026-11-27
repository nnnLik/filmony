"""Add unique reaction_type.shortcode (backfill from asset_key).

Revision ID: k1l2m3n4o567
Revises: j8k9l0m1n234
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from services.text.reaction_shortcodes import allocate_unique_shortcodes

revision: str = 'k1l2m3n4o567'
down_revision: str | Sequence[str] | None = 'j8k9l0m1n234'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'reaction_type',
        sa.Column('shortcode', sa.String(length=32), nullable=True),
    )

    bind = op.get_bind()
    rows = bind.execute(
        sa.text('SELECT id, asset_key, category_slug FROM reaction_type')
    ).fetchall()
    allocated = allocate_unique_shortcodes(
        [(int(row.id), str(row.asset_key), str(row.category_slug)) for row in rows]
    )
    update_stmt = sa.text('UPDATE reaction_type SET shortcode = :shortcode WHERE id = :id')
    for row_id, shortcode in allocated.items():
        bind.execute(update_stmt, {'shortcode': shortcode, 'id': row_id})

    op.alter_column(
        'reaction_type',
        'shortcode',
        existing_type=sa.String(length=32),
        nullable=False,
    )
    op.create_unique_constraint('uq_reaction_type_shortcode', 'reaction_type', ['shortcode'])


def downgrade() -> None:
    op.drop_constraint('uq_reaction_type_shortcode', 'reaction_type', type_='unique')
    op.drop_column('reaction_type', 'shortcode')
